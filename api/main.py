import os
import traceback
import json
import logging # 导入 logging
import numpy as np # 导入 numpy
import pandas as pd # 导入 pandas
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
# import pandas as pd # pandas is already imported below
from typing import Dict, Any, Optional
from decimal import Decimal, InvalidOperation # Import Decimal and InvalidOperation

# 导入新的 Pydantic 模型
from .models import (
    StockValuationRequest, StockValuationResponse, ValuationResultsContainer,
    DcfForecastDetails, OtherAnalysis, DividendAnalysis, GrowthAnalysis
)

# 导入数据获取器和所有新的计算器模块
from data_fetcher import AshareDataFetcher # 假设在根目录
from data_processor import DataProcessor
from financial_forecaster import FinancialForecaster
from wacc_calculator import WaccCalculator
from terminal_value_calculator import TerminalValueCalculator
from present_value_calculator import PresentValueCalculator
from equity_bridge_calculator import EquityBridgeCalculator
# FcfCalculator 和 NwcCalculator 被 FinancialForecaster 和 DataProcessor 内部使用或逻辑已整合

# 导入 LLM 调用相关的库 (示例，需要安装和配置)
# import google.generativeai as genai
# import openai
# from anthropic import Anthropic
import requests # For DeepSeek or other HTTP APIs

# --- Logging Configuration ---
LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

logging.basicConfig(
    level=logging.INFO, # 设置日志级别
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, "api.log"), encoding='utf-8'), # 输出到文件
        logging.StreamHandler() # 同时输出到控制台
    ]
)
logger = logging.getLogger(__name__)

# --- FastAPI App Initialization ---
app = FastAPI(
    title="Stock Valuation API (Streamlit Backend)",
    description="API for fetching stock data, calculating DCF valuation, and providing LLM analysis.",
    version="0.2.0",
)

