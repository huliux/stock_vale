import os
from dotenv import load_dotenv # Import load_dotenv
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

# 导入新的工具函数
from api.utils import decimal_default, generate_axis_values_backend, build_historical_financial_summary # regenerate_axis_if_needed is now called by ValuationService
from api.llm_utils import load_prompt_template, format_llm_input_data, call_llm_api
from services.valuation_service import ValuationService # Updated import
# regenerate_axis_if_needed is now part of api.utils and called by ValuationService, so no direct import needed here for it.

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

# Load environment variables from .env file AT THE VERY TOP after standard imports
load_dotenv() 

# Initialize logger early
logger = logging.getLogger(__name__)

# Log the provider at startup for initial check, but it will be fetched per request later
# This is just for an initial startup log. The actual provider used will be fetched dynamically.
_initial_llm_provider_check = os.getenv("LLM_PROVIDER", "deepseek").lower()
logger.info(f"Initial LLM_PROVIDER from .env at startup: {_initial_llm_provider_check}")


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

# Import and include screener router
from .routers import screener as screener_router
app.include_router(screener_router.router, prefix="/api/v1")

# Import functions from StockScreenerService to load data from .feather files
from services.stock_screener_service import get_latest_valid_trade_date, load_stock_basic, load_daily_basic, StockScreenerServiceError

