import os
import traceback
import json
import logging # 导入 logging
import numpy as np # 导入 numpy
import pandas as pd # 导入 pandas
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
# import pandas as pd # pandas is already imported below
from typing import Dict, Any, Optional, Tuple, List # Import Tuple and List
from decimal import Decimal, InvalidOperation # Import Decimal and InvalidOperation

# 导入 Pydantic 模型
# 使用绝对导入
from api.models import (
    StockValuationRequest, StockValuationResponse, ValuationResultsContainer, StockBasicInfoModel,
    DcfForecastDetails, OtherAnalysis, DividendAnalysis, GrowthAnalysis
)
# 导入敏感性分析模型
# 使用绝对导入
from api.sensitivity_models import SensitivityAnalysisRequest, SensitivityAnalysisResult, SensitivityAxisInput, MetricType # 修正导入名称, 添加 MetricType

# 导入数据获取器和所有新的计算器模块
# 这些在根目录，保持不变
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

# --- Backend Axis Generation Helper ---
def generate_axis_values_backend(center: float, step: float, points: int) -> List[float]:
    """
    Generates a list of axis values based on center, step, and points.
    Ensures points is an odd number >= 1 (typically >=3 for meaningful analysis).
    """
    if not isinstance(points, int) or points < 1:
        logger.warning(f"Invalid points value {points}, defaulting to 3.")
        points = 3
    elif points % 2 == 0:
        logger.warning(f"Points value {points} is even, incrementing to {points + 1}.")
        points += 1
    
    if not (isinstance(center, (float, int, Decimal)) and isinstance(step, (float, int, Decimal))):
        logger.error(f"Invalid center ({center}) or step ({step}) for axis generation.")
        # Depending on strictness, could raise error or return default list
        return [float(center)] if isinstance(center, (float, int, Decimal)) else [0.0]


    center = float(center)
    step = float(step)
    
    offset = (points - 1) // 2
    return [center + step * (i - offset) for i in range(points)]

# --- Core Valuation Logic Helper ---