# --- CORS Configuration ---
origins = [
    "http://localhost",
    "http://localhost:8501", # 默认 Streamlit 端口
    "*" # 谨慎使用
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- LLM Configuration ---
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini").lower()
PROMPT_TEMPLATE_PATH = os.getenv("PROMPT_TEMPLATE_PATH", "config/llm_prompt_template.md")
LLM_API_KEYS = {
    "gemini": os.getenv("GEMINI_API_KEY"),
    "openai": os.getenv("OPENAI_API_KEY"),
    "anthropic": os.getenv("ANTHROPIC_API_KEY"),
    "deepseek": os.getenv("DEEPSEEK_API_KEY"),
}

# --- Helper Functions ---
def load_prompt_template() -> str:
    """从文件加载 Prompt 模板"""
    try:
        with open(PROMPT_TEMPLATE_PATH, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        logger.error(f"Prompt template file not found at {PROMPT_TEMPLATE_PATH}")
        return "请分析以下数据：\n{data_json}" # Fallback template expects data_json key
    except Exception as e:
        logger.error(f"Error loading prompt template: {e}")
        return "请分析以下数据：\n{data_json}"

# Helper for JSON serialization of Decimal and other types
def decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        # Handle potential NaN/Inf from numpy floats
        if np.isnan(obj):
            return None # Or 'NaN' string, depending on desired JSON output
        elif np.isinf(obj):
            return None # Or 'Infinity'/'Infinity' string
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, pd.Timestamp) or isinstance(obj, np.datetime64): # Handle Timestamp/datetime64
        # Convert to ISO 8601 string format, or just date string if preferred
        # Check if it's NaT (Not a Time) first
        if pd.isna(obj):
             return None
        # Attempt conversion, handle potential errors
        try:
            # Ensure obj is compatible with isoformat() if it's numpy datetime64
            # Convert numpy datetime64 to pandas Timestamp for consistent formatting
            if isinstance(obj, np.datetime64):
                # Handle potential out-of-bounds errors for Timestamp conversion
                # Check numpy docs for appropriate range or use alternative string conversion
                try:
                    # Direct conversion might fail for certain units or values
                    # Safer approach might be needed depending on np.datetime64 specifics
                     ts = pd.Timestamp(obj)
                     return ts.isoformat()
                except ValueError:
                     # Fallback or log error if conversion fails
                     return str(obj) # Simple string representation as fallback
            elif isinstance(obj, pd.Timestamp):
                 return obj.isoformat()
            else: # Should not happen based on isinstance check, but for safety
                 return str(obj)
        except Exception:
             # Fallback if isoformat fails for any reason
             return str(obj)

    elif isinstance(obj, (np.bool_, bool)): # Handle numpy bool and Python bool explicitly
         return bool(obj)
    # Add handling for pd.NA if necessary
    elif pd.isna(obj): # General pandas NA check
        return None
    # Add handling for pd.Timedelta if needed
    # elif isinstance(obj, pd.Timedelta):
    #     return obj.total_seconds() # Example: convert to seconds

    # If no specific handler, raise TypeError with more info
    raise TypeError(f"Object of type {type(obj).__name__} with value '{str(obj)}' is not JSON serializable")


def format_llm_input_data(
    basic_info: Dict[str, Any],
    dcf_details: DcfForecastDetails,
    latest_metrics: Dict[str, Any],
    request_assumptions: StockValuationRequest, # 使用 StockValuationRequest 类型
    historical_ratios_from_dp: Dict[str, Any], # 从 DataProcessor 获取的历史比率
    # financial_forecaster_assumptions: Dict[str, Any] # 或者直接从 request_assumptions 获取
    other_analysis=None # 保持可选
) -> str:
    """将数据格式化为 JSON 字符串以供 Prompt 使用，包含关键假设。"""
    
    key_assumptions = {
        "forecast_years": request_assumptions.forecast_years,
        "wacc_parameters": {
            "target_debt_ratio_pct": request_assumptions.target_debt_ratio * 100 if request_assumptions.target_debt_ratio is not None else None,
            "cost_of_debt_pct": request_assumptions.cost_of_debt * 100 if request_assumptions.cost_of_debt is not None else None,
            "risk_free_rate_pct": request_assumptions.risk_free_rate * 100 if request_assumptions.risk_free_rate is not None else None,
            "beta": request_assumptions.beta,
            "market_risk_premium_pct": request_assumptions.market_risk_premium * 100 if request_assumptions.market_risk_premium is not None else None,
            "size_premium_pct": request_assumptions.size_premium * 100 if request_assumptions.size_premium is not None else None,
        },
        "effective_tax_rate_pct": request_assumptions.target_effective_tax_rate * 100 if request_assumptions.target_effective_tax_rate is not None else None,
        "terminal_value_method": request_assumptions.terminal_value_method,
        "exit_multiple": request_assumptions.exit_multiple if request_assumptions.terminal_value_method == 'exit_multiple' else None,
        "perpetual_growth_rate_pct": request_assumptions.perpetual_growth_rate * 100 if request_assumptions.terminal_value_method == 'perpetual_growth' and request_assumptions.perpetual_growth_rate is not None else None,
        "revenue_forecast_logic": "CAGR with decay",
        "revenue_initial_cagr_pct": historical_ratios_from_dp.get('revenue_cagr_3y'), # 已经是百分比
        "revenue_cagr_decay_rate_pct": request_assumptions.cagr_decay_rate * 100 if request_assumptions.cagr_decay_rate is not None else None,
        "prediction_details": {
            # General transition years
            "nwc_days_transition_years": request_assumptions.nwc_days_transition_years,
            "other_nwc_ratio_transition_years": request_assumptions.other_nwc_ratio_transition_years,
            "op_margin_transition_years": request_assumptions.op_margin_transition_years,
            "sga_rd_transition_years": request_assumptions.sga_rd_transition_years,
            "da_ratio_transition_years": request_assumptions.da_ratio_transition_years,
            "capex_ratio_transition_years": request_assumptions.capex_ratio_transition_years,
            # Specific metric modes and targets (修正属性名以匹配 StockValuationRequest)
            "op_margin_forecast_mode": request_assumptions.op_margin_forecast_mode,
            "target_operating_margin_pct": request_assumptions.target_operating_margin * 100 if request_assumptions.target_operating_margin is not None else None,
            "sga_rd_ratio_forecast_mode": request_assumptions.sga_rd_ratio_forecast_mode,
            "target_sga_rd_to_revenue_ratio_pct": request_assumptions.target_sga_rd_to_revenue_ratio * 100 if request_assumptions.target_sga_rd_to_revenue_ratio is not None else None,
            "da_ratio_forecast_mode": request_assumptions.da_ratio_forecast_mode,
            "target_da_to_revenue_ratio_pct": request_assumptions.target_da_to_revenue_ratio * 100 if request_assumptions.target_da_to_revenue_ratio is not None else None,
            "capex_ratio_forecast_mode": request_assumptions.capex_ratio_forecast_mode,
            "target_capex_to_revenue_ratio_pct": request_assumptions.target_capex_to_revenue_ratio * 100 if request_assumptions.target_capex_to_revenue_ratio is not None else None,
            "nwc_days_forecast_mode": request_assumptions.nwc_days_forecast_mode,
            "target_accounts_receivable_days": request_assumptions.target_accounts_receivable_days,
            "target_inventory_days": request_assumptions.target_inventory_days,
            "target_accounts_payable_days": request_assumptions.target_accounts_payable_days,
            "other_nwc_ratio_forecast_mode": request_assumptions.other_nwc_ratio_forecast_mode,
            "target_other_current_assets_to_revenue_ratio_pct": request_assumptions.target_other_current_assets_to_revenue_ratio * 100 if request_assumptions.target_other_current_assets_to_revenue_ratio is not None else None,
            "target_other_current_liabilities_to_revenue_ratio_pct": request_assumptions.target_other_current_liabilities_to_revenue_ratio * 100 if request_assumptions.target_other_current_liabilities_to_revenue_ratio is not None else None,
        }
    }
    
    # Filter out None values from key_assumptions for cleaner output
    def clean_dict(d):
        if not isinstance(d, dict):
            return d
        return {k: clean_dict(v) for k, v in d.items() if v is not None and not (isinstance(v, dict) and not clean_dict(v))}

    cleaned_key_assumptions = clean_dict(key_assumptions)

    dcf_results_dict = dcf_details.dict(exclude_none=True) if dcf_details else {}
    dcf_results_dict["key_assumptions"] = cleaned_key_assumptions

    data_dict = {
        "stock_info": basic_info or {},
        "dcf_results": dcf_results_dict,
        "reference_metrics": latest_metrics or {},
        # "other_analysis": other_analysis.dict(exclude_none=True) if other_analysis else {} # 可选添加
    }
    
    # 添加 latest_price 到 stock_info for prompt
    if latest_metrics and 'latest_price' in latest_metrics:
         data_dict["stock_info"]["latest_price"] = latest_metrics['latest_price']

    try:
        # 使用 ensure_ascii=False 保留中文字符, and add default handler for Decimal
        json_string = json.dumps(data_dict, indent=2, ensure_ascii=False, default=decimal_default)
        # logger.debug(f"Formatted LLM input data:\n{json_string}") # Debug log if needed
        return json_string
    except Exception as e:
        logger.error(f"Error formatting data for LLM prompt: {e}")
        return "{}" # 返回空 JSON 对象字符串

def call_llm_api(prompt: str) -> Optional[str]:
    """调用配置的 LLM API"""
    logger.info(f"--- Calling LLM ({LLM_PROVIDER}) ---")
    # logger.debug(f"Prompt:\n{prompt}\n") # Debug log for full prompt if needed

    api_key = LLM_API_KEYS.get(LLM_PROVIDER)
    if not api_key or api_key == "AIzaSy...pEU": # Also check for example key
        logger.error(f"API Key for {LLM_PROVIDER} not found or not configured correctly in .env file.")
        return f"错误：未找到或未正确配置 {LLM_PROVIDER} 的 API Key。"

    try:
        logger.info(f"Attempting to call {LLM_PROVIDER} API...")
        if LLM_PROVIDER == "gemini":
            import google.generativeai as genai # 移到函数内部或顶部
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-pro') # 或者选择更合适的模型
            # 增加对安全设置的配置，以避免潜在的内容阻塞
            generation_config = genai.types.GenerationConfig(
                # candidate_count=1, # 默认是1
                # stop_sequences=['x'],
                # max_output_tokens=2048, # 默认
                # temperature=0.7, # 默认
            )
            safety_settings = [ # 调整安全等级，例如全部设为 BLOCK_NONE (非常宽松，请谨慎) 或 BLOCK_ONLY_HIGH
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]
            print(f"调用 Gemini API (model: gemini-pro)...")
            response = model.generate_content(
                prompt,
                generation_config=generation_config,
                safety_settings=safety_settings
                )
            # 检查 response.prompt_feedback 是否有阻塞原因
            if response.prompt_feedback and response.prompt_feedback.block_reason:
                block_reason_message = f"Gemini API 请求被阻止，原因: {response.prompt_feedback.block_reason}"
                if response.prompt_feedback.block_reason_message:
                    block_reason_message += f" - {response.prompt_feedback.block_reason_message}"
                print(f"Warning: {block_reason_message}")
                # 尝试获取是否有部分文本返回
                if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
                    partial_text = "".join(part.text for part in response.candidates[0].content.parts if hasattr(part, 'text'))
                    if partial_text:
                        return f"{block_reason_message}\n部分返回内容:\n{partial_text}"
                return block_reason_message

            if not response.candidates or not response.candidates[0].content or not response.candidates[0].content.parts:
                 # 检查是否有完成原因指示问题
                 finish_reason_msg = ""
                 if response.candidates and response.candidates[0].finish_reason:
                     finish_reason_msg = f" (Finish Reason: {response.candidates[0].finish_reason.name})"
                 
                 # 检查是否有安全评分问题
                 safety_ratings_msg = ""
                 if response.candidates and response.candidates[0].safety_ratings:
                     problematic_ratings = [f"{rating.category.name}: {rating.probability.name}" for rating in response.candidates[0].safety_ratings if rating.probability.name not in ["NEGLIGIBLE", "LOW"]]
                     if problematic_ratings:
                         safety_ratings_msg = f" (Problematic Safety Ratings: {', '.join(problematic_ratings)})"

                 logger.warning(f"Gemini API did not return valid content. {finish_reason_msg}{safety_ratings_msg}")
                 return f"Gemini API 未返回有效内容。{finish_reason_msg}{safety_ratings_msg}"
            
            llm_result = "".join(part.text for part in response.candidates[0].content.parts if hasattr(part, 'text'))
            logger.info(f"Successfully received response from {LLM_PROVIDER}.")
            # logger.debug(f"LLM Result (truncated): {llm_result[:200]}...") # Debug log if needed
            # return llm_result
            # # print("模拟调用 Gemini API...")
            # # return f"Gemini 分析结果占位符。\n分析内容应基于提供的详细数据和 Prompt 指令生成..." # 占位符
        elif LLM_PROVIDER == "openai":
            # import openai
            # openai.api_key = api_key
            # client = openai.OpenAI(api_key=api_key)
            # response = client.chat.completions.create(
            #     model="gpt-3.5-turbo", # Or gpt-4
            #     messages=[{"role": "user", "content": prompt}]
            # )
            # return response.choices[0].message.content
            print("模拟调用 OpenAI API...")
            return f"OpenAI 分析结果占位符。\n分析内容应基于提供的详细数据和 Prompt 指令生成..." # 占位符
        elif LLM_PROVIDER == "anthropic":
            # from anthropic import Anthropic
            # client = Anthropic(api_key=api_key)
            # message = client.messages.create(
            #     model="claude-3-opus-20240229", # Or other models
            #     max_tokens=1024,
            #     messages=[{"role": "user", "content": prompt}]
            # )
            # return message.content[0].text
            print("模拟调用 Anthropic API...")
            return f"Anthropic 分析结果占位符。\n分析内容应基于提供的详细数据和 Prompt 指令生成..." # 占位符
        elif LLM_PROVIDER == "deepseek":
             # 实际调用 DeepSeek API
             # 注意：需要确认实际的 API 端点和模型名称
             url = "https://api.deepseek.com/chat/completions" # 假设的 DeepSeek API 端点
             headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
             # 根据 DeepSeek API 文档调整 payload 结构
             payload = {
                 "model": "deepseek-chat", # 确认模型名称
                 "messages": [{"role": "user", "content": prompt}],
                 # "max_tokens": 2048, # 可选参数
                 # "temperature": 0.7, # 可选参数
             } 
             logger.info(f"Calling DeepSeek API at {url} with model {payload['model']}...")
             response = requests.post(url, headers=headers, json=payload, timeout=180) # 增加超时
             response.raise_for_status() # 如果状态码不是 2xx，则抛出异常
             
             # 根据 DeepSeek API 文档调整响应解析方式
             response_data = response.json()
             if response_data and 'choices' in response_data and response_data['choices'] and 'message' in response_data['choices'][0] and 'content' in response_data['choices'][0]['message']:
                 llm_result = response_data['choices'][0]['message']['content']
                 logger.info(f"Successfully received response from {LLM_PROVIDER}.")
                 return llm_result
             else:
                  logger.warning(f"DeepSeek API response format unexpected: {response_data}")
                  return "DeepSeek API 返回格式错误或无有效内容。"
             # print("模拟调用 DeepSeek API...")
             # return f"DeepSeek 分析结果占位符。\n分析内容应基于提供的详细数据和 Prompt 指令生成..." # 占位符
        else:
            return f"错误：不支持的 LLM 提供商 '{LLM_PROVIDER}'。"

    except ImportError as ie:
         logger.error(f"Missing library for {LLM_PROVIDER}. Please install it. {ie}")
         return f"错误：缺少用于 {LLM_PROVIDER} 的库，请安装。"
    except Exception as e:
        logger.error(f"Error calling LLM API ({LLM_PROVIDER}): {e}\n{traceback.format_exc()}")
        return f"调用 LLM API 时出错: {str(e)}"

# --- API Endpoints ---
@app.get("/")
async def read_root():
    return {"message": "Welcome to the Stock Valuation API (Streamlit Backend)"}

@app.post("/api/v1/valuation", response_model=StockValuationResponse, summary="计算股票估值 (新版)")
async def calculate_valuation_endpoint_v2(request: StockValuationRequest):
    """
    (新版) 计算指定股票的 DCF 估值，并结合 LLM 进行分析。
    """
    logger.info(f"Received valuation request for: {request.ts_code}")
    all_data = {}
    processed_data_container = None
    financial_forecaster = None
    wacc_calculator = None
    
    try:
        # 1. 数据获取
        logger.info("Step 1: Fetching data...")
        fetcher = AshareDataFetcher(ts_code=request.ts_code)
        basic_info = fetcher.get_stock_info() # 获取基本信息 (dict)
        latest_price = fetcher.get_latest_price() # 获取最新价格 (float)
        latest_pe_pb = fetcher.get_latest_pe_pb(request.valuation_date) # 获取最新 PE/PB (dict)
        total_shares = fetcher.get_latest_total_shares(request.valuation_date) # 获取最新总股本 (float or None)
        logger.info(f"  Fetched basic info: {basic_info.get('name')}, Latest Price: {latest_price}, Latest PE/PB: {latest_pe_pb}, Total Shares: {total_shares}")
        # 获取足够历史数据用于计算 CAGR 和中位数
        hist_years_needed = max(request.forecast_years + 3, 5) # 至少需要几年数据
        raw_financial_data = fetcher.get_raw_financial_data(years=hist_years_needed)
        # 将获取的数据放入 all_data 字典，供 DataProcessor 使用
        all_data = {
            'stock_basic': basic_info, # 仍然传递给 DP 用于获取 name/industry
            'balance_sheet': raw_financial_data.get('balance_sheet'),
            'income_statement': raw_financial_data.get('income_statement'),
            'cash_flow': raw_financial_data.get('cash_flow'),
            # 不再传递 valuation_metrics DataFrame
        }

        # 检查关键数据
        logger.info("  Checking fetched data...")
        if not basic_info: raise HTTPException(status_code=404, detail=f"无法获取股票基本信息: {request.ts_code}")
        if latest_price is None or latest_price <= 0: raise HTTPException(status_code=404, detail=f"无法获取有效的最新价格: {request.ts_code}")
        # PE/PB 可以为空，DataProcessor 会处理
        if any(df is None or df.empty for df in [all_data['balance_sheet'], all_data['income_statement'], all_data['cash_flow']]): raise HTTPException(status_code=404, detail=f"缺少必要的历史财务报表数据: {request.ts_code}")
        logger.info("  Data check passed.")

        # 2. 数据处理
        logger.info("Step 2: Processing data...")
        processed_data_container = DataProcessor(all_data, latest_pe_pb=latest_pe_pb) 
        basic_info = processed_data_container.get_basic_info()
        latest_metrics = processed_data_container.get_latest_metrics()
        historical_ratios = processed_data_container.get_historical_ratios()
        latest_balance_sheet = processed_data_container.get_latest_balance_sheet()
        data_warnings = processed_data_container.get_warnings()
        latest_metrics['latest_price'] = latest_price # 将最新价格加入指标字典
        logger.info(f"  Data processing complete. Warnings: {len(data_warnings)}")

        # 3. 财务预测
        logger.info("Step 3: Forecasting financials...")
        forecast_assumptions = request.dict(exclude={'ts_code', 'market', 'valuation_date'})
        financial_forecaster = FinancialForecaster(
            last_actual_revenue=processed_data_container.processed_data['income_statement']['revenue'].iloc[-1],
            historical_ratios=historical_ratios,
            forecast_assumptions=forecast_assumptions
        )
        final_forecast_df = financial_forecaster.get_full_forecast()
        if final_forecast_df.empty or 'ufcf' not in final_forecast_df.columns: raise HTTPException(status_code=500, detail="财务预测失败或未能生成 UFCF。")
        logger.info("  Financial forecast complete.")

        # 4. WACC 计算
        logger.info("Step 4: Calculating WACC...")
        wacc_params_input = {k: getattr(request, k) for k in ['target_debt_ratio', 'cost_of_debt', 'risk_free_rate', 'beta', 'market_risk_premium', 'size_premium']}
        wacc_params_input['tax_rate'] = request.target_effective_tax_rate # 使用预测税率
        wacc_params_input['beta'] = wacc_params_input.get('beta') if wacc_params_input.get('beta') is not None else latest_metrics.get('beta')
        wacc_params_filtered = {k: v for k, v in wacc_params_input.items() if v is not None}

        # 估算市值用于 WACC 计算 (如果 PE 和最新净利有效)
        market_cap_est = None
        # 使用从 DataProcessor 获取的 latest_metrics
        if latest_metrics.get('pe') and 'income_statement' in processed_data_container.processed_data and not processed_data_container.processed_data['income_statement'].empty:
             # 确保 n_income 列存在
             if 'n_income' in processed_data_container.processed_data['income_statement'].columns:
                 last_income = processed_data_container.processed_data['income_statement']['n_income'].iloc[-1]
                 # 确保 last_income 和 pe 都有效再计算
                 if pd.notna(last_income) and last_income > 0 and pd.notna(latest_metrics.get('pe')):
                      # 将两个操作数都显式转换为 float
                      market_cap_est = float(latest_metrics['pe']) * float(last_income) / 100000000 # 转换为亿元
             else:
                  print("Warning: 'n_income' column not found in income_statement for market cap estimation.")

        wacc_calculator = WaccCalculator(financials_dict=processed_data_container.processed_data, market_cap=market_cap_est)
        wacc, cost_of_equity = wacc_calculator.get_wacc_and_ke(wacc_params_filtered)
        if wacc is None: raise HTTPException(status_code=500, detail=f"WACC 计算失败。Ke: {cost_of_equity}")
        logger.info(f"  WACC calculated: {wacc:.4f}, Ke: {cost_of_equity:.4f}")

        # 5. 终值计算 (添加校验和默认值)
        logger.info("Step 5: Calculating Terminal Value...")
        tv_calculator = TerminalValueCalculator(risk_free_rate=wacc_params_filtered.get('risk_free_rate', 0.03))
        
        exit_multiple_to_use = request.exit_multiple
        perpetual_growth_rate_to_use = request.perpetual_growth_rate

        if request.terminal_value_method == 'exit_multiple':
            if exit_multiple_to_use is None or exit_multiple_to_use <= 0:
                default_exit_multiple_str = os.getenv('DEFAULT_EXIT_MULTIPLE', '8.0')
                try:
                    default_exit_multiple = float(default_exit_multiple_str)
                    if default_exit_multiple > 0:
                        exit_multiple_to_use = default_exit_multiple
                        data_warnings.append(f"未提供有效的退出乘数，已使用默认值: {exit_multiple_to_use}")
                        print(f"Warning: Exit multiple not provided or invalid, using default: {exit_multiple_to_use}")
                    else:
                         raise HTTPException(status_code=422, detail="退出乘数法需要有效的正退出乘数，且无法获取有效的默认值。")
                except (ValueError, TypeError):
                     raise HTTPException(status_code=422, detail="退出乘数法需要有效的正退出乘数，且默认值配置无效。")
            perpetual_growth_rate_to_use = None # 确保 PGP 不被错误使用

        elif request.terminal_value_method == 'perpetual_growth':
            if perpetual_growth_rate_to_use is None:
                 default_pg_rate_str = os.getenv('DEFAULT_PERPETUAL_GROWTH_RATE', '0.025')
                 try:
                     default_pg_rate = float(default_pg_rate_str)
                     # 永续增长率可以为0，但通常需要小于 WACC 且大于等于0（或某个负数下限）
                     # 这里的校验主要在 TerminalValueCalculator 中进行
                     perpetual_growth_rate_to_use = default_pg_rate
                     data_warnings.append(f"未提供永续增长率，已使用默认值: {perpetual_growth_rate_to_use:.3f}")
                     print(f"Warning: Perpetual growth rate not provided, using default: {perpetual_growth_rate_to_use}")
                 except (ValueError, TypeError):
                      raise HTTPException(status_code=422, detail="永续增长率法需要有效的永续增长率，且默认值配置无效。")
            exit_multiple_to_use = None # 确保退出乘数不被错误使用
        else:
             raise HTTPException(status_code=422, detail=f"无效的终值计算方法: {request.terminal_value_method}")

        terminal_value, tv_error = tv_calculator.calculate_terminal_value(
            last_forecast_year_data=final_forecast_df.iloc[-1], wacc=wacc,
            method=request.terminal_value_method, 
            exit_multiple=exit_multiple_to_use,
            perpetual_growth_rate=perpetual_growth_rate_to_use
        )
        if tv_error: raise HTTPException(status_code=500, detail=f"终值计算失败: {tv_error}")
        logger.info(f"  Terminal Value calculated: {terminal_value:.2f} using method {request.terminal_value_method}")

        # 6. 现值计算
        logger.info("Step 6: Calculating Present Values...")
        pv_calculator = PresentValueCalculator()
        pv_forecast_ufcf, pv_terminal_value, pv_error = pv_calculator.calculate_present_values(
            forecast_df=final_forecast_df, terminal_value=terminal_value, wacc=wacc
        )
        if pv_error: raise HTTPException(status_code=500, detail=f"现值计算失败: {pv_error}")
        logger.info(f"  Present Values calculated. PV(UFCF): {pv_forecast_ufcf:.2f}, PV(TV): {pv_terminal_value:.2f}")

        # 7. 企业价值与股权价值计算
        logger.info("Step 7: Calculating Equity Value...")
        enterprise_value = pv_forecast_ufcf + pv_terminal_value
        equity_bridge_calculator = EquityBridgeCalculator()
        # 将从 fetcher 获取的 total_shares (单位：亿股) 转换为实际股数
        total_shares_actual = total_shares * 100000000 if total_shares is not None and total_shares > 0 else None
        net_debt, equity_value, value_per_share, eb_error = equity_bridge_calculator.calculate_equity_value(
            enterprise_value=enterprise_value, latest_balance_sheet=latest_balance_sheet,
            total_shares=total_shares_actual # 传递转换单位后的总股本
        )
        if eb_error: data_warnings.append(f"股权价值桥梁计算警告: {eb_error}")
        # 在记录日志前检查 None 值
        value_per_share_str = f"{value_per_share:.2f}" if value_per_share is not None else "N/A"
        equity_value_str = f"{equity_value:.2f}" if equity_value is not None else "N/A"
        logger.info(f"  Equity Value calculated: {equity_value_str}, Value/Share: {value_per_share_str}")


        # 8. 构建 DCF 结果
        logger.info("Step 8: Building DCF results object...")
        dcf_details = DcfForecastDetails(
            enterprise_value=enterprise_value, equity_value=equity_value, value_per_share=value_per_share,
            net_debt=net_debt, pv_forecast_ufcf=pv_forecast_ufcf, pv_terminal_value=pv_terminal_value,
            terminal_value=terminal_value, wacc_used=wacc, cost_of_equity_used=cost_of_equity,
            terminal_value_method_used=request.terminal_value_method,
            exit_multiple_used=request.exit_multiple if request.terminal_value_method == 'exit_multiple' else None,
            perpetual_growth_rate_used=request.perpetual_growth_rate if request.terminal_value_method == 'perpetual_growth' else None,
            forecast_period_years=request.forecast_years
        )

        # 9. 构建 LLM 输入并调用
        logger.info("Step 9: Preparing LLM input and calling API...")
        prompt_template = load_prompt_template()
        # 传递给 format_llm_input_data 的数据需要包含所有模板中使用的键
        # 确保 latest_metrics 包含 PE/PB (现在由 DataProcessor 处理)
        llm_input_json_str = format_llm_input_data(
            basic_info=basic_info,
            dcf_details=dcf_details,
            latest_metrics=latest_metrics, # 包含 PE/PB 和 latest_price
            request_assumptions=request, # 传递完整的 request 对象
            historical_ratios_from_dp=historical_ratios # 从 DataProcessor 获取的历史比率
        )
        prompt = prompt_template.format(data_json=llm_input_json_str) # 使用 data_json 键
        
        # Call LLM API with specific error handling
        llm_summary = None
        try:
            llm_summary = call_llm_api(prompt)
            logger.info(f"  LLM call complete. Summary length: {len(llm_summary) if llm_summary else 0}")
        except Exception as llm_exc:
            logger.error(f"Error during LLM call: {llm_exc}")
            llm_summary = f"Error in LLM analysis: {str(llm_exc)}"
            # Optionally add a warning if needed
            # data_warnings.append(f"LLM 分析失败: {str(llm_exc)}")

        # 10. 构建最终响应
        logger.info("Step 10: Building final response...")
        results_container = ValuationResultsContainer(
            latest_price=latest_price,
            current_pe=latest_metrics.get('pe'),
            current_pb=latest_metrics.get('pb'),
            dcf_forecast_details=dcf_details,
            # other_analysis=... # 暂时禁用
            llm_analysis_summary=llm_summary,
            data_warnings=data_warnings if data_warnings else None,
            detailed_forecast_table=final_forecast_df.to_dict(orient='records') if final_forecast_df is not None and not final_forecast_df.empty else None
        )
        logger.info("Valuation calculation completed successfully.")
        return StockValuationResponse(
            stock_info=basic_info,
            valuation_results=results_container
        )

    except HTTPException as http_exc:
        logger.error(f"HTTP Exception during valuation for {request.ts_code}: {http_exc.detail}")
        raise http_exc
    except Exception as e:
        logger.error(f"Unexpected error during valuation for {request.ts_code}: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8124)
