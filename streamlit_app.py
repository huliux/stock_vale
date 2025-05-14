import streamlit as st
import requests
import pandas as pd
import json
import traceback
import os # 导入 os 以使用 getenv
from dotenv import load_dotenv # 导入 dotenv
import numpy as np # Import numpy for isnan check and closest index finding
from st_utils import (
    generate_axis_values, 
    find_closest_index, 
    highlight_center_cell_apply, 
    get_unique_formatted_labels,
    supported_axis_params, # Import constants
    supported_output_metrics # Import constants
)
from stock_screener_data import (
    get_tushare_pro_api, 
    get_latest_valid_trade_date,
    load_stock_basic,  # Added for screener data update
    load_daily_basic,  # Added for screener data update
    get_merged_stock_data # Added for screener filtering
) # 筛选器需要
from datetime import datetime # 筛选器需要

load_dotenv() # 在应用早期加载 .env 文件

# --- 页面配置与渲染函数 ---
def render_page_config_and_title():
    st.set_page_config(page_title="股票估值分析工具", layout="wide")

    custom_css = """
    <style>
        /* 减小 st.metric 中数值的字体大小 */
        div[data-testid="stMetricValue"] {
            font-size: 24px !important; /* 例如 24px，可以根据需要调整 */
        }
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)

    st.title("📈 稳稳的估吧")
    st.caption("长期投资就是耐心等待。")

render_page_config_and_title() # MOVED TO BE THE FIRST STREAMLIT COMMAND AFTER IMPORTS

# --- 配置 ---
API_ENDPOINT = os.getenv("API_ENDPOINT", "http://127.0.0.1:8125/api/v1/valuation") 

# --- Tushare API 初始化 (用于股票筛选器) ---
@st.cache_resource
def init_pro_api():
    return get_tushare_pro_api()

pro = init_pro_api()

# --- 股票筛选器状态管理 ---
# Ensure session_state is accessed only after set_page_config
if 'latest_trade_date' not in st.session_state:
    st.session_state.latest_trade_date = None
if 'stock_basic_last_update' not in st.session_state:
    st.session_state.stock_basic_last_update = "N/A"
if 'daily_basic_last_update' not in st.session_state:
    st.session_state.daily_basic_last_update = "N/A"
if 'daily_basic_data_date' not in st.session_state:
    st.session_state.daily_basic_data_date = "N/A"
if 'screener_merged_data' not in st.session_state: # Renamed from merged_data to avoid conflict
    st.session_state.screener_merged_data = pd.DataFrame()
if 'screener_filtered_data' not in st.session_state: # Renamed from filtered_data
    st.session_state.screener_filtered_data = pd.DataFrame()

def update_screener_data_status(): # Renamed from update_data_status
    """Updates the status of cached screener data."""
    stock_basic_cache_path = os.path.join("data_cache", "stock_basic.feather")
    if os.path.exists(stock_basic_cache_path):
        st.session_state.stock_basic_last_update = datetime.fromtimestamp(
            os.path.getmtime(stock_basic_cache_path)
        ).strftime('%Y-%m-%d %H:%M:%S')
    else:
        st.session_state.stock_basic_last_update = "无本地缓存"

    if st.session_state.latest_trade_date:
        daily_basic_cache_path = os.path.join("data_cache", f"daily_basic_{st.session_state.latest_trade_date}.feather")
        if os.path.exists(daily_basic_cache_path):
            st.session_state.daily_basic_last_update = datetime.fromtimestamp(
                os.path.getmtime(daily_basic_cache_path)
            ).strftime('%Y-%m-%d %H:%M:%S')
            st.session_state.daily_basic_data_date = st.session_state.latest_trade_date
        else:
            st.session_state.daily_basic_last_update = "无本地缓存"
            st.session_state.daily_basic_data_date = "N/A"
    else:
        st.session_state.daily_basic_last_update = "等待确定交易日"
        st.session_state.daily_basic_data_date = "N/A"

# Initialize latest_trade_date for screener if not already set
if pro and st.session_state.latest_trade_date is None:
    with st.spinner("正在获取最新交易日 (用于筛选器)..."): # Added context for spinner
        st.session_state.latest_trade_date = get_latest_valid_trade_date(pro)
    update_screener_data_status()

# Initial screener data status update on first load
if 'screener_initial_load_done' not in st.session_state: # Renamed state variable
    if pro: # Only update if pro is available
        update_screener_data_status()
    st.session_state.screener_initial_load_done = True


# --- 页面配置与渲染函数 ---
def render_page_config_and_title():
    st.set_page_config(page_title="股票估值分析工具", layout="wide")

    custom_css = """
    <style>
        /* 减小 st.metric 中数值的字体大小 */
        div[data-testid="stMetricValue"] {
            font-size: 24px !important; /* 例如 24px，可以根据需要调整 */
        }
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)

    st.title("📈 稳稳的估吧")
    st.caption("长期投资就是耐心等待。")

# render_page_config_and_title() # CALL MOVED UP

# --- 敏感性分析辅助函数与回调 ---

# 回调函数 update_sensitivity_ui_elements 依赖 st.session_state 和全局常量
# supported_axis_params, supported_output_metrics (已从 st_utils 导入)
# 以及辅助函数 generate_axis_values (已从 st_utils 导入)

# --- 回调函数：更新敏感性分析UI元素 ---
def update_sensitivity_ui_elements():
    # 1. 获取基础假设值 (使用 .get 避免 KeyError)
    base_exit_multiple_val = st.session_state.get("tv_exit_multiple", 8.0) 
    if base_exit_multiple_val is None: base_exit_multiple_val = 8.0 # 进一步确保不是None

    base_pgr_val = st.session_state.get("tv_pg_rate", 0.025)
    if base_pgr_val is None: base_pgr_val = 0.025

    # 2. 获取当前选择的敏感性轴参数
    current_row_param_display = st.session_state.get("sens_row_param", "WACC")
    current_col_param_display = st.session_state.get("sens_col_param", "退出乘数 (EBITDA)") # Default might need adjustment based on row selection
    
    current_row_param_key = supported_axis_params.get(current_row_param_display, "wacc")
    
    # Ensure column default is different from row default if possible
    available_col_keys = [k for k, v in supported_axis_params.items() if v != current_row_param_key]
    if current_col_param_display not in available_col_keys and available_col_keys:
         current_col_param_display = available_col_keys[0] # Adjust default if row selection makes current col invalid
         st.session_state.sens_col_param = current_col_param_display # Update session state if changed

    current_col_param_key = supported_axis_params.get(current_col_param_display, "exit_multiple")


    # 3. 计算新的中心值
    try:
        # --- WACC 计算逻辑 (基于目标债务比例) ---
        wacc_calculated = None
        try:
            # 尝试从 session_state 获取计算 WACC 所需的参数
            rf = float(st.session_state.get('wacc_rf', 0.03))
            beta_val = float(st.session_state.get('wacc_beta', 1.0)) # 使用 wacc_beta key
            mrp = float(st.session_state.get('wacc_mrp', 0.06))
            rd = float(st.session_state.get('wacc_cost_debt', 0.05))
            tax = float(st.session_state.get('tax_rate', 0.25))
            debt_ratio = float(st.session_state.get('wacc_debt_ratio', 0.45)) # 使用 wacc_debt_ratio key
            
            if all(v is not None for v in [rf, beta_val, mrp, rd, tax, debt_ratio]):
                 cost_of_equity = rf + beta_val * mrp
                 equity_ratio = 1.0 - debt_ratio
                 wacc_calculated = (equity_ratio * cost_of_equity) + (debt_ratio * rd * (1 - tax))
        except (TypeError, ValueError, AttributeError):
             wacc_calculated = None 

        if current_row_param_key == "wacc":
            st.session_state.sens_row_center_value = wacc_calculated if wacc_calculated is not None else 0.08
        elif current_row_param_key == "exit_multiple":
            st.session_state.sens_row_center_value = float(base_exit_multiple_val)
        elif current_row_param_key == "perpetual_growth_rate":
            st.session_state.sens_row_center_value = float(base_pgr_val)
        
        if current_col_param_key == "wacc":
            st.session_state.sens_col_center_value = wacc_calculated if wacc_calculated is not None else 0.08
        elif current_col_param_key == "exit_multiple":
            st.session_state.sens_col_center_value = float(base_exit_multiple_val)
        elif current_col_param_key == "perpetual_growth_rate":
            st.session_state.sens_col_center_value = float(base_pgr_val)
            
    except (TypeError, ValueError):
        st.session_state.sens_row_center_value = st.session_state.get('sens_row_center_value', 0.0) 
        st.session_state.sens_col_center_value = st.session_state.get('sens_col_center_value', 0.0)

    # Update row step if parameter type (percent vs multiple) changed
    _prev_row_param_key_tracker = st.session_state.get('sens_row_param_key_tracker') 
    new_row_is_percent_type = current_row_param_key in ["wacc", "perpetual_growth_rate"]
    old_row_is_percent_type = _prev_row_param_key_tracker in ["wacc", "perpetual_growth_rate"] if _prev_row_param_key_tracker is not None else new_row_is_percent_type

    if _prev_row_param_key_tracker != current_row_param_key: 
        if new_row_is_percent_type != old_row_is_percent_type or _prev_row_param_key_tracker is None: 
            st.session_state.sens_row_step = 0.005 if new_row_is_percent_type else 0.5
    st.session_state.sens_row_param_key_tracker = current_row_param_key

    # Update col step if parameter type (percent vs multiple) changed
    _prev_col_param_key_tracker = st.session_state.get('sens_col_param_key_tracker')
    new_col_is_percent_type = current_col_param_key in ["wacc", "perpetual_growth_rate"]
    old_col_is_percent_type = _prev_col_param_key_tracker in ["wacc", "perpetual_growth_rate"] if _prev_col_param_key_tracker is not None else new_col_is_percent_type

    if _prev_col_param_key_tracker != current_col_param_key:
        if new_col_is_percent_type != old_col_is_percent_type or _prev_col_param_key_tracker is None:
            st.session_state.sens_col_step = 0.005 if new_col_is_percent_type else 0.5
    st.session_state.sens_col_param_key_tracker = current_col_param_key
    
    row_step_val = st.session_state.sens_row_step 
    col_step_val = st.session_state.sens_col_step 
    
    # Fallback if step values are somehow None after logic (should not happen with proper init and callback logic)
    if row_step_val is None: row_step_val = 0.005 if new_row_is_percent_type else 0.5
    if col_step_val is None: col_step_val = 0.005 if new_col_is_percent_type else 0.5

    row_points_val = st.session_state.get("sens_row_points", 5)
    col_points_val = st.session_state.get("sens_col_points", 5)

    final_row_values = generate_axis_values(st.session_state.get('sens_row_center_value', 0.0), row_step_val, row_points_val)
    final_col_values = generate_axis_values(st.session_state.get('sens_col_center_value', 0.0), col_step_val, col_points_val)

    row_format_spec = ".4f" if current_row_param_key != "exit_multiple" else ".1f"
    col_format_spec = ".4f" if current_col_param_key != "exit_multiple" else ".1f"
    
    try:
        st.session_state.sens_row_values_str = ", ".join([format(float(v), row_format_spec) for v in final_row_values])
        st.session_state.sens_col_values_str = ", ".join([format(float(v), col_format_spec) for v in final_col_values])
    except (ValueError, TypeError):
         st.session_state.sens_row_values_str = "Error generating list"
         st.session_state.sens_col_values_str = "Error generating list"