# Note: _run_single_valuation, format_llm_input_data, and call_llm_api
# have been moved to services/valuation_service.py and api/llm_utils.py respectively.
# LLM Configuration and helper functions (load_prompt_template, format_llm_input_data, call_llm_api)
# were previously here and are now in api/llm_utils.py.

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
    # Force reload of .env file for each request to pick up changes to LLM_PROVIDER
    load_dotenv(override=True) 
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
        # Initial fetch from database
        db_stock_info_dict = fetcher.get_stock_info() 
        db_latest_price = fetcher.get_latest_price() 
        db_latest_pe_pb = fetcher.get_latest_pe_pb(request.valuation_date)
        
        # Attempt to load data from .feather files and override/supplement DB data
        feather_stock_info_dict = {}
        feather_latest_price_val = None
        feather_pe_val = None
        feather_pb_val = None

        try:
            logger.info(f"Attempting to load data from .feather cache for {request.ts_code}")
            latest_trade_date_for_cache = get_latest_valid_trade_date()
            
            stock_basic_df = load_stock_basic(force_update=False)
            daily_basic_df = load_daily_basic(latest_trade_date_for_cache, force_update=False)

            if not stock_basic_df.empty:
                stock_specific_basic = stock_basic_df[stock_basic_df['ts_code'] == request.ts_code]
                if not stock_specific_basic.empty:
                    feather_stock_info_dict['name'] = stock_specific_basic['name'].iloc[0]
                    feather_stock_info_dict['industry'] = stock_specific_basic['industry'].iloc[0]
                    feather_stock_info_dict['market'] = stock_specific_basic['market'].iloc[0]
                    # ts_code is already known from request
                    logger.info(f"Loaded basic info from stock_basic.feather for {request.ts_code}: {feather_stock_info_dict}")

            if not daily_basic_df.empty:
                stock_specific_daily = daily_basic_df[daily_basic_df['ts_code'] == request.ts_code]
                if not stock_specific_daily.empty:
                    feather_latest_price_val = stock_specific_daily['close'].iloc[0]
                    feather_pe_val = stock_specific_daily['pe_ttm'].iloc[0] # Assuming pe_ttm is the desired PE
                    feather_pb_val = stock_specific_daily['pb'].iloc[0]
                    logger.info(f"Loaded daily info from daily_basic.feather for {request.ts_code}: Price={feather_latest_price_val}, PE={feather_pe_val}, PB={feather_pb_val}")
        
        except StockScreenerServiceError as sse:
            logger.warning(f"Could not load data from .feather files for {request.ts_code}: {sse}. Will use database data as primary or fallback.")
        except Exception as e_feather:
            logger.error(f"Unexpected error loading from .feather files for {request.ts_code}: {e_feather}. Will use database data.")

        # Merge DB data with .feather data, prioritizing .feather data
        base_stock_info_dict = {**db_stock_info_dict, **feather_stock_info_dict} # Feather overrides DB for common keys
        latest_price = feather_latest_price_val if feather_latest_price_val is not None and pd.notna(feather_latest_price_val) else db_latest_price
        
        # For PE/PB, construct the dict similar to how db_latest_pe_pb is structured
        latest_pe_pb = db_latest_pe_pb.copy() if db_latest_pe_pb else {} # Start with DB data or empty dict
        if feather_pe_val is not None and pd.notna(feather_pe_val):
            latest_pe_pb['pe_ttm'] = feather_pe_val # Or 'pe' if that's the key used by DataProcessor
        if feather_pb_val is not None and pd.notna(feather_pb_val):
            latest_pe_pb['pb'] = feather_pb_val
        # Ensure 'pe' key exists if 'pe_ttm' was used from feather, for DataProcessor compatibility
        if 'pe_ttm' in latest_pe_pb and 'pe' not in latest_pe_pb:
             latest_pe_pb['pe'] = latest_pe_pb['pe_ttm']


        logger.info(f"Final merged basic info for {request.ts_code}: Name={base_stock_info_dict.get('name')}, Price={latest_price}, PE/PB={latest_pe_pb}")

        total_shares = fetcher.get_latest_total_shares(request.valuation_date) # 获取最新总股本 (float or None)
        total_shares_actual = total_shares * 100000000 if total_shares is not None and total_shares > 0 else None
        
        # 获取TTM股息数据
        valuation_date_to_use_for_ttm = request.valuation_date
        if not valuation_date_to_use_for_ttm:
            valuation_date_to_use_for_ttm = pd.Timestamp.now().strftime('%Y-%m-%d')
        ttm_dividends_df = fetcher.get_dividends_ttm(valuation_date_to_use_for_ttm)
        logger.info(f"  Fetched TTM dividends count: {len(ttm_dividends_df) if ttm_dividends_df is not None else 'None'}")

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
        processed_data_container = DataProcessor(
            all_data, 
            latest_pe_pb=latest_pe_pb,
            ttm_dividends_df=ttm_dividends_df, # 传递TTM股息数据
            latest_price=latest_price # 传递最新价格
        )
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
        logger.debug(f"  Base latest metrics including actual EBITDA: {base_latest_metrics}") # Changed to debug


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

        # --- Initialize ValuationService ---
        valuation_service = ValuationService(
            processed_data_container=processed_data_container,
            wacc_calculator=wacc_calculator,
            logger_override=logger 
        )

        # --- Run Base Case Valuation ---
        logger.info("Running base case valuation...")
        
        # Adjust terminal_value_method based on provided terminal_growth_rate
        # Removed: Problematic if block that switched method if terminal_growth_rate was present with exit_multiple
        if request.terminal_growth_rate is None and request.terminal_value_method == 'perpetual_growth':
            logger.warning("Perpetual growth method selected, but terminal_growth_rate is not provided. This might lead to errors or default behavior in calculation.")
            # Consider if a default should be forced here or if validation should catch it earlier.
            # For now, just a warning. The calculator might use its own default or error out.

        base_request_dict = request.model_dump() 
        
        # The `request` object now directly contains `discount_rate` and `terminal_growth_rate`
        # if they were sent by the client, due to Pydantic model field renaming.
        # These will be part of `base_request_dict`.
        # The `valuation_service.run_single_valuation` and subsequently `WaccCalculator`
        # and `TerminalValueCalculator` will need to be aware of these fields
        # and prioritize them if present.
        
        base_dcf_details, base_forecast_df, base_run_warnings = valuation_service.run_single_valuation(
            request_dict=base_request_dict, # This dict now includes 'discount_rate' and 'terminal_growth_rate' if provided
            total_shares_actual=total_shares_actual
            # No overrides for base case
        )
        all_warnings = base_data_warnings + base_run_warnings
        if base_dcf_details is None:
            # If base case fails, we cannot proceed with sensitivity or LLM
            raise HTTPException(status_code=500, detail=f"基础估值计算失败: {all_warnings[-1] if all_warnings else '未知错误'}")
        logger.info("Base case valuation successful.")

        # --- Sensitivity Analysis (if requested) ---
        if request.sensitivity_analysis and base_dcf_details: # Ensure base_dcf_details is available
            logger.info("Calling ValuationService for sensitivity analysis...")
            # Ensure all necessary parameters are passed to the service method
            sensitivity_result_obj, sensitivity_run_warnings = valuation_service.run_sensitivity_analysis(
                sa_request_model=request.sensitivity_analysis,
                base_dcf_details=base_dcf_details, # Pass DcfForecastDetails from base run
                base_request_dict=base_request_dict, # Pass the original request dict for base assumptions
                total_shares_actual=total_shares_actual, # Pass total shares
                base_latest_metrics=base_latest_metrics # Pass latest metrics for EV/EBITDA base
            )
            all_warnings.extend(sensitivity_run_warnings)
            if sensitivity_result_obj:
                logger.info("Sensitivity analysis by service complete.")
            else:
                logger.warning("Sensitivity analysis by service returned no result object, or an error occurred.")
        elif request.sensitivity_analysis and not base_dcf_details: # Base valuation failed
            logger.warning("Skipping sensitivity analysis because base valuation failed.")
            all_warnings.append("基础估值失败，跳过敏感性分析。")
        # If request.sensitivity_analysis is None, this block is skipped, sensitivity_result_obj remains None.

        # --- LLM Analysis (Based on Base Case) ---
        logger.info("Step 9: Preparing LLM input and calling API (based on base case)...")
        llm_summary = None
        # Check if LLM summary is requested and base DCF calculation was successful
        if request.request_llm_summary and base_dcf_details:
            logger.info("LLM summary requested. Proceeding with LLM call.")
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
                # Dynamically get LLM_PROVIDER and other LLM parameters from request or .env defaults
                provider_to_use = request.llm_provider or os.getenv("LLM_PROVIDER", "deepseek").lower()
                
                model_id_to_use = request.llm_model_id # Frontend should pass this; llm_utils will fallback if None
                api_base_to_use = request.llm_api_base_url # Frontend should pass for custom; llm_utils will fallback if None
                
                temp_to_use = request.llm_temperature if request.llm_temperature is not None else float(os.getenv("LLM_DEFAULT_TEMPERATURE", "0.7"))
                top_p_to_use = request.llm_top_p if request.llm_top_p is not None else float(os.getenv("LLM_DEFAULT_TOP_P", "0.9"))
                max_tokens_to_use = request.llm_max_tokens if request.llm_max_tokens is not None else int(os.getenv("LLM_DEFAULT_MAX_TOKENS", "4000"))

                logger.info(f"Using LLM Provider: {provider_to_use}, Model: {model_id_to_use or 'Default'}, Temp: {temp_to_use}, TopP: {top_p_to_use}, MaxTokens: {max_tokens_to_use}")
                if provider_to_use == "custom_openai" and api_base_to_use: # Log base_url only if custom and provided
                    logger.info(f"Custom OpenAI Base URL: {api_base_to_use}")
                elif provider_to_use == "custom_openai":
                    logger.info(f"Custom OpenAI Base URL from env: {os.getenv('CUSTOM_LLM_API_BASE_URL')}")


                llm_summary = call_llm_api(
                    prompt=prompt,
                    provider=provider_to_use,
                    model_id=model_id_to_use,
                    api_base_url=api_base_to_use,
                    temperature=temp_to_use,
                    top_p=top_p_to_use,
                    max_tokens=max_tokens_to_use
                )
                logger.info(f"  LLM call complete. Summary length: {len(llm_summary) if llm_summary else 0}")
            except Exception as llm_exc:
                logger.error(f"Error during LLM call: {llm_exc}")
                llm_summary = f"Error in LLM analysis: {str(llm_exc)}"
                all_warnings.append(f"LLM 分析失败: {str(llm_exc)}")
        elif not request.request_llm_summary:
            logger.info("LLM summary not requested by client. Skipping LLM call.")
            llm_summary = None # Or an empty string, or a specific message like "LLM analysis not requested."
        else: # This case means base_dcf_details is None
             logger.warning("Skipping LLM analysis because base valuation failed.")
             llm_summary = "基础估值计算失败，无法进行 LLM 分析。"


        # --- Build Final Response ---
        logger.info("Step 10: Building final response...")

        # --- Logic for Special Industry Warning ---
        special_warning_text: Optional[str] = None
        comp_type_value: Optional[str] = None
        
        if processed_data_container and processed_data_container.processed_data and \
           'balance_sheet' in processed_data_container.processed_data and \
           not processed_data_container.processed_data['balance_sheet'].empty and \
           'comp_type' in processed_data_container.processed_data['balance_sheet'].columns:
            
            try:
                bs_df_for_comp_type = processed_data_container.processed_data['balance_sheet'].copy()
                # Ensure 'end_date' is index for proper sorting to get latest
                # DataProcessor should ideally provide data with 'end_date' as sorted datetime index
                if 'end_date' in bs_df_for_comp_type.columns and not isinstance(bs_df_for_comp_type.index, pd.DatetimeIndex):
                    bs_df_for_comp_type['end_date'] = pd.to_datetime(bs_df_for_comp_type['end_date'])
                    bs_df_for_comp_type = bs_df_for_comp_type.set_index('end_date')
                
                if isinstance(bs_df_for_comp_type.index, pd.DatetimeIndex):
                    bs_df_for_comp_type = bs_df_for_comp_type.sort_index(ascending=False)
                
                if not bs_df_for_comp_type.empty:
                    comp_type_value_raw = bs_df_for_comp_type['comp_type'].iloc[0]
                    if pd.notna(comp_type_value_raw):
                        comp_type_value = str(comp_type_value_raw).strip()
                    else:
                        comp_type_value = None
                        logger.info("Latest comp_type value is NaN.")
                else:
                    logger.info("Balance sheet DataFrame for comp_type is empty after processing.")
            except Exception as e_ct:
                logger.warning(f"Could not reliably extract comp_type from balance_sheet: {e_ct}")

        if comp_type_value:
            FINANCIAL_COMP_TYPES_STR = ["2", "3", "4"] # 银行, 保险, 证券
            is_financial_stock = comp_type_value in FINANCIAL_COMP_TYPES_STR
            
            has_significant_warnings = False
            if all_warnings: # all_warnings is a list of strings
                # Check if there are more than 2 warnings OR specific keywords are present
                if len(all_warnings) > 2:
                    has_significant_warnings = True
                else:
                    for warn_msg in all_warnings:
                        if any(keyword in warn_msg for keyword in ["NWC", "营运资本", "流动资产", "流动负债", "周转天数", "cogs_to_revenue", "inventories/oper_cost", "accounts_receiv_bill/revenue", "accounts_pay/oper_cost"]):
                            has_significant_warnings = True
                            break
            
            if is_financial_stock and has_significant_warnings:
                special_warning_text = (
                    "您选择的股票属于金融行业。当前通用DCF估值模型可能不完全适用于此类公司，"
                    "且由于其财务数据结构的特殊性，部分关键财务数据可能缺失或已采用默认值处理。"
                    "这可能导致估值结果与实际情况存在较大偏差，请谨慎参考并结合其他分析方法。"
                )
                logger.info(f"Identified financial stock (comp_type: {comp_type_value}) with significant warnings. Setting special_industry_warning.")
        else:
            logger.info(f"Comp_type not found or not applicable for special industry warning. comp_type_value: {comp_type_value}")

        # --- Prepare historical_ratios_summary ---
        historical_ratios_summary_data = []
        if base_historical_ratios:
            for name, value in base_historical_ratios.items():
                historical_ratios_summary_data.append({"metric_name": name, "value": float(value) if isinstance(value, Decimal) else value})
        
        # --- Prepare historical_financial_summary (Moved to utils) ---
        historical_financial_summary_data = build_historical_financial_summary(processed_data_container)
        if historical_financial_summary_data:
            logger.debug(f"DEBUG: Fetched historical_financial_summary_data from util (first 2 items): {json.dumps(historical_financial_summary_data[:2], ensure_ascii=False, default=str)}")


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

            # 计算并添加基础 EV/EBITDA
            base_ev_ebitda_value = None
            latest_actual_ebitda = base_latest_metrics.get('latest_actual_ebitda')
            if base_dcf_details.enterprise_value is not None and latest_actual_ebitda is not None and isinstance(latest_actual_ebitda, Decimal) and latest_actual_ebitda > Decimal('0'):
                try:
                    base_ev_ebitda_value = float(Decimal(str(base_dcf_details.enterprise_value)) / latest_actual_ebitda)
                    logger.info(f"Calculated Base EV/EBITDA: {base_ev_ebitda_value}")
                except (InvalidOperation, TypeError, ZeroDivisionError) as e_ev_ebitda_calc:
                    logger.warning(f"Error calculating Base EV/EBITDA: EV={base_dcf_details.enterprise_value}, EBITDA={latest_actual_ebitda}. Error: {e_ev_ebitda_calc}")
                    all_warnings.append(f"计算基础EV/EBITDA时出错: {e_ev_ebitda_calc}")
            elif latest_actual_ebitda is None or not (isinstance(latest_actual_ebitda, Decimal) and latest_actual_ebitda > Decimal('0')):
                logger.warning(f"Cannot calculate Base EV/EBITDA due to invalid latest_actual_ebitda: {latest_actual_ebitda}")
                all_warnings.append(f"无法计算基础EV/EBITDA，因为最新实际EBITDA无效: {latest_actual_ebitda}")
            
            base_dcf_details.base_ev_ebitda = base_ev_ebitda_value
            logger.info(f"Assigned base_ev_ebitda to base_dcf_details: {base_dcf_details.base_ev_ebitda}")

            # 计算隐含永续增长率 (如果使用退出乘数法)
            implied_pgr_value = None
            if base_dcf_details.terminal_value_method_used == 'exit_multiple' and \
               base_dcf_details.terminal_value is not None and \
               base_dcf_details.wacc_used is not None and \
               base_forecast_df is not None and not base_forecast_df.empty and \
               'ufcf' in base_forecast_df.columns:
                
                try:
                    tv_decimal = Decimal(str(base_dcf_details.terminal_value))
                    wacc_decimal = Decimal(str(base_dcf_details.wacc_used))
                    # 获取预测期最后一年的 UFCF
                    fcf_t_decimal = Decimal(str(base_forecast_df['ufcf'].iloc[-1]))

                    if (tv_decimal + fcf_t_decimal) != Decimal('0'): # 避免除以零
                        # PGR = (TV * WACC - FCF_T) / (TV + FCF_T)
                        numerator = (tv_decimal * wacc_decimal) - fcf_t_decimal
                        denominator = tv_decimal + fcf_t_decimal
                        implied_pgr_value = float(numerator / denominator)
                        logger.info(f"Calculated Implied Perpetual Growth Rate: {implied_pgr_value:.4f}")
                    else:
                        logger.warning("Cannot calculate Implied PGR: TV + FCF_T is zero.")
                        all_warnings.append("无法计算隐含永续增长率：终值与终期现金流之和为零。")
                except Exception as e_ipgr:
                    logger.error(f"Error calculating Implied Perpetual Growth Rate: {e_ipgr}")
                    all_warnings.append(f"计算隐含永续增长率时出错: {str(e_ipgr)}")
            
            if base_dcf_details: # 再次确保 base_dcf_details 存在
                base_dcf_details.implied_perpetual_growth_rate = implied_pgr_value
                logger.info(f"Assigned implied_perpetual_growth_rate to base_dcf_details: {base_dcf_details.implied_perpetual_growth_rate}")

        results_container = ValuationResultsContainer(
            latest_price=latest_price,
            current_pe=base_latest_metrics.get('pe'),
            current_pb=base_latest_metrics.get('pb'),
            dcf_forecast_details=base_dcf_details, # Use base case details for main display (now includes PE)
            llm_analysis_summary=llm_summary,
            data_warnings=list(set(all_warnings)) if all_warnings else None, # Remove duplicate warnings
            detailed_forecast_table=base_forecast_df.to_dict(orient='records') if base_forecast_df is not None and not base_forecast_df.empty else None, # Use base forecast table
            sensitivity_analysis_result=sensitivity_result_obj, # Add sensitivity results if available
            historical_financial_summary=historical_financial_summary_data if historical_financial_summary_data else None,
            historical_ratios_summary=historical_ratios_summary_data if historical_ratios_summary_data else None,
            special_industry_warning=special_warning_text # Add the new field here
        )
        logger.info("Valuation request processed successfully.")
        # Use StockBasicInfoModel for stock_info
        final_stock_info_data = base_basic_info.copy() if base_basic_info else {}
        # 从 base_latest_metrics 获取 TTM DPS 和股息率 (DataProcessor 初始化时已计算并存储)
        final_stock_info_data['ttm_dps'] = base_latest_metrics.get('ttm_dps')
        final_stock_info_data['dividend_yield'] = base_latest_metrics.get('dividend_yield')
        # 新增：从 base_basic_info 获取 market (DataProcessor 已处理默认值)
        final_stock_info_data['market'] = base_basic_info.get('market')
        # 新增：从 base_latest_metrics 获取 latest_annual_diluted_eps
        final_stock_info_data['latest_annual_diluted_eps'] = base_latest_metrics.get('latest_annual_diluted_eps')
        # 新增：从 DataProcessor 获取基准财务报表日期
        if processed_data_container: # 确保 processed_data_container 已被初始化
            final_stock_info_data['base_report_date'] = processed_data_container.get_base_financial_statement_date()
        
        final_stock_info = StockBasicInfoModel(**final_stock_info_data)
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