def _run_single_valuation(
    processed_data_container: DataProcessor,
    request_dict: Dict[str, Any], # Use dict representation of request
    wacc_calculator: WaccCalculator,
    total_shares_actual: Optional[float],
    override_wacc: Optional[float] = None,
    override_exit_multiple: Optional[float] = None,
    override_perpetual_growth_rate: Optional[float] = None
) -> Tuple[Optional[DcfForecastDetails], Optional[pd.DataFrame], List[str]]: # Return type already includes DataFrame
    """
    执行单次估值计算的核心逻辑。
    接收处理后的数据、请求参数字典、WACC计算器、总股本，以及可选的覆盖参数。
    返回 DCF 详情、预测 DataFrame 和警告列表。
    """
    local_warnings = []
    final_forecast_df = None
    dcf_details = None

    try:
        # 3. 财务预测 (使用 request_dict 中的假设)
        logger.debug("  Running single valuation: Step 3 - Forecasting financials...")
        # 从 request_dict 提取预测假设，排除非假设字段
        forecast_assumptions = {k: v for k, v in request_dict.items() if k not in ['ts_code', 'market', 'valuation_date', 'sensitivity_analysis']}
        
        # 确保传递给 FinancialForecaster 的是有效的 last_actual_revenue
        last_actual_revenue = None
        if 'income_statement' in processed_data_container.processed_data and \
           not processed_data_container.processed_data['income_statement'].empty and \
           'revenue' in processed_data_container.processed_data['income_statement'].columns:
            last_actual_revenue = processed_data_container.processed_data['income_statement']['revenue'].iloc[-1]
        
        if last_actual_revenue is None or pd.isna(last_actual_revenue):
             raise ValueError("无法获取有效的上一年度实际收入用于财务预测。")

        financial_forecaster = FinancialForecaster(
            last_actual_revenue=last_actual_revenue,
            historical_ratios=processed_data_container.get_historical_ratios(),
            forecast_assumptions=forecast_assumptions
        )
        final_forecast_df = financial_forecaster.get_full_forecast()
        if final_forecast_df is None or final_forecast_df.empty or 'ufcf' not in final_forecast_df.columns:
            raise ValueError("财务预测失败或未能生成 UFCF。")
        logger.debug("  Single valuation: Financial forecast complete.")

        # 4. WACC 计算 (使用 request_dict 中的 WACC 参数或 override_wacc)
        logger.debug("  Running single valuation: Step 4 - Calculating WACC...")
        wacc = None
        cost_of_equity = None
        if override_wacc is not None:
            wacc = override_wacc
            # 如果直接覆盖 WACC，Ke 可能无法精确得知，除非也覆盖或单独计算
            # 为了简化，当覆盖 WACC 时，Ke 设为 None 或基础 Ke
            # 暂时设为 None
            cost_of_equity = None
            logger.debug(f"  Using overridden WACC: {wacc:.4f}")
        else:
            wacc_params_input = {k: request_dict.get(k) for k in ['target_debt_ratio', 'cost_of_debt', 'risk_free_rate', 'beta', 'market_risk_premium', 'size_premium']}
            wacc_params_input['tax_rate'] = request_dict.get('target_effective_tax_rate')
            wacc_params_input['beta'] = wacc_params_input.get('beta') if wacc_params_input.get('beta') is not None else processed_data_container.get_latest_metrics().get('beta')
            wacc_params_filtered = {k: v for k, v in wacc_params_input.items() if v is not None}
            current_wacc_weight_mode = request_dict.get('wacc_weight_mode', "target")
            
            # WaccCalculator 实例已在外部创建并传入
            wacc, cost_of_equity = wacc_calculator.get_wacc_and_ke(
                params=wacc_params_filtered,
                wacc_weight_mode=current_wacc_weight_mode
            )
            if wacc is None:
                raise ValueError(f"WACC 计算失败。Ke: {cost_of_equity}")
            logger.debug(f"  WACC calculated: {wacc:.4f} (mode: {current_wacc_weight_mode}), Ke: {cost_of_equity:.4f}")

        # 5. 终值计算 (使用 request_dict 中的 TV 参数或 overrides)
        logger.debug("  Running single valuation: Step 5 - Calculating Terminal Value...")
        # 使用基础 Rf 或从 params 获取
        base_rf = request_dict.get('risk_free_rate') or wacc_calculator.default_risk_free_rate
        tv_calculator = TerminalValueCalculator(risk_free_rate=float(base_rf)) # Ensure float

        tv_method = request_dict.get('terminal_value_method', 'exit_multiple')
        exit_multiple_to_use = override_exit_multiple if override_exit_multiple is not None else request_dict.get('exit_multiple')
        perpetual_growth_rate_to_use = override_perpetual_growth_rate if override_perpetual_growth_rate is not None else request_dict.get('perpetual_growth_rate')

        # 校验和默认值处理 (简化版，假设 Pydantic 已处理部分)
        if tv_method == 'exit_multiple' and (exit_multiple_to_use is None or exit_multiple_to_use <= 0):
            exit_multiple_to_use = float(os.getenv('DEFAULT_EXIT_MULTIPLE', '8.0')) # Use default if invalid
            local_warnings.append(f"敏感性分析中退出乘数无效或未提供，使用默认值: {exit_multiple_to_use}")
        elif tv_method == 'perpetual_growth' and perpetual_growth_rate_to_use is None:
             perpetual_growth_rate_to_use = float(os.getenv('DEFAULT_PERPETUAL_GROWTH_RATE', '0.025')) # Use default if invalid
             local_warnings.append(f"敏感性分析中永续增长率无效或未提供，使用默认值: {perpetual_growth_rate_to_use:.3f}")

        terminal_value, tv_error = tv_calculator.calculate_terminal_value(
            last_forecast_year_data=final_forecast_df.iloc[-1], wacc=wacc,
            method=tv_method,
            exit_multiple=exit_multiple_to_use if tv_method == 'exit_multiple' else None,
            perpetual_growth_rate=perpetual_growth_rate_to_use if tv_method == 'perpetual_growth' else None
        )
        if tv_error: raise ValueError(f"终值计算失败: {tv_error}")
        logger.debug(f"  Terminal Value calculated: {terminal_value:.2f} using method {tv_method}")

        # 6. 现值计算
        logger.debug("  Running single valuation: Step 6 - Calculating Present Values...")
        pv_calculator = PresentValueCalculator()
        pv_forecast_ufcf, pv_terminal_value, pv_error = pv_calculator.calculate_present_values(
            forecast_df=final_forecast_df, terminal_value=terminal_value, wacc=wacc
        )
        if pv_error: raise ValueError(f"现值计算失败: {pv_error}")
        logger.debug(f"  Present Values calculated. PV(UFCF): {pv_forecast_ufcf:.2f}, PV(TV): {pv_terminal_value:.2f}")

        # 7. 企业价值与股权价值计算
        logger.debug("  Running single valuation: Step 7 - Calculating Equity Value...")
        enterprise_value = pv_forecast_ufcf + pv_terminal_value
        equity_bridge_calculator = EquityBridgeCalculator()
        net_debt, equity_value, value_per_share, eb_error = equity_bridge_calculator.calculate_equity_value(
            enterprise_value=enterprise_value,
            latest_balance_sheet=processed_data_container.get_latest_balance_sheet(),
            total_shares=total_shares_actual
        )
        if eb_error: local_warnings.append(f"股权价值桥梁计算警告: {eb_error}")
        # Prepare strings for logging, handling None
        equity_value_str = f"{equity_value:.2f}" if equity_value is not None else "N/A"
        value_per_share_str = f"{value_per_share:.2f}" if value_per_share is not None else "N/A"
        logger.debug(f"  Equity Value calculated: {equity_value_str}, Value/Share: {value_per_share_str}")

        # 8. 构建 DCF 结果对象
        logger.debug("  Running single valuation: Step 8 - Building DCF results object...")
        
        # 计算 DCF 隐含稀释 PE (在 _run_single_valuation 外部，因为它依赖于 base_latest_metrics)
        # 这个逻辑应该在 calculate_valuation_endpoint_v2 中，当 base_dcf_details 和 base_latest_metrics 可用时
        # 因此，dcf_implied_diluted_pe 将在构建最终的 base_dcf_details 时添加

        dcf_details = DcfForecastDetails(
            enterprise_value=enterprise_value, equity_value=equity_value, value_per_share=value_per_share,
            net_debt=net_debt, pv_forecast_ufcf=pv_forecast_ufcf, pv_terminal_value=pv_terminal_value,
            terminal_value=terminal_value, wacc_used=wacc, cost_of_equity_used=cost_of_equity,
            terminal_value_method_used=tv_method,
            exit_multiple_used=exit_multiple_to_use if tv_method == 'exit_multiple' else None,
            perpetual_growth_rate_used=perpetual_growth_rate_to_use if tv_method == 'perpetual_growth' else None,
            forecast_period_years=request_dict.get('forecast_years', 5) # Get from dict
            # dcf_implied_diluted_pe 将在主函数中计算并添加到基础 DcfForecastDetails
        )
        logger.debug("  Single valuation run completed successfully.")
        return dcf_details, final_forecast_df, local_warnings

    except Exception as e:
        logger.error(f"Error during single valuation run: {e}\n{traceback.format_exc()}")
        local_warnings.append(f"单次估值计算失败: {str(e)}")
        return None, None, local_warnings