if 'sensitivity_initialized' not in st.session_state:
    st.session_state.sens_row_param = st.session_state.get('sens_row_param', "WACC")
    st.session_state.sens_col_param = st.session_state.get('sens_col_param', "退出乘数 (EBITDA)")
    _initial_row_param_key = supported_axis_params.get(st.session_state.sens_row_param, "wacc")
    _initial_col_param_key = supported_axis_params.get(st.session_state.sens_col_param, "exit_multiple")
    st.session_state.sens_row_step = st.session_state.get('sens_row_step', 0.005 if _initial_row_param_key in ["wacc", "perpetual_growth_rate"] else 0.5)
    st.session_state.sens_row_points = st.session_state.get('sens_row_points', 5)
    # Initialize steps based on these initial keys
    st.session_state.sens_row_step = 0.005 if _initial_row_param_key in ["wacc", "perpetual_growth_rate"] else 0.5
    st.session_state.sens_col_step = 0.005 if _initial_col_param_key in ["wacc", "perpetual_growth_rate"] else 0.5
    
    st.session_state.sens_row_param_key_tracker = _initial_row_param_key # Initialize tracker
    st.session_state.sens_col_param_key_tracker = _initial_col_param_key # Initialize tracker

    st.session_state.sens_col_points = st.session_state.get('sens_col_points', 5)
    st.session_state.sens_row_center_value = 0.0 
    st.session_state.sens_col_center_value = 0.0 
    st.session_state.sens_row_values_str = ""    
    st.session_state.sens_col_values_str = ""    
    st.session_state.sensitivity_initialized = True

# --- 函数：渲染基本信息区块 ---
def render_basic_info_section(stock_info, valuation_results):
    st.subheader(f"📋 基本信息")
    base_report_date_str = stock_info.get('base_report_date')
    if base_report_date_str:
        try:
            # Ensure pd is available or pass it as an argument if defined locally in the calling scope
            formatted_date = pd.to_datetime(base_report_date_str).strftime('%Y年%m月%d日')
            st.caption(f"本估值基于 {formatted_date} 年报数据")
        except Exception:
            st.caption(f"基准年报日期: {base_report_date_str}") # Fallback if formatting fails
    
    # 基本信息 - 第 1 行
    basic_info_row1_cols = st.columns(6)
    with basic_info_row1_cols[0]:
        with st.container():
            st.metric("股票代码", stock_info.get('ts_code', "N/A"))
    with basic_info_row1_cols[1]:
        with st.container():
            st.metric("股票名称", stock_info.get('name', "N/A"))
    with basic_info_row1_cols[2]:
        with st.container():
            st.metric("所属行业", stock_info.get('industry', "N/A"))
    with basic_info_row1_cols[3]:
        with st.container():
            st.metric("市场类型", stock_info.get('market', "未知"))
    with basic_info_row1_cols[4]:
        with st.container():
            st.metric("实控人名称", stock_info.get('act_name', "未知"))
    with basic_info_row1_cols[5]:
        with st.container():
            st.metric("实控人企业性质", stock_info.get('act_ent_type', "民营企业"))

    # 基本信息 - 第 2 行
    basic_info_row2_cols = st.columns(6)
    
    # 获取当前估值股票代码
    current_dcf_ts_code = stock_info.get('ts_code')
    screener_metrics = st.session_state.get('screener_metrics_for_dcf')
    
    use_screener_data = False
    screener_trade_date_str = None
    if screener_metrics and screener_metrics.get('ts_code') == current_dcf_ts_code:
        use_screener_data = True
        screener_trade_date = screener_metrics.get('trade_date')
        if screener_trade_date:
            try:
                screener_trade_date_str = pd.to_datetime(screener_trade_date, format='%Y%m%d').strftime('%Y-%m-%d')
            except: # Fallback if format is different or error
                screener_trade_date_str = str(screener_trade_date)

    # 获取指标值，优先从筛选器获取 (价格, PE, PB)
    latest_price_val = screener_metrics.get('close') if use_screener_data and screener_metrics.get('close') is not None else valuation_results.get('latest_price')
    current_pe_val = screener_metrics.get('pe') if use_screener_data and screener_metrics.get('pe') is not None else valuation_results.get('current_pe')
    current_pb_val = screener_metrics.get('pb') if use_screener_data and screener_metrics.get('pb') is not None else valuation_results.get('current_pb')
    
    # 股息率始终来自财报数据 (API)
    # API的dividend_yield是小数形式，如0.0333 for 3.33%
    raw_dividend_yield_from_api = stock_info.get('dividend_yield') 

    # 每股收益和TTM每股股息通常来自财报，继续使用API/stock_info的数据源
    latest_annual_eps_val = stock_info.get('latest_annual_diluted_eps')
    ttm_dps_val = stock_info.get('ttm_dps')

    price_suffix = f" ({screener_trade_date_str})" if use_screener_data and screener_trade_date_str and latest_price_val == screener_metrics.get('close') else ""
    pe_suffix = f" ({screener_trade_date_str})" if use_screener_data and screener_metrics.get('pe') is not None and screener_trade_date_str and current_pe_val == screener_metrics.get('pe') else ""
    pb_suffix = f" ({screener_trade_date_str})" if use_screener_data and screener_metrics.get('pb') is not None and screener_trade_date_str and current_pb_val == screener_metrics.get('pb') else ""
    # 股息率的后缀将基于财报，不显示筛选器日期
    dv_suffix = " (TTM)"


    with basic_info_row2_cols[0]:
        with st.container():
            st.metric(f"最新价格{price_suffix}", f"{float(latest_price_val):.2f}" if latest_price_val is not None else "N/A")
    with basic_info_row2_cols[1]:
        with st.container():
            st.metric(f"当前PE{pe_suffix}", f"{float(current_pe_val):.2f}" if current_pe_val is not None else "N/A")
    with basic_info_row2_cols[2]:
        with st.container():
            st.metric(f"当前PB{pb_suffix}", f"{float(current_pb_val):.2f}" if current_pb_val is not None else "N/A")
    with basic_info_row2_cols[3]:
        with st.container():
            st.metric("每股收益 (年报)", f"{float(latest_annual_eps_val):.2f}" if latest_annual_eps_val is not None else "N/A")
    
    with basic_info_row2_cols[4]:
        with st.container():
            if raw_dividend_yield_from_api is not None and pd.notna(raw_dividend_yield_from_api):
                try:
                    display_dv_percent = float(raw_dividend_yield_from_api) * 100 # API data is decimal, e.g., 0.0333
                    st.metric(f"股息率{dv_suffix}", f"{display_dv_percent:.2f}%")
                except ValueError: 
                    st.metric(f"股息率{dv_suffix}", "N/A")
            else: 
                st.metric(f"股息率{dv_suffix}", "N/A")
    
    with basic_info_row2_cols[5]:
        with st.container():
            if ttm_dps_val is not None:
                dps_display_val = float(ttm_dps_val)
                dps_format_str = ".4f" if abs(dps_display_val) < 0.01 and dps_display_val != 0 else ".2f"
                st.metric("TTM每股股息", f"{dps_display_val:{dps_format_str}}")
            else:
                st.metric("TTM每股股息", "N/A")

# --- 函数：渲染估值结果摘要区块 ---
def render_valuation_summary_section(dcf_details, valuation_results):
    st.subheader("💴 估值结果")

    # 估值结果 - 第 1 行
    valuation_results_row1_cols = st.columns(7) # 修改为7列
    dcf_value_per_share = dcf_details.get('value_per_share')
    latest_price_for_sm = valuation_results.get('latest_price')
    safety_margin = ((dcf_value_per_share / latest_price_for_sm) - 1) * 100 if dcf_value_per_share is not None and latest_price_for_sm is not None and latest_price_for_sm > 0 else None
    dcf_implied_pe_val = dcf_details.get('dcf_implied_diluted_pe')
    base_ev_ebitda_val = dcf_details.get('base_ev_ebitda')
    implied_pgr_val = dcf_details.get('implied_perpetual_growth_rate') # 获取新字段
    wacc_used_val = dcf_details.get('wacc_used')
    cost_of_equity_used_val = dcf_details.get('cost_of_equity_used')

    with valuation_results_row1_cols[0]:
        with st.container():
            st.metric("每股价值 (DCF)", f"{float(dcf_value_per_share):.2f}" if dcf_value_per_share is not None else "N/A")
    with valuation_results_row1_cols[1]:
        with st.container():
            st.metric("安全边际", f"{safety_margin:.1f}%" if safety_margin is not None else "N/A", delta=f"{safety_margin:.1f}%" if safety_margin is not None else None, delta_color="normal")
    with valuation_results_row1_cols[2]:
        with st.container():
            st.metric("隐含PE倍数", f"{float(dcf_implied_pe_val):.2f}x" if dcf_implied_pe_val is not None else "N/A")
    with valuation_results_row1_cols[3]:
        with st.container():
            st.metric("隐含 EV/EBITDA", f"{float(base_ev_ebitda_val):.2f}x" if base_ev_ebitda_val is not None else "N/A")
    with valuation_results_row1_cols[4]: # 新的第5个块
        with st.container():
            st.metric("隐含永续增长率", f"{float(implied_pgr_val) * 100:.2f}%" if implied_pgr_val is not None else "N/A")
    with valuation_results_row1_cols[5]: # 原第5，现第6
        with st.container():
            st.metric("WACC", f"{float(wacc_used_val) * 100:.2f}%" if wacc_used_val is not None else "N/A")
    with valuation_results_row1_cols[6]: # 原第6，现第7
        with st.container():
            st.metric("Ke (股权成本)", f"{float(cost_of_equity_used_val) * 100:.2f}%" if cost_of_equity_used_val is not None else "N/A")

    # 估值结果 - 第 2 行
    valuation_results_row2_cols = st.columns(7) # 修改为7列
    enterprise_value_val = dcf_details.get('enterprise_value')
    equity_value_val = dcf_details.get('equity_value')
    pv_forecast_ufcf_val = dcf_details.get('pv_forecast_ufcf')
    pv_terminal_value_val = dcf_details.get('pv_terminal_value')
    terminal_value_val = dcf_details.get('terminal_value')
    net_debt_val = dcf_details.get('net_debt')
    exit_multiple_used_val = dcf_details.get('exit_multiple_used') # 获取退出乘数

    with valuation_results_row2_cols[0]:
        with st.container():
            st.metric("企业价值 (EV)", f"{float(enterprise_value_val) / 1e8:.2f} 亿" if enterprise_value_val is not None else "N/A")
    with valuation_results_row2_cols[1]:
        with st.container():
            st.metric("股权价值", f"{float(equity_value_val) / 1e8:.2f} 亿" if equity_value_val is not None else "N/A")
    with valuation_results_row2_cols[2]:
        with st.container():
            st.metric("UFCF现值", f"{float(pv_forecast_ufcf_val) / 1e8:.2f} 亿" if pv_forecast_ufcf_val is not None else "N/A")
    with valuation_results_row2_cols[3]:
        with st.container():
            st.metric("终值现值", f"{float(pv_terminal_value_val) / 1e8:.2f} 亿" if pv_terminal_value_val is not None else "N/A")
    with valuation_results_row2_cols[4]:
        with st.container():
            st.metric("终值", f"{float(terminal_value_val) / 1e8:.2f} 亿" if terminal_value_val is not None else "N/A")
    with valuation_results_row2_cols[5]:
        with st.container():
            st.metric("净债务", f"{float(net_debt_val) / 1e8:.2f} 亿" if net_debt_val is not None else "N/A")
    with valuation_results_row2_cols[6]: # 新增的第7个块
        with st.container():
            if dcf_details.get('terminal_value_method_used') == 'exit_multiple' and exit_multiple_used_val is not None:
                st.metric("退出乘数", f"{float(exit_multiple_used_val):.1f}x")
            else:
                st.metric("退出乘数", "N/A")

