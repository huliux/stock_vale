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

# 导入新的工具函数
from api.utils import decimal_default, generate_axis_values_backend, build_historical_financial_summary # 新增导入
from api.llm_utils import load_prompt_template, format_llm_input_data, call_llm_api
from services.valuation_service import run_single_valuation # 新增导入

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

        # --- Run Base Case Valuation ---
        logger.info("Running base case valuation...")
        base_request_dict = request.model_dump() # Get base assumptions, updated from .dict()
        base_dcf_details, base_forecast_df, base_run_warnings = run_single_valuation(
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
                    dcf_details_sens, forecast_df_sens, run_warnings_sens = run_single_valuation(
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
                llm_summary = call_llm_api(prompt)
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
                llm_summary = call_llm_api(prompt)
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
        
        # --- Prepare historical_financial_summary ---
        historical_financial_summary_data = []
        if processed_data_container and processed_data_container.processed_data:
            core_items_config = {
                "income_statement": {
                    "营业总收入": "total_revenue",
                    "毛利润": "gross_profit", # Need to calculate if not present: total_revenue - oper_cost
                    "营业利润": "operate_profit", # or 'ebit'
                    "净利润": "n_income",
                    "研发费用": "rd_exp"
                },
                "balance_sheet": {
                    "总资产": "total_assets",
                    "总负债": "total_liab",
                    "股东权益合计": "total_hldr_eqy_exc_min_int", # Corrected to exc_min_int
                    "流动资产合计": "total_cur_assets",
                    "流动负债合计": "total_cur_liab",
                    "货币资金": "money_cap",
                    "应收账款及票据": "accounts_receiv_bill", 
                    "存货": "inventories",
                    "固定资产": "fix_assets_total", # Changed to fix_assets_total based on log
                    "短期借款": "st_borr",
                    "长期借款": "lt_borr"
                    # "净债务" is calculated, not directly from raw report for this summary
                },
                "cash_flow": {
                    "经营活动现金流量净额": "n_cashflow_act",
                    "投资活动现金流量净额": "n_cashflow_inv_act",
                    "筹资活动现金流量净额": "n_cashflow_fin_act"
                }
            }
            
            num_years_to_display = 5

            for report_type, items_map in core_items_config.items():
                df = processed_data_container.processed_data.get(report_type)
                
                # Debug log for balance sheet - this block should be at the same indent level as the next 'if'
                if report_type == "balance_sheet" and df is not None: 
                    logger.debug(f"DEBUG_BS: Balance Sheet columns from DataProcessor: {df.columns.tolist()}") # Changed to debug
                    logger.debug(f"DEBUG_BS: Balance Sheet head (from DataProcessor):\n{df.head().to_string()}") # Changed to debug
                    logger.debug(f"DEBUG_BS: Balance Sheet index name from DataProcessor: {df.index.name}") # Changed to debug

                if df is not None and not df.empty: # MODIFIED CONDITION: Only check if df is valid
                    df_for_years = df.copy()
                    # Ensure end_date is the index and sorted
                    if 'end_date' in df_for_years.columns:
                        df_for_years['end_date'] = pd.to_datetime(df_for_years['end_date'])
                        df_for_years = df_for_years.set_index('end_date')
                    
                    if df_for_years.index.name == 'end_date':
                        df_for_years = df_for_years.sort_index(ascending=False)
                    else:
                        logger.warning(f"DEBUG_MAIN: Skipping report_type {report_type} because 'end_date' could not be set or confirmed as index.")
                        continue # Skip this report type if end_date cannot be made index

                    # This debug log is correctly indented relative to its purpose
                    if report_type == "balance_sheet":
                        logger.debug(f"DEBUG_BS: df_for_years head (after indexing and sorting):\n{df_for_years.head().to_string()}") # Changed to debug
                        logger.debug(f"DEBUG_BS: df_for_years index name: {df_for_years.index.name}") # Changed to debug

                    annual_report_dates = sorted(
                        [date for date in df_for_years.index.unique() if date.month == 12],
                        reverse=True
                    )
                    
                    if len(annual_report_dates) < num_years_to_display:
                        all_report_dates = sorted(df_for_years.index.unique(), reverse=True)
                        display_dates = all_report_dates[:num_years_to_display]
                    else:
                        display_dates = annual_report_dates[:num_years_to_display]

                    if report_type == "balance_sheet":
                        logger.debug(f"DEBUG_BS: Display dates: {display_dates}") # Changed to debug

                    display_years_str = [date.strftime('%Y') for date in display_dates]

                    for display_name, actual_col_name in items_map.items():
                        item_data = {"科目": display_name, "报表类型": report_type.replace("_", " ").title()}
                        
                        if report_type == "balance_sheet":
                             logger.debug(f"DEBUG_BS: --- Processing Item: {display_name} (maps to: {actual_col_name}) ---") # Changed to debug

                        # Special handling for Gross Profit
                        if report_type == "income_statement" and actual_col_name == "gross_profit":
                            if "total_revenue" in df_for_years.columns and "oper_cost" in df_for_years.columns:
                                for i, date_obj in enumerate(display_dates):
                                    year_str = display_years_str[i]
                                    row = df_for_years[df_for_years.index == date_obj]
                                    if not row.empty:
                                        revenue = row["total_revenue"].iloc[0]
                                        cost = row["oper_cost"].iloc[0]
                                        if pd.notna(revenue) and pd.notna(cost):
                                            item_data[year_str] = float(Decimal(str(revenue)) - Decimal(str(cost)))
                                        else:
                                            item_data[year_str] = None
                                    else:
                                        item_data[year_str] = None
                            else: # Missing components for gross profit
                                for year_str in display_years_str: item_data[year_str] = None
                        
                        elif actual_col_name in df_for_years.columns:
                            if report_type == "balance_sheet": 
                                logger.debug(f"DEBUG_BS: Item: '{display_name}' (col: '{actual_col_name}') - FOUND in df_for_years.columns.") # Changed to debug
                            for i, date_obj in enumerate(display_dates):
                                year_str = display_years_str[i]
                                row = df_for_years[df_for_years.index == date_obj]
                                if not row.empty and actual_col_name in row.columns and pd.notna(row[actual_col_name].iloc[0]):
                                    try:
                                        value_to_add = float(Decimal(str(row[actual_col_name].iloc[0])))
                                        item_data[year_str] = value_to_add
                                        if report_type == "balance_sheet":
                                            logger.debug(f"DEBUG_BS: Item: '{display_name}', Year: {year_str}, Date: {date_obj}, Raw Value: {row[actual_col_name].iloc[0]}, Added Value: {value_to_add}") # Changed to debug
                                    except InvalidOperation:
                                        item_data[year_str] = None 
                                        if report_type == "balance_sheet":
                                            logger.warning(f"DEBUG_BS: Item: '{display_name}', Year: {year_str}, Date: {date_obj}, InvalidOperation for value: {row[actual_col_name].iloc[0]}")
                                else:
                                    item_data[year_str] = None 
                                    if report_type == "balance_sheet":
                                        logger.debug(f"DEBUG_BS: Item: '{display_name}', Year: {year_str}, Date: {date_obj}, Value: None (Reason: row empty? {row.empty}; col in row? {actual_col_name in row.columns if not row.empty else 'N/A'}; val notna? {pd.notna(row[actual_col_name].iloc[0]) if not row.empty and actual_col_name in row.columns else 'N/A'})") # Changed to debug
                        else: # Column not found in this df
                            if report_type == "balance_sheet": 
                                logger.warning(f"DEBUG_BS: Item: '{display_name}' (col: '{actual_col_name}') - NOT FOUND in df_for_years.columns. Available: {df_for_years.columns.tolist()}")
                            for year_str in display_years_str: item_data[year_str] = None
                        
                        historical_financial_summary_data.append(item_data)
            if historical_financial_summary_data: 
                logger.debug(f"DEBUG: Final historical_financial_summary_data (first 5 items): {json.dumps(historical_financial_summary_data[:5], ensure_ascii=False, default=str)}") # Changed to debug

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
    uvicorn.run(app, host="0.0.0.0", port=8125)
