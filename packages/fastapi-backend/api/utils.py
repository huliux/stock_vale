import logging
import numpy as np
import pandas as pd
from decimal import Decimal, InvalidOperation
from typing import List, Dict, Any, Optional # Added Optional

# Attempt to import DataProcessor for type hinting
try:
    from data_processor import DataProcessor
except ImportError:
    class DataProcessor: # type: ignore
        pass # Placeholder if not found

# Attempt to import models for type hinting
try:
    from api.models import DcfForecastDetails # For type hinting
    from api.sensitivity_models import SensitivityAxisInput, MetricType # For type hinting
except ImportError:
    class DcfForecastDetails: pass # type: ignore
    class SensitivityAxisInput: pass # type: ignore
    class MetricType: # type: ignore
        WACC = "wacc"
        TERMINAL_GROWTH_RATE = "perpetual_growth_rate"
        TERMINAL_EBITDA_MULTIPLE = "exit_multiple"
        # Add other metric types if needed for fallback logic

logger = logging.getLogger(__name__) # This logger will be for utils.py
# The regenerate_axis_if_needed function will accept a logger instance from the caller.

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

# --- Historical Financial Summary Builder ---
def build_historical_financial_summary(processed_data_container: DataProcessor) -> List[Dict[str, Any]]:
    """
    Builds the historical financial summary data from processed data.
    """
    historical_financial_summary_data = []
    if not processed_data_container or not processed_data_container.processed_data:
        return historical_financial_summary_data

    core_items_config = {
        "income_statement": {
            "营业总收入": "total_revenue", "毛利润": "gross_profit",
            "营业利润": "operate_profit", "净利润": "n_income", "研发费用": "rd_exp"
        },
        "balance_sheet": {
            "总资产": "total_assets", "总负债": "total_liab",
            "股东权益合计": "total_hldr_eqy_exc_min_int",
            "流动资产合计": "total_cur_assets", "流动负债合计": "total_cur_liab",
            "货币资金": "money_cap", "应收账款及票据": "accounts_receiv_bill",
            "存货": "inventories", "固定资产": "fix_assets_total",
            "短期借款": "st_borr", "长期借款": "lt_borr"
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
        
        if df is not None and not df.empty:
            df_for_years = df.copy()
            if 'end_date' in df_for_years.columns:
                df_for_years['end_date'] = pd.to_datetime(df_for_years['end_date'])
                df_for_years = df_for_years.set_index('end_date')
            
            if df_for_years.index.name == 'end_date':
                df_for_years = df_for_years.sort_index(ascending=False)
            else:
                logger.warning(f"Skipping report_type {report_type} for historical summary due to missing 'end_date' index.")
                continue

            annual_report_dates = sorted(
                [date for date in df_for_years.index.unique() if date.month == 12],
                reverse=True
            )
            display_dates = annual_report_dates[:num_years_to_display]
            if len(display_dates) < num_years_to_display: # Fallback if not enough annual reports
                all_report_dates = sorted(df_for_years.index.unique(), reverse=True)
                display_dates = all_report_dates[:num_years_to_display]

            display_years_str = [date.strftime('%Y') for date in display_dates]

            for display_name, actual_col_name in items_map.items():
                item_data = {"科目": display_name, "报表类型": report_type.replace("_", " ").title()}
                
                if report_type == "income_statement" and actual_col_name == "gross_profit":
                    if "total_revenue" in df_for_years.columns and "oper_cost" in df_for_years.columns:
                        for i, date_obj in enumerate(display_dates):
                            year_str = display_years_str[i]
                            row = df_for_years[df_for_years.index == date_obj]
                            if not row.empty:
                                revenue = row["total_revenue"].iloc[0]
                                cost = row["oper_cost"].iloc[0]
                                item_data[year_str] = float(Decimal(str(revenue)) - Decimal(str(cost))) if pd.notna(revenue) and pd.notna(cost) else None
                            else: item_data[year_str] = None
                    else: 
                        for year_str in display_years_str: item_data[year_str] = None
                elif actual_col_name in df_for_years.columns:
                    for i, date_obj in enumerate(display_dates):
                        year_str = display_years_str[i]
                        row = df_for_years[df_for_years.index == date_obj]
                        if not row.empty and pd.notna(row[actual_col_name].iloc[0]):
                            try:
                                item_data[year_str] = float(Decimal(str(row[actual_col_name].iloc[0])))
                            except InvalidOperation: item_data[year_str] = None
                        else: item_data[year_str] = None
                else:
                    for year_str in display_years_str: item_data[year_str] = None
                historical_financial_summary_data.append(item_data)
    
    # For debugging, can be removed or commented out in production
    # import json
    # if historical_financial_summary_data:
    #     logger.debug(f"Built historical_financial_summary_data (first 2 items): {json.dumps(historical_financial_summary_data[:2], ensure_ascii=False, default=str)}")
        
    return historical_financial_summary_data

# --- Axis Regeneration Helper (Moved from api/main.py) ---
def regenerate_axis_if_needed(
    axis_input: SensitivityAxisInput, 
    base_details: Optional[DcfForecastDetails], 
    param_name: str, 
    is_row_axis: bool, 
    base_req_dict: Dict[str, Any],
    logger_obj: logging.Logger, # Pass logger instance from caller
    sensitivity_warnings_list: List[str] # Pass warnings list from caller
) -> List[float]:
    current_values = axis_input.values
    should_regenerate = False
    center_val = None

    # For WACC, always try to regenerate if step/points are given, using base_wacc as center
    if param_name == MetricType.WACC.value: # type: ignore
        if axis_input.step is not None and axis_input.points is not None:
            center_val = base_details.wacc_used if base_details else None
            if center_val is None: # Fallback to request input for WACC if base_details.wacc_used is None
                center_val = base_req_dict.get('wacc') 
                if center_val is None: 
                    pass # Further fallback logic might be needed if wacc_calculator was involved
            
            if center_val is not None:
                should_regenerate = True
            else:
                logger_obj.warning(f"Cannot regenerate WACC axis for {'row' if is_row_axis else 'column'} due to missing base WACC and no fallback in request. Using original values if provided, else empty.")
                sensitivity_warnings_list.append(f"WACC轴无法重新生成（缺少基础WACC且请求中无回退值），将使用请求中提供的原始值（如果存在）。")
    
    # For other params, regenerate only if values list is empty AND step/points are given
    elif not current_values and axis_input.step is not None and axis_input.points is not None:
        if param_name == MetricType.TERMINAL_GROWTH_RATE.value: # type: ignore
            center_val = base_details.perpetual_growth_rate_used if base_details else None
            if center_val is None: center_val = base_req_dict.get('perpetual_growth_rate')
        elif param_name == MetricType.TERMINAL_EBITDA_MULTIPLE.value: # type: ignore
            center_val = base_details.exit_multiple_used if base_details else None
            if center_val is None: center_val = base_req_dict.get('exit_multiple')
            if center_val is None: 
                center_val = 8.0 # Default exit multiple
                logger_obj.info(f"Using hardcoded default center value {center_val} for {param_name} axis for {'row' if is_row_axis else 'column'}.")
                sensitivity_warnings_list.append(f"{param_name}轴缺少基准值和请求值，使用默认中心值 {center_val}。")
        
        if center_val is not None:
            try:
                center_val = float(center_val)
                should_regenerate = True
            except (ValueError, TypeError):
                logger_obj.warning(f"Cannot convert center_val '{center_val}' to float for {param_name} axis for {'row' if is_row_axis else 'column'}. Using original (empty) values.")
                sensitivity_warnings_list.append(f"{param_name}轴的中心值 '{center_val}' 无法转换为浮点数，将使用空的原始值列表。")
                should_regenerate = False
        else:
            logger_obj.warning(f"Cannot regenerate {param_name} axis for {'row' if is_row_axis else 'column'} due to missing base value and no fallback in request. Using original (empty) values.")
            sensitivity_warnings_list.append(f"{param_name}轴无法重新生成（所有回退机制均失败），将使用空的原始值列表。")
    
    if should_regenerate and center_val is not None:
        logger_obj.info(f"Regenerating {'row' if is_row_axis else 'column'} axis for {param_name} around center value: {center_val:.4f}, Step: {axis_input.step}, Points: {axis_input.points}")
        return generate_axis_values_backend( # This function is already in api/utils.py
            center=float(center_val),
            step=float(axis_input.step), # type: ignore
            points=int(axis_input.points) # type: ignore
        )
    
    return current_values if current_values is not None else []