# --- 函数：渲染数据警告 ---
def render_data_warnings(data_warnings):
    if data_warnings:
        with st.expander("⚠️ 数据处理警告", expanded=False):
            for warning in data_warnings:
                st.warning(warning)

# --- 函数：渲染特殊行业警告 ---
def render_special_industry_warning(warning_text):
    if warning_text:
        st.error(f"⚠️ **行业特别提示：** {warning_text}")

# --- 函数：渲染敏感性分析区块 ---
def render_sensitivity_analysis_section(sensitivity_data, base_assumptions, selected_output_metric_keys_from_ui, base_wacc_used, base_exit_multiple_used, base_pgr_used):
    if sensitivity_data: # No need to check sensitivity_enabled_for_this_run here, as it's checked before calling
        st.subheader("🔬 敏感性分析")
        try:
            row_param = sensitivity_data['row_parameter']
            col_param = sensitivity_data['column_parameter']
            row_vals = sensitivity_data['row_values']
            col_vals = sensitivity_data['column_values']
            result_tables = sensitivity_data['result_tables'] 

            center_row_val = None
            if row_param == 'wacc': center_row_val = base_wacc_used 
            elif row_param == 'exit_multiple': center_row_val = base_exit_multiple_used # Use the actual used value
            elif row_param == 'perpetual_growth_rate': center_row_val = base_pgr_used # Use the actual used value
            
            center_col_val = None
            if col_param == 'wacc': center_col_val = base_wacc_used
            elif col_param == 'exit_multiple': center_col_val = base_exit_multiple_used # Use the actual used value
            elif col_param == 'perpetual_growth_rate': center_col_val = base_pgr_used # Use the actual used value

            center_row_idx = find_closest_index(row_vals, center_row_val)
            center_col_idx = find_closest_index(col_vals, center_col_val)

            for metric_key in selected_output_metric_keys_from_ui: 
                if metric_key in result_tables:
                    table_data = result_tables[metric_key]
                    metric_display_name = next((k for k, v in supported_output_metrics.items() if v == metric_key), metric_key)
                    st.markdown(f"**{metric_display_name}**")
                    
                    df_sensitivity = pd.DataFrame(
                        table_data, 
                        index=get_unique_formatted_labels(row_vals, row_param), 
                        columns=get_unique_formatted_labels(col_vals, col_param)
                    )
                    
                    if metric_key == "value_per_share": cell_format = "{:,.2f}"
                    elif metric_key == "enterprise_value" or metric_key == "equity_value": cell_format = lambda x: f"{x/1e8:,.2f} 亿" if pd.notna(x) else "N/A"
                    elif metric_key == "ev_ebitda": cell_format = "{:.1f}x"
                    elif metric_key == "tv_ev_ratio": cell_format = "{:.1%}"
                    else: cell_format = "{:,.2f}"
                    
                    styled_df = df_sensitivity.style
                    if isinstance(cell_format, str): 
                        styled_df = styled_df.format(cell_format, na_rep='N/A')
                    else: 
                        styled_df = styled_df.format(cell_format, na_rep='N/A')
                    
                    styled_df = styled_df.highlight_null(color='lightgrey')
                    styled_df = styled_df.apply(highlight_center_cell_apply, center_row_idx=center_row_idx, center_col_idx=center_col_idx, axis=None) 
                    
                    st.dataframe(styled_df, use_container_width=True)
                    st.divider() 
                else:
                    st.warning(f"未找到指标 '{metric_key}' 的敏感性分析结果。")
        except Exception as e:
            st.error(f"无法显示敏感性分析表格: {e}")
            st.error(traceback.format_exc()) # For debugging

# --- 函数：渲染高级分析区块 ---
def render_advanced_analysis_section(valuation_results):
    with st.expander("高级分析", expanded=False):
        st.subheader("历史财务摘要")
        historical_financial_summary_data = valuation_results.get("historical_financial_summary")
        if historical_financial_summary_data:
            try:
                df_financial_summary = pd.DataFrame(historical_financial_summary_data)
                if "科目" in df_financial_summary.columns:
                    df_financial_summary = df_financial_summary.set_index("科目")
                
                year_cols_to_format = [col for col in df_financial_summary.columns if col.isdigit() and len(col) == 4]
                format_dict_fs = {col: "{:,.0f}" for col in year_cols_to_format}

                st.dataframe(df_financial_summary.style.format(format_dict_fs, na_rep='-'), use_container_width=True)
            except Exception as e_fs:
                st.error(f"渲染历史财务摘要时出错: {e_fs}")
        else:
            st.caption("未找到历史财务摘要数据。")

        st.subheader("历史财务比率")
        historical_ratios_summary_data = valuation_results.get("historical_ratios_summary")
        if historical_ratios_summary_data:
            try:
                ratio_display_names_map = {
                    "cogs_to_revenue_ratio": "主营业务成本率 (%)",
                    "sga_rd_to_revenue_ratio": "销售管理及研发费用率 (%)",
                    "operating_margin_median": "营业利润率 (中位数 %)",
                    "operating_margin": "营业利润率 (中位数 %)",
                    "da_to_revenue_ratio": "折旧与摊销率 (占收入 %)",
                    "capex_to_revenue_ratio": "资本支出率 (占收入 %)",
                    "accounts_receivable_days": "应收账款周转天数 (天)",
                    "inventory_days": "存货周转天数 (天)",
                    "accounts_payable_days": "应付账款周转天数 (天)",
                    "other_current_assets_to_revenue_ratio": "其他流动资产率 (占收入 %)",
                    "other_current_liabilities_to_revenue_ratio": "其他流动负债率 (占收入 %)",
                    "nwc_to_revenue_ratio": "净营运资本率 (占收入 %)",
                    "last_historical_nwc": "上一历史期净营运资本 (元)",
                    "effective_tax_rate": "有效税率 (%)",
                    "historical_revenue_cagr": "历史收入复合年增长率 (%)"
                }
                df_ratios_summary = pd.DataFrame(historical_ratios_summary_data)
                
                if 'metric_name' in df_ratios_summary.columns:
                    df_ratios_summary['指标中文名称'] = df_ratios_summary['metric_name'].map(ratio_display_names_map).fillna(df_ratios_summary['metric_name'])
                else:
                    df_ratios_summary['指标中文名称'] = "未知指标"

                if 'value' in df_ratios_summary.columns:
                    df_ratios_summary['value'] = pd.to_numeric(df_ratios_summary['value'], errors='coerce')
                    for index, row in df_ratios_summary.iterrows():
                        metric_name_for_format_check = row.get('指标中文名称', row.get('metric_name', '')) 
                        value = row.get('value')
                        if pd.notna(value):
                            if '率' in metric_name_for_format_check or 'CAGR' in metric_name_for_format_check or \
                               'ratio' in metric_name_for_format_check.lower() or 'margin' in metric_name_for_format_check.lower():
                                if '天数' not in metric_name_for_format_check and 'days' not in metric_name_for_format_check.lower() and '元' not in metric_name_for_format_check:
                                    df_ratios_summary.loc[index, 'value_display'] = f"{value*100:.2f}%"
                                elif '天数' in metric_name_for_format_check or 'days' in metric_name_for_format_check.lower():
                                    df_ratios_summary.loc[index, 'value_display'] = f"{value:.1f}"
                                else:
                                    df_ratios_summary.loc[index, 'value_display'] = f"{value:,.0f}"
                            elif '天数' in metric_name_for_format_check or 'days' in metric_name_for_format_check.lower():
                                 df_ratios_summary.loc[index, 'value_display'] = f"{value:.1f}"
                            elif '元' in metric_name_for_format_check:
                                df_ratios_summary.loc[index, 'value_display'] = f"{value:,.0f}"
                            else:
                                df_ratios_summary.loc[index, 'value_display'] = f"{value:.2f}"
                        else:
                            df_ratios_summary.loc[index, 'value_display'] = "-"
                    
                    df_ratios_display = df_ratios_summary.rename(columns={'指标中文名称':'指标名称', 'value_display':'中位数/历史值'})
                    if '指标名称' in df_ratios_display.columns and '中位数/历史值' in df_ratios_display.columns:
                        st.dataframe(df_ratios_display[['指标名称', '中位数/历史值']].set_index('指标名称'), use_container_width=True)
                    elif 'metric_name' in df_ratios_summary.columns and 'value_display' in df_ratios_summary.columns:
                        df_ratios_fallback_display = df_ratios_summary.rename(columns={'metric_name':'指标名称', 'value_display':'中位数/历史值'})
                        st.dataframe(df_ratios_fallback_display[['指标名称', '中位数/历史值']].set_index('指标名称'), use_container_width=True)
                    elif 'metric_name' in df_ratios_summary.columns and 'value' in df_ratios_summary.columns: 
                        st.dataframe(df_ratios_summary[['metric_name', 'value']].set_index('metric_name'), use_container_width=True)
                    else: 
                         st.dataframe(df_ratios_summary, use_container_width=True)
                else:
                    if '指标中文名称' in df_ratios_summary.columns:
                        st.dataframe(df_ratios_summary.set_index('指标中文名称'), use_container_width=True)
                    elif 'metric_name' in df_ratios_summary.columns:
                         st.dataframe(df_ratios_summary.set_index('metric_name'), use_container_width=True)
                    else:
                         st.dataframe(df_ratios_summary, use_container_width=True)
            except Exception as e_rs:
                st.error(f"渲染历史财务比率时出错: {e_rs}")
        else:
            st.caption("未找到历史财务比率数据。")

        st.subheader("未来财务预测")
        detailed_forecast_table_data = valuation_results.get("detailed_forecast_table")
        if detailed_forecast_table_data:
            try:
                df_forecast = pd.DataFrame(detailed_forecast_table_data)
                if not df_forecast.empty:
                    forecast_column_names_map = {
                        "year": "年份 (Year)", "revenue": "营业收入 (Revenue)", "revenue_growth_rate": "收入增长率 (%)",
                        "cogs": "营业成本 (COGS)", "gross_profit": "毛利润 (Gross Profit)", 
                        "sga_expenses": "销售及管理费用 (SG&A)", "rd_expenses": "研发费用 (R&D)",
                        "sga_rd_expenses": "销售管理及研发费用 (SG&A+R&D)", "operating_expenses": "营业费用 (OpEx)",
                        "ebit": "息税前利润 (EBIT)", "interest_expense": "利息费用 (Interest Exp.)", "ebt": "税前利润 (EBT)",
                        "taxes": "所得税 (Taxes)", "net_income_after_tax": "税后净利润 (Net Income)", "net_income": "净利润 (Net Income)",
                        "nopat": "税后净营业利润 (NOPAT)", "depreciation_amortization": "折旧与摊销 (D&A)", "d_a": "折旧与摊销 (D&A)",
                        "capex": "资本性支出 (CapEx)", "accounts_receivable": "应收账款 (AR)", "inventories": "存货 (Inventories)",
                        "accounts_payable": "应付账款 (AP)", "other_current_assets": "其他流动资产 (OCA)", 
                        "other_current_liabilities": "其他流动负债 (OCL)", "nwc": "净营运资本 (NWC)",
                        "change_in_nwc": "净营运资本变动 (ΔNWC)", "delta_nwc": "净营运资本变动 (ΔNWC)",
                        "ebitda": "息税折旧摊销前利润 (EBITDA)", "ufcf": "无杠杆自由现金流 (UFCF)", "pv_ufcf": "UFCF现值 (PV of UFCF)"
                    }
                    if 'year' in df_forecast.columns:
                        df_forecast_display = df_forecast.set_index('year')
                    else:
                        df_forecast_display = df_forecast
                    format_dict_fc = {}
                    for col_original in df_forecast_display.columns:
                        if col_original == 'revenue_growth_rate':
                            format_dict_fc[col_original] = "{:.2%}"
                        elif df_forecast_display[col_original].dtype in ['float', 'int', 'float64', 'int64']:
                            format_dict_fc[col_original] = "{:,.0f}"
                    df_forecast_display_renamed = df_forecast_display.rename(columns=forecast_column_names_map)
                    final_format_dict_fc = {}
                    for original_col, new_col_name in forecast_column_names_map.items():
                        if original_col in format_dict_fc:
                            final_format_dict_fc[new_col_name] = format_dict_fc[original_col]
                    for col_renamed in df_forecast_display_renamed.columns:
                        if col_renamed not in final_format_dict_fc and df_forecast_display_renamed[col_renamed].dtype in ['float', 'int', 'float64', 'int64']:
                            original_col_for_renamed = next((k for k, v in forecast_column_names_map.items() if v == col_renamed), None)
                            if original_col_for_renamed and original_col_for_renamed in format_dict_fc:
                                final_format_dict_fc[col_renamed] = format_dict_fc[original_col_for_renamed]
                            elif col_renamed == forecast_column_names_map.get("revenue_growth_rate"):
                                 final_format_dict_fc[col_renamed] = "{:.2%}"
                            else:
                                final_format_dict_fc[col_renamed] = "{:,.0f}"
                    st.dataframe(df_forecast_display_renamed.style.format(final_format_dict_fc, na_rep='-'), use_container_width=True)
                else:
                    st.caption("详细预测数据为空。")
            except Exception as e_fc:
                st.error(f"渲染详细预测数据时出错: {e_fc}")
                st.error(traceback.format_exc())
        else:
            st.caption("未找到详细预测数据。")