def format_llm_input_data(
    basic_info: Dict[str, Any], # Changed to Dict
    dcf_details: Optional[DcfForecastDetails], # Can be None if base calc fails
    latest_metrics: Dict[str, Any],
    request_assumptions_dict: Dict[str, Any], # Use dict representation
    historical_ratios_from_dp: Dict[str, Any],
    other_analysis=None
) -> str:
    """将数据格式化为 JSON 字符串以供 Prompt 使用，包含关键假设。"""
    
    # Use request_assumptions_dict instead of request_assumptions object
    key_assumptions = {
        "forecast_years": request_assumptions_dict.get('forecast_years'),
        "wacc_parameters": {
            "wacc_weight_mode": request_assumptions_dict.get('wacc_weight_mode'), # Add mode
            "target_debt_ratio_pct": request_assumptions_dict.get('target_debt_ratio') * 100 if request_assumptions_dict.get('target_debt_ratio') is not None else None,
            "cost_of_debt_pct": request_assumptions_dict.get('cost_of_debt') * 100 if request_assumptions_dict.get('cost_of_debt') is not None else None,
            "risk_free_rate_pct": request_assumptions_dict.get('risk_free_rate') * 100 if request_assumptions_dict.get('risk_free_rate') is not None else None,
            "beta": request_assumptions_dict.get('beta'),
            "market_risk_premium_pct": request_assumptions_dict.get('market_risk_premium') * 100 if request_assumptions_dict.get('market_risk_premium') is not None else None,
            "size_premium_pct": request_assumptions_dict.get('size_premium') * 100 if request_assumptions_dict.get('size_premium') is not None else None,
        },
        "effective_tax_rate_pct": request_assumptions_dict.get('target_effective_tax_rate') * 100 if request_assumptions_dict.get('target_effective_tax_rate') is not None else None,
        "terminal_value_method": request_assumptions_dict.get('terminal_value_method'),
        "exit_multiple": request_assumptions_dict.get('exit_multiple') if request_assumptions_dict.get('terminal_value_method') == 'exit_multiple' else None,
        "perpetual_growth_rate_pct": request_assumptions_dict.get('perpetual_growth_rate') * 100 if request_assumptions_dict.get('terminal_value_method') == 'perpetual_growth' and request_assumptions_dict.get('perpetual_growth_rate') is not None else None,
        "revenue_forecast_logic": "CAGR with decay",
        "revenue_initial_cagr_pct": historical_ratios_from_dp.get('revenue_cagr_3y'), # 已经是百分比
        "revenue_cagr_decay_rate_pct": request_assumptions_dict.get('cagr_decay_rate') * 100 if request_assumptions_dict.get('cagr_decay_rate') is not None else None,
        "prediction_details": {
            # General transition years
            "nwc_days_transition_years": request_assumptions_dict.get('nwc_days_transition_years'),
            "other_nwc_ratio_transition_years": request_assumptions_dict.get('other_nwc_ratio_transition_years'),
            "op_margin_transition_years": request_assumptions_dict.get('op_margin_transition_years'),
            "sga_rd_transition_years": request_assumptions_dict.get('sga_rd_transition_years'),
            "da_ratio_transition_years": request_assumptions_dict.get('da_ratio_transition_years'),
            "capex_ratio_transition_years": request_assumptions_dict.get('capex_ratio_transition_years'),
            # Specific metric modes and targets
            "op_margin_forecast_mode": request_assumptions_dict.get('op_margin_forecast_mode'),
            "target_operating_margin_pct": request_assumptions_dict.get('target_operating_margin') * 100 if request_assumptions_dict.get('target_operating_margin') is not None else None,
            "sga_rd_ratio_forecast_mode": request_assumptions_dict.get('sga_rd_ratio_forecast_mode'),
            "target_sga_rd_to_revenue_ratio_pct": request_assumptions_dict.get('target_sga_rd_to_revenue_ratio') * 100 if request_assumptions_dict.get('target_sga_rd_to_revenue_ratio') is not None else None,
            "da_ratio_forecast_mode": request_assumptions_dict.get('da_ratio_forecast_mode'),
            "target_da_to_revenue_ratio_pct": request_assumptions_dict.get('target_da_to_revenue_ratio') * 100 if request_assumptions_dict.get('target_da_to_revenue_ratio') is not None else None,
            "capex_ratio_forecast_mode": request_assumptions_dict.get('capex_ratio_forecast_mode'),
            "target_capex_to_revenue_ratio_pct": request_assumptions_dict.get('target_capex_to_revenue_ratio') * 100 if request_assumptions_dict.get('target_capex_to_revenue_ratio') is not None else None,
            "nwc_days_forecast_mode": request_assumptions_dict.get('nwc_days_forecast_mode'),
            "target_accounts_receivable_days": request_assumptions_dict.get('target_accounts_receivable_days'),
            "target_inventory_days": request_assumptions_dict.get('target_inventory_days'),
            "target_accounts_payable_days": request_assumptions_dict.get('target_accounts_payable_days'),
            "other_nwc_ratio_forecast_mode": request_assumptions_dict.get('other_nwc_ratio_forecast_mode'),
            "target_other_current_assets_to_revenue_ratio_pct": request_assumptions_dict.get('target_other_current_assets_to_revenue_ratio') * 100 if request_assumptions_dict.get('target_other_current_assets_to_revenue_ratio') is not None else None,
            "target_other_current_liabilities_to_revenue_ratio_pct": request_assumptions_dict.get('target_other_current_liabilities_to_revenue_ratio') * 100 if request_assumptions_dict.get('target_other_current_liabilities_to_revenue_ratio') is not None else None,
        }
    }
    
    # Filter out None values from key_assumptions for cleaner output
    def clean_dict(d):
        if not isinstance(d, dict):
            return d
        return {k: clean_dict(v) for k, v in d.items() if v is not None and not (isinstance(v, dict) and not clean_dict(v))}

    cleaned_key_assumptions = clean_dict(key_assumptions)

    dcf_results_dict = dcf_details.model_dump(exclude_none=True) if dcf_details else {} # Changed .dict() to .model_dump()
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
    支持可选的敏感性分析。
    """
    logger.info(f"Received valuation request for: {request.ts_code}")
    all_data = {}
    processed_data_container = None
    wacc_calculator = None
    base_results_container = None # Store base results
    sensitivity_result_obj = None # Store sensitivity results

    try:
        # --- Step 1 & 2: Data Fetching and Processing (Common for all scenarios) ---
        logger.info("Step 1: Fetching data...")
        fetcher = AshareDataFetcher(ts_code=request.ts_code)
        base_stock_info_dict = fetcher.get_stock_info() # 获取基本信息 (dict)
        latest_price = fetcher.get_latest_price() # 获取最新价格 (float)
        latest_pe_pb = fetcher.get_latest_pe_pb(request.valuation_date) # 获取最新 PE/PB (dict)
        total_shares = fetcher.get_latest_total_shares(request.valuation_date) # 获取最新总股本 (float or None)
        total_shares_actual = total_shares * 100000000 if total_shares is not None and total_shares > 0 else None
        logger.info(f"  Fetched base info: {base_stock_info_dict.get('name')}, Latest Price: {latest_price}, Latest PE/PB: {latest_pe_pb}, Total Shares: {total_shares}")
        hist_years_needed = max(request.forecast_years + 3, 5)
        raw_financial_data = fetcher.get_raw_financial_data(years=hist_years_needed)
        all_data = {
            'stock_basic': base_stock_info_dict,
            'balance_sheet': raw_financial_data.get('balance_sheet'),
            'income_statement': raw_financial_data.get('income_statement'),
            'cash_flow': raw_financial_data.get('cash_flow'),
        }
        logger.info("  Checking fetched data...")
        if not base_stock_info_dict: raise HTTPException(status_code=404, detail=f"无法获取股票基本信息: {request.ts_code}")
        if latest_price is None or latest_price <= 0: raise HTTPException(status_code=404, detail=f"无法获取有效的最新价格: {request.ts_code}")
        if any(df is None or df.empty for df in [all_data['balance_sheet'], all_data['income_statement'], all_data['cash_flow']]): raise HTTPException(status_code=404, detail=f"缺少必要的历史财务报表数据: {request.ts_code}")
        logger.info("  Data check passed.")

        logger.info("Step 2: Processing data...")
        processed_data_container = DataProcessor(all_data, latest_pe_pb=latest_pe_pb)
        # Get processed data needed for valuation runs
        base_basic_info = processed_data_container.get_basic_info() # Use this for final response
        base_latest_metrics = processed_data_container.get_latest_metrics()
        # Explicitly call get_latest_actual_ebitda to ensure it's calculated and stored in latest_metrics
        _ = processed_data_container.get_latest_actual_ebitda() # The result is stored in self.latest_metrics
        base_latest_metrics = processed_data_container.get_latest_metrics() # Re-fetch to include latest_actual_ebitda
        
        base_historical_ratios = processed_data_container.get_historical_ratios()
        base_data_warnings = processed_data_container.get_warnings() # Initial warnings
        base_latest_metrics['latest_price'] = latest_price
        logger.info(f"  Data processing complete. Initial Warnings: {len(base_data_warnings)}")
        logger.info(f"  Base latest metrics including actual EBITDA: {base_latest_metrics}")


        # --- Initialize WACC Calculator (Common) ---
        market_cap_est = None
        if base_latest_metrics.get('pe') and 'income_statement' in processed_data_container.processed_data and not processed_data_container.processed_data['income_statement'].empty:
             if 'n_income' in processed_data_container.processed_data['income_statement'].columns:
                 last_income = processed_data_container.processed_data['income_statement']['n_income'].iloc[-1]
                 if pd.notna(last_income) and last_income > 0 and pd.notna(base_latest_metrics.get('pe')):
                      market_cap_est = float(base_latest_metrics['pe']) * float(last_income) / 100000000
             else:
                  print("Warning: 'n_income' column not found in income_statement for market cap estimation.")
        wacc_calculator = WaccCalculator(financials_dict=processed_data_container.processed_data, market_cap=market_cap_est)

        # --- Run Base Case Valuation ---
        logger.info("Running base case valuation...")
        base_request_dict = request.model_dump() # Get base assumptions, updated from .dict()
        base_dcf_details, base_forecast_df, base_run_warnings = _run_single_valuation(
            processed_data_container=processed_data_container,
            request_dict=base_request_dict,
            wacc_calculator=wacc_calculator,
            total_shares_actual=total_shares_actual
            # No overrides for base case
        )
        all_warnings = base_data_warnings + base_run_warnings
        if base_dcf_details is None:
            # If base case fails, we cannot proceed with sensitivity or LLM
            raise HTTPException(status_code=500, detail=f"基础估值计算失败: {all_warnings[-1] if all_warnings else '未知错误'}")
        logger.info("Base case valuation successful.")

        # --- Sensitivity Analysis (if requested) ---
        if request.sensitivity_analysis:
            logger.info("Starting sensitivity analysis...")
            sa_request = request.sensitivity_analysis
            row_param = sa_request.row_axis.parameter_name
            col_param = sa_request.column_axis.parameter_name
            row_values = sa_request.row_axis.values
            col_values = sa_request.column_axis.values
            # output_metric is no longer in the request, we calculate all supported metrics
            # output_metric = sa_request.output_metric

            if row_param == col_param:
                raise HTTPException(status_code=422, detail="敏感性分析的行轴和列轴不能使用相同的参数。")

            # Validate supported parameters (extend this list as needed)
            supported_params = ["wacc", "exit_multiple", "perpetual_growth_rate"]
            if row_param not in supported_params or col_param not in supported_params:
                 raise HTTPException(status_code=422, detail=f"敏感性分析仅支持以下参数: {', '.join(supported_params)}")

            sensitivity_warnings = [] # Initialize warnings for sensitivity analysis part

            # --- WACC-specific axis regeneration ---
            actual_row_values = row_values # Default to request values
            actual_col_values = col_values # Default to request values
            
            # Regenerate axis values if step and points are provided
            def regenerate_axis_if_needed(axis_input: SensitivityAxisInput, base_details: Optional[DcfForecastDetails], param_name: str, is_row_axis: bool, base_req_dict: Dict[str, Any]) -> List[float]:
                current_values = axis_input.values
                should_regenerate = False
                center_val = None

                # For WACC, always try to regenerate if step/points are given, using base_wacc as center
                if param_name == MetricType.WACC.value:
                    if axis_input.step is not None and axis_input.points is not None:
                        center_val = base_details.wacc_used if base_details else None
                        if center_val is None: # Fallback to request input for WACC if base_details.wacc_used is None
                            center_val = base_req_dict.get('wacc') # Assuming 'wacc' might be a direct param or calculated
                            if center_val is None: # Try to get from wacc_calculator if not directly in request
                                # This part is tricky as wacc_calculator is outside this direct scope
                                # For now, rely on base_details.wacc_used or a clear request param
                                pass 
                        
                        if center_val is not None:
                            should_regenerate = True
                        else:
                            logger.warning(f"Cannot regenerate WACC axis for {'row' if is_row_axis else 'column'} due to missing base WACC and no fallback in request. Using original values if provided, else empty.")
                            sensitivity_warnings.append(f"WACC轴无法重新生成（缺少基础WACC且请求中无回退值），将使用请求中提供的原始值（如果存在）。")
                
                # For other params, regenerate only if values list is empty AND step/points are given
                elif not current_values and axis_input.step is not None and axis_input.points is not None:
                    if param_name == MetricType.TERMINAL_GROWTH_RATE.value:
                        center_val = base_details.perpetual_growth_rate_used if base_details else None
                        if center_val is None: # Fallback to request input
                            center_val = base_req_dict.get('perpetual_growth_rate')
                    elif param_name == MetricType.TERMINAL_EBITDA_MULTIPLE.value: # "exit_multiple"
                        center_val = base_details.exit_multiple_used if base_details else None
                        if center_val is None: # Fallback to request input
                            center_val = base_req_dict.get('exit_multiple')
                        if center_val is None: # Further fallback to a hardcoded default if still None
                            center_val = 8.0 # Default exit multiple
                            logger.info(f"Using hardcoded default center value {center_val} for {param_name} axis for {'row' if is_row_axis else 'column'}.")
                            sensitivity_warnings.append(f"{param_name}轴缺少基准值和请求值，使用默认中心值 {center_val}。")
                    
                    if center_val is not None:
                        try:
                            # Ensure center_val is float for generate_axis_values_backend
                            center_val = float(center_val)
                            should_regenerate = True
                        except (ValueError, TypeError):
                            logger.warning(f"Cannot convert center_val '{center_val}' to float for {param_name} axis for {'row' if is_row_axis else 'column'}. Using original (empty) values.")
                            sensitivity_warnings.append(f"{param_name}轴的中心值 '{center_val}' 无法转换为浮点数，将使用空的原始值列表。")
                            should_regenerate = False # Prevent regeneration if conversion fails
                    else:
                        # This case should ideally not be reached if we have a hardcoded default for exit_multiple
                        logger.warning(f"Cannot regenerate {param_name} axis for {'row' if is_row_axis else 'column'} due to missing base value and no fallback in request (even after default). Using original (empty) values.")
                        sensitivity_warnings.append(f"{param_name}轴无法重新生成（所有回退机制均失败），将使用空的原始值列表。")
                
                if should_regenerate and center_val is not None: # center_val already converted to float or regeneration is skipped
                    logger.info(f"Regenerating {'row' if is_row_axis else 'column'} axis for {param_name} around center value: {center_val:.4f}, Step: {axis_input.step}, Points: {axis_input.points}")
                    return generate_axis_values_backend(
                        center=float(center_val),
                        step=float(axis_input.step),
                        points=int(axis_input.points)
                    )
                
                # If not regenerated, return the original values from the request
                # If original values were empty and regeneration didn't happen (e.g. missing center_val for non-WACC), it will return empty.
                return current_values

            actual_row_values = regenerate_axis_if_needed(sa_request.row_axis, base_dcf_details, row_param, True, base_request_dict)
            actual_col_values = regenerate_axis_if_needed(sa_request.column_axis, base_dcf_details, col_param, False, base_request_dict)

            # Initialize result tables for all supported metrics using actual axis dimensions
            from api.sensitivity_models import SUPPORTED_SENSITIVITY_OUTPUT_METRICS # Import the Literal type
            output_metrics_to_calculate = list(SUPPORTED_SENSITIVITY_OUTPUT_METRICS.__args__)
            result_tables: Dict[str, List[List[Optional[float]]]] = {
                metric: [[None for _ in actual_col_values] for _ in actual_row_values]
                for metric in output_metrics_to_calculate
            }
            # sensitivity_warnings already initialized

            for i, row_val in enumerate(actual_row_values): # Use actual_row_values
                for j, col_val in enumerate(actual_col_values): # Use actual_col_values
                    logger.debug(f"  Running sensitivity case: {row_param}={row_val}, {col_param}={col_val}")
                    temp_request_dict = base_request_dict.copy()
                    override_wacc = None
                    override_exit_multiple = None
                    override_perpetual_growth_rate = None

                    # Apply overrides based on axis parameters
                    if row_param == "wacc": override_wacc = float(row_val)
                    elif row_param == "exit_multiple": override_exit_multiple = float(row_val)
                    elif row_param == "perpetual_growth_rate": override_perpetual_growth_rate = float(row_val)

                    if col_param == "wacc": override_wacc = float(col_val)
                    elif col_param == "exit_multiple": override_exit_multiple = float(col_val)
                    elif col_param == "perpetual_growth_rate": override_perpetual_growth_rate = float(col_val)
                    
                    # Need to handle terminal value method logic based on overrides
                    if override_exit_multiple is not None:
                        temp_request_dict['terminal_value_method'] = 'exit_multiple'
                        temp_request_dict['perpetual_growth_rate'] = None # Ensure consistency
                    elif override_perpetual_growth_rate is not None:
                        temp_request_dict['terminal_value_method'] = 'perpetual_growth'
                        temp_request_dict['exit_multiple'] = None # Ensure consistency

                    # Run valuation for this specific combination
                    dcf_details_sens, forecast_df_sens, run_warnings_sens = _run_single_valuation(
                        processed_data_container=processed_data_container,
                        request_dict=temp_request_dict, # Pass modified assumptions
                        wacc_calculator=wacc_calculator,
                        total_shares_actual=total_shares_actual,
                        override_wacc=override_wacc,
                        override_exit_multiple=override_exit_multiple,
                        override_perpetual_growth_rate=override_perpetual_growth_rate
                    )
                    sensitivity_warnings.extend(run_warnings_sens)
                    
                    # Calculate and store all supported output metrics for this combination
                    if dcf_details_sens:
                        # Value per Share
                        result_tables["value_per_share"][i][j] = dcf_details_sens.value_per_share
                        # Enterprise Value
                        result_tables["enterprise_value"][i][j] = dcf_details_sens.enterprise_value
                        # Equity Value
                        result_tables["equity_value"][i][j] = dcf_details_sens.equity_value
                        # TV/EV Ratio (using PV of Terminal Value)
                        if dcf_details_sens.enterprise_value and dcf_details_sens.enterprise_value != 0:
                            result_tables["tv_ev_ratio"][i][j] = (dcf_details_sens.pv_terminal_value or 0) / dcf_details_sens.enterprise_value
                        else:
                            result_tables["tv_ev_ratio"][i][j] = None
                        
                        # DCF Implied PE
                        result_tables["dcf_implied_pe"][i][j] = dcf_details_sens.dcf_implied_diluted_pe
                        logger.debug(f"DEBUG api/main: Populating dcf_implied_pe table at [{i}][{j}] with value: {dcf_details_sens.dcf_implied_diluted_pe} (Type: {type(dcf_details_sens.dcf_implied_diluted_pe)})")

                        # EV/EBITDA (using base year's actual EBITDA)
                        base_actual_ebitda = base_latest_metrics.get('latest_actual_ebitda')
                        if base_actual_ebitda is not None and isinstance(base_actual_ebitda, Decimal) and base_actual_ebitda > Decimal('0'):
                            if dcf_details_sens.enterprise_value is not None:
                                try:
                                    result_tables["ev_ebitda"][i][j] = float(Decimal(str(dcf_details_sens.enterprise_value)) / base_actual_ebitda)
                                except (InvalidOperation, TypeError, ZeroDivisionError) as e_calc:
                                    logger.warning(f"Error calculating EV/EBITDA for sensitivity: EV={dcf_details_sens.enterprise_value}, BaseEBITDA={base_actual_ebitda}. Error: {e_calc}")
                                    result_tables["ev_ebitda"][i][j] = None
                            else:
                                result_tables["ev_ebitda"][i][j] = None
                        else:
                            result_tables["ev_ebitda"][i][j] = None
                            if base_actual_ebitda is None:
                                sensitivity_warnings.append("无法获取基准年实际EBITDA，EV/EBITDA敏感性分析结果可能不准确或为空。")
                            elif not (isinstance(base_actual_ebitda, Decimal) and base_actual_ebitda > Decimal('0')):
                                 sensitivity_warnings.append(f"基准年实际EBITDA无效 ({base_actual_ebitda})，EV/EBITDA敏感性分析结果可能不准确或为空。")
                                 
                    else:
                        # If dcf_details_sens is None, all metrics for this combo are None (already initialized)
                        logger.warning(f"  Sensitivity case failed for {row_param}={row_val}, {col_param}={col_val}")

            sensitivity_result_obj = SensitivityAnalysisResult(
                row_parameter=row_param,
                column_parameter=col_param,
                row_values=actual_row_values, # Return the actual values used
                column_values=actual_col_values, # Return the actual values used
                result_tables=result_tables # Pass the dictionary of tables
            )
            all_warnings.extend(sensitivity_warnings) # Add warnings from sensitivity runs
            logger.info("Sensitivity analysis complete.")

        # --- LLM Analysis (Based on Base Case) ---
        logger.info("Step 9: Preparing LLM input and calling API (based on base case)...")
        llm_summary = None
        if base_dcf_details: # Only run if base case was successful
            prompt_template = load_prompt_template()
            llm_input_json_str = format_llm_input_data(
                basic_info=base_basic_info, # Use base info
                dcf_details=base_dcf_details, # Use base DCF details
                latest_metrics=base_latest_metrics,
                request_assumptions_dict=base_request_dict, # Use base assumptions dict
                historical_ratios_from_dp=base_historical_ratios
            )
            prompt = prompt_template.format(data_json=llm_input_json_str)
            try:
                llm_summary = call_llm_api(prompt)
                logger.info(f"  LLM call complete. Summary length: {len(llm_summary) if llm_summary else 0}")
            except Exception as llm_exc:
                logger.error(f"Error during LLM call: {llm_exc}")
                llm_summary = f"Error in LLM analysis: {str(llm_exc)}"
                all_warnings.append(f"LLM 分析失败: {str(llm_exc)}")
        else:
             logger.warning("Skipping LLM analysis because base valuation failed.")
             llm_summary = "基础估值计算失败，无法进行 LLM 分析。"


        # --- Build Final Response ---
        logger.info("Step 10: Building final response...")

        # 计算并添加到基础 DCF 详情中
        dcf_implied_diluted_pe_value = None
        if base_dcf_details and base_dcf_details.value_per_share is not None:
            latest_annual_eps = base_latest_metrics.get('latest_annual_diluted_eps')
            logger.info(f"Calculating DCF Implied PE: ValuePerShare={base_dcf_details.value_per_share}, LatestAnnualDilutedEPS={latest_annual_eps}")
            if latest_annual_eps is not None and isinstance(latest_annual_eps, Decimal) and latest_annual_eps > Decimal('0'):
                try:
                    dcf_implied_diluted_pe_value = float(Decimal(str(base_dcf_details.value_per_share)) / latest_annual_eps)
                    logger.info(f"Calculated DCF Implied PE Value: {dcf_implied_diluted_pe_value}")
                except (InvalidOperation, TypeError, ZeroDivisionError) as e_pe_calc:
                    logger.warning(f"Error calculating DCF implied diluted PE: VPS={base_dcf_details.value_per_share}, EPS={latest_annual_eps}. Error: {e_pe_calc}")
                    all_warnings.append(f"计算DCF隐含PE时出错: {e_pe_calc}")
            elif latest_annual_eps is not None: # EPS is zero or negative
                 logger.warning(f"Latest annual diluted EPS ({latest_annual_eps}) is zero or negative. Cannot calculate DCF implied PE.")
                 all_warnings.append(f"最近年报稀释EPS ({latest_annual_eps}) 为零或负数，无法计算DCF隐含PE。")
            else: # EPS is None
                 logger.warning("Latest annual diluted EPS is None. Cannot calculate DCF implied PE.")
                 all_warnings.append("无法获取最近年报稀释EPS，无法计算DCF隐含PE。")
        else:
            logger.warning("Base DCF details or value_per_share is None. Cannot calculate DCF implied PE.")
        
        if base_dcf_details: # 确保 base_dcf_details 不是 None
            base_dcf_details.dcf_implied_diluted_pe = dcf_implied_diluted_pe_value
            logger.info(f"Assigned dcf_implied_diluted_pe to base_dcf_details: {base_dcf_details.dcf_implied_diluted_pe}")

        results_container = ValuationResultsContainer(
            latest_price=latest_price,
            current_pe=base_latest_metrics.get('pe'),
            current_pb=base_latest_metrics.get('pb'),
            dcf_forecast_details=base_dcf_details, # Use base case details for main display (now includes PE)
            llm_analysis_summary=llm_summary,
            data_warnings=list(set(all_warnings)) if all_warnings else None, # Remove duplicate warnings
            detailed_forecast_table=base_forecast_df.to_dict(orient='records') if base_forecast_df is not None and not base_forecast_df.empty else None, # Use base forecast table
            sensitivity_analysis_result=sensitivity_result_obj # Add sensitivity results if available
        )
        logger.info("Valuation request processed successfully.")
        # Use StockBasicInfoModel for stock_info
        final_stock_info = StockBasicInfoModel(**base_basic_info) if base_basic_info else StockBasicInfoModel()
        return StockValuationResponse(
            stock_info=final_stock_info,
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