# --- 函数：渲染LLM总结区块 ---
def render_llm_summary_section(llm_summary, llm_requested):
    # Only display LLM section if toggle is on (llm_requested is True) and summary is available or not
    if llm_requested: # Check if LLM was requested by the user via toggle
        st.subheader("🤖 LLM 分析与投资建议摘要")
        st.caption("请结合以下分析判断投资价值。") 
        if llm_summary:
            st.markdown(llm_summary, unsafe_allow_html=True)
        else:
            # If LLM was requested but summary is None/empty, it means it failed or was not returned
            st.warning("未能获取 LLM 分析结果。")
    # If llm_requested is False, we don't show this section at all, 
    # or optionally show a message that it was not enabled.
    # For now, let's not show anything if not requested.
    # else:
    #     st.info("LLM 分析未启用。")


# --- 函数：渲染估值结果 ---
def render_valuation_results(payload_filtered, current_ts_code, base_assumptions, selected_output_metric_keys_from_ui):
    # st.header("估值结果")
    st.info(f"正在为 {current_ts_code} 请求估值...")

    try:
        with st.spinner('正在调用后端 API 并进行计算...'):
            response = requests.post(API_ENDPOINT, json=payload_filtered, timeout=180) 
        
        if response.status_code == 200:
            results = response.json()
            
            if results.get("error"):
                st.error(f"估值计算出错: {results['error']}")
            else:
                stock_info = results.get("stock_info", {})
                valuation_results = results.get("valuation_results", {})
                dcf_details = valuation_results.get("dcf_forecast_details", {})
                llm_summary = valuation_results.get("llm_analysis_summary") 
                data_warnings = valuation_results.get("data_warnings") 

                base_wacc_used = dcf_details.get('wacc_used')
                base_exit_multiple_used = dcf_details.get('exit_multiple_used')
                base_pgr_used = dcf_details.get('perpetual_growth_rate_used')

                # 调用新的函数渲染数据警告
                render_data_warnings(data_warnings)

                # --- Display Special Industry Warning ---
                special_industry_warning_text = valuation_results.get("special_industry_warning")
                # 调用新的函数渲染特殊行业警告
                render_special_industry_warning(special_industry_warning_text)

                # 调用新的函数渲染基本信息
                render_basic_info_section(stock_info, valuation_results)
                
                st.markdown("---") # 在基本信息和估值结果之间添加横线

                # 调用新的函数渲染估值结果摘要
                render_valuation_summary_section(dcf_details, valuation_results)
                
                st.markdown("---") # Keep the separator before the expander

                # Removed "查看 DCF 详细构成" expander
                # st.expander("查看 DCF 详细构成"):
                #     col1_detail, col2_detail = st.columns(2) 
                #     col1_detail.metric("企业价值 (EV)", f"{dcf_details.get('enterprise_value', 'N/A') / 1e8:.2f} 亿" if dcf_details.get('enterprise_value') is not None else "N/A")
                #     col1_detail.metric("预测期 UFCF 现值", f"{dcf_details.get('pv_forecast_ufcf', 'N/A') / 1e8:.2f} 亿" if dcf_details.get('pv_forecast_ufcf') is not None else "N/A")
                #     col1_detail.metric("终值 (TV)", f"{dcf_details.get('terminal_value', 'N/A') / 1e8:.2f} 亿" if dcf_details.get('terminal_value') is not None else "N/A")
                #     col2_detail.metric("股权价值", f"{dcf_details.get('equity_value', 'N/A') / 1e8:.2f} 亿" if dcf_details.get('equity_value') is not None else "N/A")
                #     col2_detail.metric("终值现值 (PV of TV)", f"{dcf_details.get('pv_terminal_value', 'N/A') / 1e8:.2f} 亿" if dcf_details.get('pv_terminal_value') is not None else "N/A")
                #     col2_detail.metric("净债务", f"{dcf_details.get('net_debt', 'N/A') / 1e8:.2f} 亿" if dcf_details.get('net_debt') is not None else "N/A")
                #     st.caption(f"终值计算方法: {dcf_details.get('terminal_value_method_used', 'N/A')}")
                #     if dcf_details.get('terminal_value_method_used') == 'exit_multiple':
                #         st.caption(f"退出乘数: {dcf_details.get('exit_multiple_used', 'N/A')}")
                #     elif dcf_details.get('terminal_value_method_used') == 'perpetual_growth':
                #         st.caption(f"永续增长率: {dcf_details.get('perpetual_growth_rate_used', 'N/A') * 100:.2f}%")
                
                sensitivity_data = valuation_results.get("sensitivity_analysis_result")
                sensitivity_enabled_for_this_run = payload_filtered.get("sensitivity_analysis") is not None
                
                if sensitivity_enabled_for_this_run: # Check if sensitivity analysis was enabled for this run
                    render_sensitivity_analysis_section(
                        sensitivity_data, 
                        base_assumptions, # Pass the original base_assumptions from the payload
                        selected_output_metric_keys_from_ui, 
                        base_wacc_used,
                        base_exit_multiple_used, # Pass the actual used exit multiple
                        base_pgr_used # Pass the actual used pgr
                    )

                # 调用新的函数渲染高级分析区块
                render_advanced_analysis_section(valuation_results)

                # 调用新的函数渲染LLM总结区块
                llm_requested_in_payload = payload_filtered.get("request_llm_summary", False) # Get the actual request status
                render_llm_summary_section(llm_summary, llm_requested_in_payload)

        else:
             st.error(f"API 请求失败，状态码: {response.status_code}")
             try:
                 error_detail = response.json().get("detail", response.text)
                 st.error(f"错误详情: {error_detail}")
             except json.JSONDecodeError:
                 st.error(f"无法解析错误响应: {response.text}")
    except requests.exceptions.Timeout:
        st.error("请求后端 API 超时，请稍后再试或增加超时时间。")
    except requests.exceptions.RequestException as e:
        st.error(f"请求后端 API 时出错: {e}")
    except Exception as e:
        st.error(f"处理估值结果时发生未知错误: {e}")
        st.error(traceback.format_exc())

# --- 函数：渲染侧边栏输入 ---
def render_sidebar_inputs():
    with st.sidebar:
        st.header("DCF估值参数") # Changed header for clarity
        ts_code_val = st.text_input("股票代码 (例如 600519.SH):", st.session_state.get("ts_code_input", "600519.SH"), key="ts_code_input") # Use session state for persistence
        valuation_date_val = st.date_input("估值基准日期:", value=pd.to_datetime(st.session_state.get("valuation_date_input", pd.to_datetime("today"))), key="valuation_date_input")
        st.subheader("核心假设")
        forecast_years_val = st.slider("预测期年数:", min_value=3, max_value=15, value=st.session_state.get("forecast_years_slider", 5), key="forecast_years_slider")
        with st.expander("收入预测假设", expanded=True):
            cagr_decay_rate_val = st.number_input("历史 CAGR 年衰减率 (0-1):", min_value=0.0, max_value=1.0, value=st.session_state.get("cagr_decay", 0.1), step=0.01, format="%.2f", help="用于基于历史CAGR预测未来收入时的年衰减比例。0表示不衰减，1表示第一年后增长为0。", key="cagr_decay")
        with st.expander("利润率与费用预测假设"):
            op_margin_forecast_mode_val = st.selectbox("营业利润率模式:", options=['historical_median', 'transition_to_target'], index=['historical_median', 'transition_to_target'].index(st.session_state.get("op_margin_mode", 'historical_median')), key="op_margin_mode", help="选择使用历史中位数，还是逐渐过渡到目标值。")
            target_operating_margin_val = st.number_input("目标营业利润率:", value=st.session_state.get("target_op_margin", 0.15), step=0.01, format="%.3f", key="target_op_margin", disabled=(op_margin_forecast_mode_val != 'transition_to_target')) if op_margin_forecast_mode_val == 'transition_to_target' else None
            op_margin_transition_years_val = st.number_input("利润率过渡年数:", min_value=1, value=st.session_state.get("op_margin_trans_years", forecast_years_val), step=1, key="op_margin_trans_years", disabled=(op_margin_forecast_mode_val != 'transition_to_target' or target_operating_margin_val is None)) if op_margin_forecast_mode_val == 'transition_to_target' else None
            sga_rd_ratio_forecast_mode_val = st.selectbox("SGA&RD 占收入比模式:", options=['historical_median', 'transition_to_target'], index=['historical_median', 'transition_to_target'].index(st.session_state.get("sga_rd_mode", 'historical_median')), key="sga_rd_mode")
            target_sga_rd_to_revenue_ratio_val = st.number_input("目标 SGA&RD 占收入比:", value=st.session_state.get("target_sga_rd_ratio", 0.20), step=0.01, format="%.3f", key="target_sga_rd_ratio", disabled=(sga_rd_ratio_forecast_mode_val != 'transition_to_target')) if sga_rd_ratio_forecast_mode_val == 'transition_to_target' else None
            sga_rd_transition_years_val = st.number_input("SGA&RD 比率过渡年数:", min_value=1, value=st.session_state.get("sga_rd_trans_years", forecast_years_val), step=1, key="sga_rd_trans_years", disabled=(sga_rd_ratio_forecast_mode_val != 'transition_to_target' or target_sga_rd_to_revenue_ratio_val is None)) if sga_rd_ratio_forecast_mode_val == 'transition_to_target' else None
        with st.expander("资产与投资预测假设"):
            da_ratio_forecast_mode_val = st.selectbox("D&A 占收入比模式:", options=['historical_median', 'transition_to_target'], index=['historical_median', 'transition_to_target'].index(st.session_state.get("da_mode", 'historical_median')), key="da_mode")
            target_da_to_revenue_ratio_val = st.number_input("目标 D&A 占收入比:", value=st.session_state.get("target_da_ratio", 0.05), step=0.005, format="%.3f", key="target_da_ratio", disabled=(da_ratio_forecast_mode_val != 'transition_to_target')) if da_ratio_forecast_mode_val == 'transition_to_target' else None
            da_ratio_transition_years_val = st.number_input("D&A 比率过渡年数:", min_value=1, value=st.session_state.get("da_trans_years", forecast_years_val), step=1, key="da_trans_years", disabled=(da_ratio_forecast_mode_val != 'transition_to_target' or target_da_to_revenue_ratio_val is None)) if da_ratio_forecast_mode_val == 'transition_to_target' else None
            capex_ratio_forecast_mode_val = st.selectbox("Capex 占收入比模式:", options=['historical_median', 'transition_to_target'], index=['historical_median', 'transition_to_target'].index(st.session_state.get("capex_mode", 'historical_median')), key="capex_mode")
            target_capex_to_revenue_ratio_val = st.number_input("目标 Capex 占收入比:", value=st.session_state.get("target_capex_ratio", 0.07), step=0.005, format="%.3f", key="target_capex_ratio", disabled=(capex_ratio_forecast_mode_val != 'transition_to_target')) if capex_ratio_forecast_mode_val == 'transition_to_target' else None
            capex_ratio_transition_years_val = st.number_input("Capex 比率过渡年数:", min_value=1, value=st.session_state.get("capex_trans_years", forecast_years_val), step=1, key="capex_trans_years", disabled=(capex_ratio_forecast_mode_val != 'transition_to_target' or target_capex_to_revenue_ratio_val is None)) if capex_ratio_forecast_mode_val == 'transition_to_target' else None
        with st.expander("营运资本预测假设"):
            nwc_days_forecast_mode_val = st.selectbox("核心 NWC 周转天数模式:", options=['historical_median', 'transition_to_target'], index=['historical_median', 'transition_to_target'].index(st.session_state.get("nwc_days_mode", 'historical_median')), key="nwc_days_mode")
            target_accounts_receivable_days_val = st.number_input("目标 DSO:", value=st.session_state.get("target_ar_days", 30.0), step=1.0, format="%.1f", key="target_ar_days", disabled=(nwc_days_forecast_mode_val != 'transition_to_target')) if nwc_days_forecast_mode_val == 'transition_to_target' else None
            target_inventory_days_val = st.number_input("目标 DIO:", value=st.session_state.get("target_inv_days", 60.0), step=1.0, format="%.1f", key="target_inv_days", disabled=(nwc_days_forecast_mode_val != 'transition_to_target')) if nwc_days_forecast_mode_val == 'transition_to_target' else None
            target_accounts_payable_days_val = st.number_input("目标 DPO:", value=st.session_state.get("target_ap_days", 45.0), step=1.0, format="%.1f", key="target_ap_days", disabled=(nwc_days_forecast_mode_val != 'transition_to_target')) if nwc_days_forecast_mode_val == 'transition_to_target' else None
            nwc_days_transition_years_val = st.number_input("NWC 天数过渡年数:", min_value=1, value=st.session_state.get("nwc_days_trans_years", forecast_years_val), step=1, key="nwc_days_trans_years", disabled=(nwc_days_forecast_mode_val != 'transition_to_target' or not any([target_accounts_receivable_days_val, target_inventory_days_val, target_accounts_payable_days_val]))) if nwc_days_forecast_mode_val == 'transition_to_target' else None
            other_nwc_ratio_forecast_mode_val = st.selectbox("其他 NWC 占收入比模式:", options=['historical_median', 'transition_to_target'], index=['historical_median', 'transition_to_target'].index(st.session_state.get("other_nwc_mode", 'historical_median')), key="other_nwc_mode")
            target_other_current_assets_to_revenue_ratio_val = st.number_input("目标其他流动资产/收入:", value=st.session_state.get("target_oca_ratio", 0.05), step=0.005, format="%.3f", key="target_oca_ratio", disabled=(other_nwc_ratio_forecast_mode_val != 'transition_to_target')) if other_nwc_ratio_forecast_mode_val == 'transition_to_target' else None
            target_other_current_liabilities_to_revenue_ratio_val = st.number_input("目标其他流动负债/收入:", value=st.session_state.get("target_ocl_ratio", 0.03), step=0.005, format="%.3f", key="target_ocl_ratio", disabled=(other_nwc_ratio_forecast_mode_val != 'transition_to_target')) if other_nwc_ratio_forecast_mode_val == 'transition_to_target' else None
            other_nwc_ratio_transition_years_val = st.number_input("其他 NWC 比率过渡年数:", min_value=1, value=st.session_state.get("other_nwc_trans_years", forecast_years_val), step=1, key="other_nwc_trans_years", disabled=(other_nwc_ratio_forecast_mode_val != 'transition_to_target' or not any([target_other_current_assets_to_revenue_ratio_val, target_other_current_liabilities_to_revenue_ratio_val]))) if other_nwc_ratio_forecast_mode_val == 'transition_to_target' else None
        with st.expander("税率假设"):
            target_effective_tax_rate_val = st.number_input("目标有效所得税率:", min_value=0.0, max_value=1.0, value=st.session_state.get("tax_rate", 0.25), step=0.01, format="%.2f", key="tax_rate")
        with st.expander("WACC 参数 (可选覆盖)"):
            wacc_weight_mode_ui_val = st.radio( "WACC 权重模式:", options=["使用目标债务比例", "使用最新市场价值计算权重"], index=["使用目标债务比例", "使用最新市场价值计算权重"].index(st.session_state.get("wacc_weight_mode_selector", "使用最新市场价值计算权重")), key="wacc_weight_mode_selector", help="选择使用预设的目标资本结构，还是基于最新的市值和负债动态计算资本结构权重。" )
            target_debt_ratio_disabled_val = (wacc_weight_mode_ui_val == "使用最新市场价值计算权重")
            target_debt_ratio_val = st.number_input( "目标债务比例 D/(D+E):", min_value=0.0, max_value=1.0, value=st.session_state.get("wacc_debt_ratio", 0.45), step=0.05, format="%.2f", help="仅在选择“使用目标债务比例”模式时有效。留空则使用后端默认值。", key="wacc_debt_ratio", disabled=target_debt_ratio_disabled_val )
            cost_of_debt_val = st.number_input("税前债务成本 (Rd):", min_value=0.0, value=st.session_state.get("wacc_cost_debt", 0.05), step=0.005, format="%.3f", help="留空则使用默认值", key="wacc_cost_debt")
            risk_free_rate_val = st.number_input("无风险利率 (Rf):", min_value=0.0, value=st.session_state.get("wacc_rf", 0.03), step=0.005, format="%.3f", help="留空则使用默认值", key="wacc_rf")
            beta_val = st.number_input("贝塔系数 (Beta):", value=st.session_state.get("wacc_beta", 1.0), step=0.1, format="%.2f", help="留空则使用数据库最新值或默认值", key="wacc_beta")
            market_risk_premium_val = st.number_input("市场风险溢价 (MRP):", min_value=0.0, value=st.session_state.get("wacc_mrp", 0.06), step=0.005, format="%.3f", help="留空则使用默认值", key="wacc_mrp")
        with st.expander("终值计算假设"):
            terminal_value_method_val = st.selectbox("终值计算方法:", options=['exit_multiple', 'perpetual_growth'], index=['exit_multiple', 'perpetual_growth'].index(st.session_state.get("tv_method", 'exit_multiple')), key="tv_method")
            exit_multiple_val = st.number_input("退出乘数 (EBITDA):", min_value=0.1, value=st.session_state.get("tv_exit_multiple", 7.0), step=0.5, format="%.1f", key="tv_exit_multiple", disabled=(terminal_value_method_val != 'exit_multiple'), on_change=update_sensitivity_ui_elements) if terminal_value_method_val == 'exit_multiple' else None
            perpetual_growth_rate_val = st.number_input("永续增长率:", min_value=0.0, max_value=0.05, value=st.session_state.get("tv_pg_rate", 0.025), step=0.001, format="%.3f", key="tv_pg_rate", disabled=(terminal_value_method_val != 'perpetual_growth'), on_change=update_sensitivity_ui_elements) if terminal_value_method_val == 'perpetual_growth' else None
        st.divider()
        st.subheader("敏感性分析")
        enable_sensitivity_val = st.checkbox("启用敏感性分析", value=st.session_state.get("enable_sensitivity_cb", True), key="enable_sensitivity_cb")
        if enable_sensitivity_val:
            st.markdown("**行轴设置**")
            row_param_display_val = st.selectbox( "选择行轴参数:", options=list(supported_axis_params.keys()), index=list(supported_axis_params.keys()).index(st.session_state.get("sens_row_param", "WACC")), key="sens_row_param", on_change=update_sensitivity_ui_elements )
            st.number_input("步长:", value=st.session_state.get("sens_row_step"), step=0.001 if supported_axis_params.get(row_param_display_val) != "exit_multiple" else 0.1, format="%.4f" if supported_axis_params.get(row_param_display_val) != "exit_multiple" else "%.1f", key="sens_row_step", on_change=update_sensitivity_ui_elements)
            st.slider("点数 (奇数):", min_value=3, max_value=9, value=st.session_state.get("sens_row_points", 5), step=2, key="sens_row_points", on_change=update_sensitivity_ui_elements)
            if st.session_state.sens_row_param == "WACC":
                st.caption("提示: WACC轴的中心将基于实际计算的WACC值，步长和点数将用于后端重新生成分析轴。")
            st.number_input(f"中心值 ({row_param_display_val}):", value=float(st.session_state.get('sens_row_center_value', 0.0)), key="sens_row_center_display", disabled=True, format="%.4f" if supported_axis_params.get(row_param_display_val) == "wacc" or supported_axis_params.get(row_param_display_val) == "perpetual_growth_rate" else "%.1f")
            st.text_area( "行轴值列表 (逗号分隔):", value=st.session_state.get('sens_row_values_str', ""), key="sens_row_values_input" )
            st.markdown("**列轴设置**")
            available_col_params_options_val = [k for k, v in supported_axis_params.items() if v != supported_axis_params.get(row_param_display_val)]
            current_col_display_val = st.session_state.get("sens_col_param", available_col_params_options_val[0] if available_col_params_options_val else list(supported_axis_params.keys())[0])
            col_default_index_val = available_col_params_options_val.index(current_col_display_val) if current_col_display_val in available_col_params_options_val else 0
            col_param_display_val = st.selectbox( "选择列轴参数:", options=available_col_params_options_val, index=col_default_index_val, key="sens_col_param", on_change=update_sensitivity_ui_elements )
            st.number_input("步长:", value=st.session_state.get("sens_col_step"), step=0.001 if supported_axis_params.get(col_param_display_val) != "exit_multiple" else 0.1, format="%.4f" if supported_axis_params.get(col_param_display_val) != "exit_multiple" else "%.1f", key="sens_col_step", on_change=update_sensitivity_ui_elements)
            st.slider("点数 (奇数):", min_value=3, max_value=9, value=st.session_state.get("sens_col_points", 5), step=2, key="sens_col_points", on_change=update_sensitivity_ui_elements)
            if st.session_state.sens_col_param == "WACC":
                st.caption("提示: WACC轴的中心将基于实际计算的WACC值，步长和点数将用于后端重新生成分析轴。")
            st.number_input(f"中心值 ({col_param_display_val}):", value=float(st.session_state.get('sens_col_center_value', 0.0)), key="sens_col_center_display", disabled=True, format="%.4f" if supported_axis_params.get(col_param_display_val) == "wacc" or supported_axis_params.get(col_param_display_val) == "perpetual_growth_rate" else "%.1f")
            st.text_area( "列轴值列表 (逗号分隔):", value=st.session_state.get('sens_col_values_str', ""), key="sens_col_values_input" )
            st.markdown("**输出指标**")
            st.multiselect( "选择要显示的敏感性表格指标:", options=list(supported_output_metrics.keys()), default=st.session_state.get("sens_output_metrics_select", list(supported_output_metrics.keys())), key="sens_output_metrics_select" )
            if 'sensitivity_initialized' in st.session_state and st.session_state.sensitivity_initialized:
                 if 'sens_ui_initialized_run' not in st.session_state:
                     update_sensitivity_ui_elements()
                     st.session_state.sens_ui_initialized_run = True
        st.divider()
        st.subheader("其他选项")
        llm_toggle_value_val = st.checkbox("启用 LLM 分析总结", value=st.session_state.get("llm_toggle", False), key="llm_toggle", help="控制是否请求并显示 LLM 生成的分析摘要。")
        
        if llm_toggle_value_val:
            st.markdown("---")
            st.subheader("LLM 配置")
            llm_provider_options = ["DeepSeek", "自定义 (OpenAI 兼容)"]
            default_provider_from_env = os.getenv("LLM_PROVIDER", "deepseek").lower()
            default_provider_index = 0 
            if default_provider_from_env == "custom_openai":
                 # This needs a more robust mapping if .env stores "custom_openai"
                 # For now, assume UI default is DeepSeek unless explicitly set in session_state
                 default_provider_index = llm_provider_options.index("自定义 (OpenAI 兼容)") if "自定义 (OpenAI 兼容)" in llm_provider_options else 0
            
            llm_provider_select_val = st.selectbox(
                "选择 LLM 提供商:", 
                options=llm_provider_options, 
                index=st.session_state.get("llm_provider_select_index", default_provider_index), # Use session state or calculated default
                key="llm_provider_select"
            )
            st.session_state.llm_provider_select_index = llm_provider_options.index(llm_provider_select_val)


            deepseek_model_id_val = None
            custom_llm_api_base_url_val = None
            custom_llm_model_id_val = None

            if llm_provider_select_val == "DeepSeek":
                deepseek_model_id_val = st.text_input(
                    "DeepSeek 模型 ID (可选):", 
                    value=st.session_state.get("deepseek_model_id", os.getenv("DEEPSEEK_MODEL_NAME", "deepseek-chat")), 
                    key="deepseek_model_id",
                    help="留空则使用 .env 中的 DEEPSEEK_MODEL_NAME 或 deepseek-chat"
                )
            elif llm_provider_select_val == "自定义 (OpenAI 兼容)":
                custom_llm_api_base_url_val = st.text_input(
                    "自定义模型 API Base URL:", 
                    value=st.session_state.get("custom_base_url", os.getenv("CUSTOM_LLM_API_BASE_URL", "")), 
                    key="custom_base_url", 
                    help="例如: http://localhost:1234/v1"
                )
                custom_llm_model_id_val = st.text_input(
                    "自定义模型 ID:", 
                    value=st.session_state.get("custom_model_id", os.getenv("CUSTOM_LLM_MODEL_ID", "")), 
                    key="custom_model_id",
                    help="例如: my-custom-model"
                )
            
            llm_temperature_val = st.slider(
                "Temperature:", 
                min_value=0.0, max_value=2.0, 
                value=st.session_state.get("llm_temp", float(os.getenv("LLM_DEFAULT_TEMPERATURE", "0.7"))), 
                step=0.1, key="llm_temp"
            )
            llm_top_p_val = st.slider(
                "Top-P:", 
                min_value=0.0, max_value=1.0, 
                value=st.session_state.get("llm_top_p", float(os.getenv("LLM_DEFAULT_TOP_P", "0.9"))), 
                step=0.05, key="llm_top_p"
            )
            llm_max_tokens_val = st.number_input(
                "Max Tokens (最大完成长度):", 
                min_value=50, max_value=32000, 
                value=st.session_state.get("llm_max_tokens", int(os.getenv("LLM_DEFAULT_MAX_TOKENS", "4000"))), 
                step=100, key="llm_max_tokens",
                help="LLM 生成内容的最大 token 数。"
            )
        
        st.divider()
        st.caption("未来功能：情景分析")
        st.info("未来版本将支持对关键假设进行情景分析。")
    
        # --- 股票筛选器侧边栏 ---
        st.sidebar.divider() 
        st.sidebar.header("股票筛选器参数") 

        # Data Update Section for Screener
        st.sidebar.subheader("数据管理 (筛选器)") 
        if st.sidebar.button("更新股票基础数据", key="update_stock_basic_main"):
            if pro:
                with st.spinner("正在更新股票基础数据 (筛选器)... 请稍候..."):
                    load_stock_basic(pro, force_update=True)
                st.sidebar.success("股票基础数据更新完成！(筛选器)") 
                update_screener_data_status() 
                st.rerun()
            else:
                st.sidebar.error("Tushare API 未初始化 (筛选器)。") 

        selected_trade_date_input_val = st.sidebar.text_input(
            "行情数据交易日 (YYYYMMDD)", 
            value=st.session_state.get('latest_trade_date', datetime.now().strftime('%Y%m%d')), 
            key="screener_trade_date_input",
            help="输入您想获取行情数据的交易日，默认为最新可获取交易日。"
        )

        if st.sidebar.button("更新每日行情指标", key="update_daily_basic_main"):
            if pro and selected_trade_date_input_val:
                try:
                    datetime.strptime(selected_trade_date_input_val, '%Y%m%d')
                    with st.spinner(f"正在更新交易日 {selected_trade_date_input_val} 的每日行情指标 (筛选器)... 请稍候..."):
                        load_daily_basic(pro, selected_trade_date_input_val, force_update=True)
                    st.session_state.latest_trade_date = selected_trade_date_input_val
                    st.sidebar.success(f"交易日 {selected_trade_date_input_val} 的每日行情指标更新完成！(筛选器)") 
                    update_screener_data_status()
                    st.rerun()
                except ValueError:
                    st.sidebar.error("日期格式无效，请输入 YYYYMMDD 格式。(筛选器)") 
            elif not pro:
                st.sidebar.error("Tushare API 未初始化。(筛选器)") 
            else:
                st.sidebar.error("请输入有效的交易日期。(筛选器)") 
        
        st.sidebar.caption(f"基础数据最后更新: {st.session_state.stock_basic_last_update}") 
        st.sidebar.caption(f"行情数据日期: {st.session_state.daily_basic_data_date}") 
        st.sidebar.caption(f"行情缓存最后更新: {st.session_state.daily_basic_last_update}") 
        st.sidebar.divider() 

        # Filter Criteria for Screener
        st.sidebar.subheader("筛选指标") 
        pe_min_val = st.sidebar.number_input("最低PE (市盈率)", min_value=0.0, value=st.session_state.get("screener_pe_min", 0.1), step=0.1, format="%.2f", key="screener_pe_min")
        pe_max_val = st.sidebar.number_input("最高PE (市盈率)", min_value=0.0, value=st.session_state.get("screener_pe_max", 30.0), step=1.0, format="%.2f", key="screener_pe_max")

        pb_min_val = st.sidebar.number_input("最低PB (市净率)", min_value=0.0, value=st.session_state.get("screener_pb_min", 0.1), step=0.1, format="%.2f", key="screener_pb_min")
        pb_max_val = st.sidebar.number_input("最高PB (市净率)", min_value=0.0, value=st.session_state.get("screener_pb_max", 3.0), step=0.1, format="%.2f", key="screener_pb_max")

        market_cap_min_billion_val = st.sidebar.number_input("最低市值 (亿元)", min_value=0.0, value=st.session_state.get("screener_mcap_min", 50.0), step=10.0, format="%.2f", key="screener_mcap_min")
        market_cap_max_billion_val = st.sidebar.number_input("最高市值 (亿元)", min_value=0.0, value=st.session_state.get("screener_mcap_max", 10000.0), step=100.0, format="%.2f", key="screener_mcap_max")

        # "开始筛选" 按钮的逻辑将在主程序区处理，这里只收集参数
        # if st.button("开始筛选", type="primary", key="filter_stocks_main"):
            # This button will now be in the screener tab, its action will use these sidebar values.
            # The actual filtering logic will be triggered from the main application body within the screener tab.
            # st.session_state.screener_filter_button_clicked = True # Flag that button was clicked

    returned_params = {
        "ts_code": ts_code_val,
        "valuation_date": valuation_date_val,
        "forecast_years": forecast_years_val,
        "cagr_decay_rate": cagr_decay_rate_val,
        "op_margin_forecast_mode": op_margin_forecast_mode_val,
        "target_operating_margin": target_operating_margin_val,
        "op_margin_transition_years": op_margin_transition_years_val,
        "sga_rd_ratio_forecast_mode": sga_rd_ratio_forecast_mode_val,
        "target_sga_rd_to_revenue_ratio": target_sga_rd_to_revenue_ratio_val,
        "sga_rd_transition_years": sga_rd_transition_years_val,
        "da_ratio_forecast_mode": da_ratio_forecast_mode_val,
        "target_da_to_revenue_ratio": target_da_to_revenue_ratio_val,
        "da_ratio_transition_years": da_ratio_transition_years_val,
        "capex_ratio_forecast_mode": capex_ratio_forecast_mode_val,
        "target_capex_to_revenue_ratio": target_capex_to_revenue_ratio_val,
        "capex_ratio_transition_years": capex_ratio_transition_years_val,
        "nwc_days_forecast_mode": nwc_days_forecast_mode_val,
        "target_accounts_receivable_days": target_accounts_receivable_days_val,
        "target_inventory_days": target_inventory_days_val,
        "target_accounts_payable_days": target_accounts_payable_days_val,
        "nwc_days_transition_years": nwc_days_transition_years_val,
        "other_nwc_ratio_forecast_mode": other_nwc_ratio_forecast_mode_val,
        "target_other_current_assets_to_revenue_ratio": target_other_current_assets_to_revenue_ratio_val,
        "target_other_current_liabilities_to_revenue_ratio": target_other_current_liabilities_to_revenue_ratio_val,
        "other_nwc_ratio_transition_years": other_nwc_ratio_transition_years_val,
        "target_effective_tax_rate": target_effective_tax_rate_val,
        "wacc_weight_mode_ui": wacc_weight_mode_ui_val,
        "target_debt_ratio": target_debt_ratio_val,
        "target_debt_ratio_disabled": target_debt_ratio_disabled_val,
        "cost_of_debt": cost_of_debt_val,
        "risk_free_rate": risk_free_rate_val,
        "beta": beta_val,
        "market_risk_premium": market_risk_premium_val,
        "terminal_value_method": terminal_value_method_val,
        "exit_multiple": exit_multiple_val,
        "perpetual_growth_rate": perpetual_growth_rate_val,
        "enable_sensitivity": enable_sensitivity_val,
        "llm_toggle_value": llm_toggle_value_val,
        # Add new LLM config values from sidebar to be returned by render_sidebar_inputs
        "llm_provider_selected": st.session_state.get("llm_provider_select", "DeepSeek") if llm_toggle_value_val else None,
        "deepseek_model_id_input": st.session_state.get("deepseek_model_id") if llm_toggle_value_val and st.session_state.get("llm_provider_select") == "DeepSeek" else None,
        "custom_llm_api_base_url_input": st.session_state.get("custom_base_url") if llm_toggle_value_val and st.session_state.get("llm_provider_select") == "自定义 (OpenAI 兼容)" else None,
        "custom_llm_model_id_input": st.session_state.get("custom_model_id") if llm_toggle_value_val and st.session_state.get("llm_provider_select") == "自定义 (OpenAI 兼容)" else None,
        "llm_temperature_input": st.session_state.get("llm_temp", float(os.getenv("LLM_DEFAULT_TEMPERATURE", "0.7"))) if llm_toggle_value_val else None,
        "llm_top_p_input": st.session_state.get("llm_top_p", float(os.getenv("LLM_DEFAULT_TOP_P", "0.9"))) if llm_toggle_value_val else None,
        "llm_max_tokens_input": st.session_state.get("llm_max_tokens", int(os.getenv("LLM_DEFAULT_MAX_TOKENS", "4000"))) if llm_toggle_value_val else None,
        # Add screener inputs to the return dict
        "screener_pe_min": pe_min_val,
        "screener_pe_max": pe_max_val,
        "screener_pb_min": pb_min_val,
        "screener_pb_max": pb_max_val,
        "screener_market_cap_min_billion": market_cap_min_billion_val,
        "screener_market_cap_max_billion": market_cap_max_billion_val,
        "screener_selected_trade_date": selected_trade_date_input_val
    }
    # Ensure all keys exist in session state for persistence across reruns
    for key, value in returned_params.items():
        if key not in st.session_state: # Initialize if not present
            st.session_state[key] = value
        # For inputs that might be None initially but get a value (like from text_input)
        # and we want to preserve that user-entered value or the default.
        # This is mostly handled by setting `value=st.session_state.get(key, default_value)` in the widget itself.
    return returned_params

# --- 主程序逻辑 ---

# Handle pending ts_code update from screener button before rendering sidebar
if st.session_state.get('pending_ts_code_update'):
    st.session_state.ts_code_input = st.session_state.pending_ts_code_update
    del st.session_state.pending_ts_code_update # Clear after use

# 调用侧边栏渲染函数并获取输入值
sidebar_inputs = render_sidebar_inputs()

# --- 定义股票筛选器标签页渲染函数 (占位符) ---
def render_stock_screener_tab():
    st.header("股票筛选器")
    st.markdown("使用侧边栏设置筛选条件并管理数据，然后点击下方的“开始筛选”按钮。")

    if st.button("开始筛选", type="primary", key="filter_stocks_main_tab_button"):
        if pro and sidebar_inputs.get("screener_selected_trade_date"):
            with st.spinner("正在加载并合并数据进行筛选..."):
                current_trade_date_for_screener = st.session_state.get('screener_trade_date_input', st.session_state.latest_trade_date)
                st.session_state.screener_merged_data = get_merged_stock_data(
                    pro, 
                    current_trade_date_for_screener,
                    force_update_basic=False,
                    force_update_daily=False
                )
            
            if st.session_state.screener_merged_data is not None and not st.session_state.screener_merged_data.empty:
                df_to_filter = st.session_state.screener_merged_data.copy()
                conditions = (
                    (df_to_filter['pe'] >= sidebar_inputs["screener_pe_min"]) & (df_to_filter['pe'] <= sidebar_inputs["screener_pe_max"]) & (df_to_filter['pe'] > 0) &
                    (df_to_filter['pb'] >= sidebar_inputs["screener_pb_min"]) & (df_to_filter['pb'] <= sidebar_inputs["screener_pb_max"]) & (df_to_filter['pb'] > 0) &
                    (df_to_filter['market_cap_billion'] >= sidebar_inputs["screener_market_cap_min_billion"]) &
                    (df_to_filter['market_cap_billion'] <= sidebar_inputs["screener_market_cap_max_billion"])
                )
                st.session_state.screener_filtered_data = df_to_filter[conditions]
                st.success(f"筛选完成！找到 {len(st.session_state.screener_filtered_data)} 只符合条件的股票。")
                st.session_state.screener_filter_button_clicked = True
            else:
                st.error("未能加载或合并数据，无法进行筛选。请先尝试在侧边栏更新数据。")
                st.session_state.screener_filtered_data = pd.DataFrame() # Clear previous results
                st.session_state.screener_filter_button_clicked = True
        elif not pro:
            st.error("Tushare API 未初始化。")
        else:
            st.error("未能确定行情数据的交易日，请先在侧边栏更新每日行情指标。")
        
    if 'screener_filtered_data' in st.session_state and not st.session_state.screener_filtered_data.empty:
        st.subheader(f"筛选结果 ({len(st.session_state.screener_filtered_data)} 只股票)")
        
        # 定义要显示的列和格式化方式
        display_columns_config = {
            'ts_code': {"name": "代码", "format": None, "width": 1},
            'name': {"name": "名称", "format": None, "width": 1.3},
            'industry': {"name": "行业", "format": None, "width": 1.7},
            'close': {"name": "收盘价", "format": "{:.2f}", "width": 0.8},
            'pe': {"name": "PE", "format": "{:.2f}", "width": 0.7},
            'pb': {"name": "PB", "format": "{:.2f}", "width": 0.7},
            'turnover_rate': {"name": "换手率(%)", "format": "{:.2f}%", "width": 1},
            'market_cap_billion': {"name": "市值(亿)", "format": "{:,.1f}", "width": 1.2},
            'action': {"name": "操作", "format": None, "width": 1.1}
        }
        
        # 表头
        header_cols = st.columns([cfg["width"] for cfg in display_columns_config.values()])
        for i, col_key in enumerate(display_columns_config.keys()):
            header_cols[i].markdown(f"**{display_columns_config[col_key]['name']}**")

        st.divider()

        # 数据行
        for index, row_data in st.session_state.screener_filtered_data.iterrows():
            row_cols = st.columns([cfg["width"] for cfg in display_columns_config.values()])
            for i, col_key in enumerate(display_columns_config.keys()):
                if col_key == 'action':
                    button_key = f"valuate_{row_data['ts_code']}_{index}"
                    if row_cols[i].button("进行估值", key=button_key, help=f"对 {row_data['name']} ({row_data['ts_code']}) 进行DCF估值"):
                        st.session_state.pending_ts_code_update = row_data['ts_code']
                        # Store relevant metrics from screener for DCF tab display
                        st.session_state.screener_metrics_for_dcf = {
                            "ts_code": row_data.get('ts_code'),
                            "trade_date": row_data.get('trade_date'), # Make sure trade_date is in screener_filtered_data
                            "close": row_data.get('close'),
                            "pe": row_data.get('pe'), # Or pe_ttm, decide which one
                            "pb": row_data.get('pb'),
                            "dv_ratio": row_data.get('dv_ratio'), # dv_ratio is usually % value without % sign
                            "dv_ttm": row_data.get('dv_ttm') # dv_ttm is also % value without % sign
                        }
                        st.info(f"已将股票代码 {row_data['ts_code']} ({row_data['name']}) 的信息填充到DCF估值区，请切换到“DCF估值”标签页查看并开始计算。")
                        st.rerun() 
                else:
                    cell_value = row_data.get(col_key)
                    cell_format = display_columns_config[col_key]["format"]
                    if cell_value is not None and cell_format:
                        try:
                            row_cols[i].markdown(cell_format.format(cell_value))
                        except (ValueError, TypeError):
                            row_cols[i].markdown(str(cell_value))
                    else:
                        row_cols[i].markdown(str(cell_value) if cell_value is not None else "N/A")
            st.divider()

    elif st.session_state.get('screener_filter_button_clicked', False):
        st.info("没有找到符合当前筛选条件的股票。请尝试调整筛选范围或检查数据更新状态。")

# --- 创建标签页 ---
# active_tab_name = st.session_state.get('active_tab', "DCF估值") # Get active tab from session state
# tabs_list = ["DCF估值", "股票筛选器"]
# default_tab_index = tabs_list.index(active_tab_name) if active_tab_name in tabs_list else 0
# tab_valuation, tab_screener = st.tabs(tabs_list) # default_index not directly supported, manage content visibility instead

tab_valuation, tab_screener = st.tabs(["DCF估值", "股票筛选器"])

with tab_valuation:
    if st.button("🚀 开始估值计算", key="start_valuation_button"): 
        # State cleanup: If the ts_code for valuation is different from what screener provided, clear screener metrics
        current_valuation_ts_code = sidebar_inputs["ts_code"]
        screener_metrics_for_dcf = st.session_state.get('screener_metrics_for_dcf')
        if screener_metrics_for_dcf and screener_metrics_for_dcf.get('ts_code') != current_valuation_ts_code:
            del st.session_state.screener_metrics_for_dcf
            # Optionally, re-fetch or ensure valuation_results from API will be used fully
            # For now, just deleting is fine, render_basic_info_section will fallback to API data

        base_request_payload = {
            "ts_code": current_valuation_ts_code, # Use the potentially updated ts_code
            "valuation_date": sidebar_inputs["valuation_date"].strftime('%Y-%m-%d') if sidebar_inputs["valuation_date"] else None,
            "forecast_years": sidebar_inputs["forecast_years"],
            "cagr_decay_rate": sidebar_inputs["cagr_decay_rate"],
            "op_margin_forecast_mode": sidebar_inputs["op_margin_forecast_mode"],
            "target_operating_margin": sidebar_inputs["target_operating_margin"],
            "op_margin_transition_years": sidebar_inputs["op_margin_transition_years"],
            "sga_rd_ratio_forecast_mode": sidebar_inputs["sga_rd_ratio_forecast_mode"],
            "target_sga_rd_to_revenue_ratio": sidebar_inputs["target_sga_rd_to_revenue_ratio"],
            "sga_rd_transition_years": sidebar_inputs["sga_rd_transition_years"],
            "da_ratio_forecast_mode": sidebar_inputs["da_ratio_forecast_mode"], 
            "target_da_to_revenue_ratio": sidebar_inputs["target_da_to_revenue_ratio"],
            "da_ratio_transition_years": sidebar_inputs["da_ratio_transition_years"],
            "capex_ratio_forecast_mode": sidebar_inputs["capex_ratio_forecast_mode"], 
            "target_capex_to_revenue_ratio": sidebar_inputs["target_capex_to_revenue_ratio"],
            "capex_ratio_transition_years": sidebar_inputs["capex_ratio_transition_years"],
            "nwc_days_forecast_mode": sidebar_inputs["nwc_days_forecast_mode"],
            "target_accounts_receivable_days": sidebar_inputs["target_accounts_receivable_days"],
            "target_inventory_days": sidebar_inputs["target_inventory_days"],
            "target_accounts_payable_days": sidebar_inputs["target_accounts_payable_days"],
            "nwc_days_transition_years": sidebar_inputs["nwc_days_transition_years"],
            "other_nwc_ratio_forecast_mode": sidebar_inputs["other_nwc_ratio_forecast_mode"],
            "target_other_current_assets_to_revenue_ratio": sidebar_inputs["target_other_current_assets_to_revenue_ratio"],
            "target_other_current_liabilities_to_revenue_ratio": sidebar_inputs["target_other_current_liabilities_to_revenue_ratio"],
            "other_nwc_ratio_transition_years": sidebar_inputs["other_nwc_ratio_transition_years"],
            "target_effective_tax_rate": sidebar_inputs["target_effective_tax_rate"],
            "wacc_weight_mode": "market" if sidebar_inputs["wacc_weight_mode_ui"] == "使用最新市场价值计算权重" else "target", 
            "target_debt_ratio": sidebar_inputs["target_debt_ratio"] if not sidebar_inputs["target_debt_ratio_disabled"] else None, 
            "cost_of_debt": sidebar_inputs["cost_of_debt"],
            "risk_free_rate": sidebar_inputs["risk_free_rate"],
            "beta": sidebar_inputs["beta"],
            "market_risk_premium": sidebar_inputs["market_risk_premium"],
            "terminal_value_method": sidebar_inputs["terminal_value_method"],
            "exit_multiple": sidebar_inputs["exit_multiple"],
            "perpetual_growth_rate": sidebar_inputs["perpetual_growth_rate"],
            "request_llm_summary": sidebar_inputs["llm_toggle_value"],
            # Add new LLM params to payload
            "llm_provider": None, # Will be set below
            "llm_model_id": None, # Will be set below
            "llm_api_base_url": None, # Will be set below
            "llm_temperature": None, # Will be set below
            "llm_top_p": None, # Will be set below
            "llm_max_tokens": None, # Will be set below
        }

        if sidebar_inputs["llm_toggle_value"]:
            provider_ui_value = sidebar_inputs.get("llm_provider_selected")
            if provider_ui_value == "DeepSeek":
                base_request_payload["llm_provider"] = "deepseek"
                base_request_payload["llm_model_id"] = sidebar_inputs.get("deepseek_model_id_input") or os.getenv("DEEPSEEK_MODEL_NAME") # Fallback to env if input is empty
            elif provider_ui_value == "自定义 (OpenAI 兼容)":
                base_request_payload["llm_provider"] = "custom_openai"
                base_request_payload["llm_api_base_url"] = sidebar_inputs.get("custom_llm_api_base_url_input")
                base_request_payload["llm_model_id"] = sidebar_inputs.get("custom_llm_model_id_input")
            
            base_request_payload["llm_temperature"] = sidebar_inputs.get("llm_temperature_input")
            base_request_payload["llm_top_p"] = sidebar_inputs.get("llm_top_p_input")
            base_request_payload["llm_max_tokens"] = sidebar_inputs.get("llm_max_tokens_input")

        sensitivity_payload = None
        # The following block was erroneously duplicated and caused a SyntaxError.
        # It is being removed as the logic for sensitivity_payload construction
        # is handled further down within the "if sidebar_inputs["enable_sensitivity"]:" block.
        # if sidebar_inputs["enable_sensitivity"]: 
        #     "valuation_date": valuation_date.strftime('%Y-%m-%d') if valuation_date else None,
        #     "forecast_years": forecast_years,
        #     ... (rest of duplicated block)
        #     "request_llm_summary": llm_toggle_value, # Add the toggle state to the payload
        # } # This was the unmatched '}'

        # Corrected logic for handling sensitivity payload starts here:
        if sidebar_inputs["enable_sensitivity"]: 
            try:
                row_param_key_final = supported_axis_params.get(st.session_state.get("sens_row_param", "WACC"), "wacc")
                col_param_key_final = supported_axis_params.get(st.session_state.get("sens_col_param", "退出乘数 (EBITDA)"), "exit_multiple")
                row_values_input_str = st.session_state.get("sens_row_values_input", st.session_state.get("sens_row_values_str", ""))
                col_values_input_str = st.session_state.get("sens_col_values_input", st.session_state.get("sens_col_values_str", ""))
                row_values_parsed = [float(x.strip()) for x in row_values_input_str.split(',') if x.strip()] 
                col_values_parsed = [float(x.strip()) for x in col_values_input_str.split(',') if x.strip()] 
                selected_output_metric_displays_final = st.session_state.get("sens_output_metrics_select", list(supported_output_metrics.keys()))
                selected_output_metric_keys_final = [supported_output_metrics[d] for d in selected_output_metric_displays_final]
                if not row_values_parsed or not col_values_parsed:
                     st.error("敏感性分析的行轴和列轴值列表不能为空或解析失败。")
                elif not selected_output_metric_keys_final:
                     st.error("请至少选择一个敏感性分析输出指标。")
                else:
                    sensitivity_payload = {
                        "row_axis": { "parameter_name": row_param_key_final, "values": row_values_parsed, "step": st.session_state.get("sens_row_step"), "points": st.session_state.get("sens_row_points") },
                        "column_axis": { "parameter_name": col_param_key_final, "values": col_values_parsed, "step": st.session_state.get("sens_col_step"), "points": st.session_state.get("sens_col_points") },
                    }
                    base_request_payload["sensitivity_analysis"] = sensitivity_payload
            except ValueError:
                st.error("无法解析敏感性分析的值列表，请确保输入的是逗号分隔的有效数字。")
                sensitivity_payload = None 
                base_request_payload["sensitivity_analysis"] = None 
            except Exception as e: 
                 st.error(f"处理敏感性分析输入时出错: {e}")
                 sensitivity_payload = None
                 base_request_payload["sensitivity_analysis"] = None
        request_payload_filtered = {k: v for k, v in base_request_payload.items() if v is not None}
        selected_metrics_keys_for_render = []
        # Use sidebar_inputs to get the value of enable_sensitivity
        if sidebar_inputs["enable_sensitivity"] and sensitivity_payload: 
            selected_output_metric_displays_render = st.session_state.get("sens_output_metrics_select", list(supported_output_metrics.keys()))
            selected_metrics_keys_for_render = [supported_output_metrics[d] for d in selected_output_metric_displays_render]
        elif sidebar_inputs["enable_sensitivity"]: 
             selected_metrics_keys_for_render = []
        render_valuation_results(request_payload_filtered, sidebar_inputs["ts_code"], base_assumptions=base_request_payload, selected_output_metric_keys_from_ui=selected_metrics_keys_for_render)

with tab_screener:
    render_stock_screener_tab()
