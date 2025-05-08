import streamlit as st
import requests
import pandas as pd
import json
import traceback
import os # 导入 os 以使用 getenv
import numpy as np # Import numpy for isnan check and closest index finding

# --- 配置 ---
API_ENDPOINT = os.getenv("API_ENDPOINT", "http://127.0.0.1:8124/api/v1/valuation") 

# --- 页面配置 ---
st.set_page_config(page_title="股票估值分析工具", layout="wide")

st.title("📈 稳如狗估值服务")
st.caption("炒股风险高，投资需谨慎。梭哈要安全，远离割韭菜。")

# --- 敏感性分析辅助函数与回调 ---

# 定义支持的轴参数和输出指标 (全局，或在回调函数和UI部分都能访问到的地方)
supported_axis_params = {
    "WACC": "wacc", 
    "退出乘数 (EBITDA)": "exit_multiple", 
    "永续增长率": "perpetual_growth_rate"
}
supported_output_metrics = { 
    "每股价值": "value_per_share",
    "企业价值 (EV)": "enterprise_value",
    "股权价值": "equity_value",
    "EV/EBITDA (末期)": "ev_ebitda", 
    "终值/EV 比例": "tv_ev_ratio"
}

# Helper function to generate axis values (更新版，处理 None/NaN 更健壮)
def generate_axis_values(center, step, points):
    # Ensure points is an odd number >= 3
    if not isinstance(points, int) or points < 1:
        points = 3
    elif points % 2 == 0:
        points += 1
        
    # Ensure center and step are valid numbers (handle None or NaN)
    try:
        center = float(center)
        if np.isnan(center): center = 0.0
    except (TypeError, ValueError):
        center = 0.0
    
    try:
        step = float(step)
        if np.isnan(step): step = 0.01
    except (TypeError, ValueError):
        step = 0.01

    offset = (points - 1) // 2
    return [center + step * (i - offset) for i in range(points)]

# Helper function to find the closest index for highlighting (更新版，处理类型和NaN)
def find_closest_index(value_list, target_value):
    """Finds the index of the value in the list closest to the target value."""
    if target_value is None or not value_list:
        return None
    try:
        target_float = float(target_value)
        if np.isnan(target_float): return None
        # Ensure list values are floats for comparison
        value_list_float = np.array(value_list).astype(float)
        if np.isnan(value_list_float).any(): # Handle NaN in the list itself if necessary
             # Option 1: Ignore NaNs in list (find closest among non-NaNs) - more complex
             # Option 2: Return None if list contains NaN (simpler)
             # Let's choose Option 2 for now, or handle based on expected data
             pass # Assuming list should not contain NaN for sensitivity axis
        diffs = np.abs(value_list_float - target_float) 
        return np.argmin(diffs)
    except (ValueError, TypeError):
        return None

# Helper function to apply styling for the center cell (更新版，略微调整边界检查)
def highlight_center_cell_apply(df, center_row_idx, center_col_idx, color='background-color: #fcf8e3'):
    """Applies styling to the center cell based on calculated indices."""
    style_df = pd.DataFrame('', index=df.index, columns=df.columns)
    if center_row_idx is not None and center_col_idx is not None:
        # Ensure indices are within DataFrame bounds
        if 0 <= center_row_idx < df.shape[0] and 0 <= center_col_idx < df.shape[1]:
            style_df.iloc[center_row_idx, center_col_idx] = color
    return style_df

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
            
            # 仅在目标债务比例模式下，且提供了所有参数时计算
            # 注意：这里假设用户选择了“使用目标债务比例”模式，或者我们以此模式为基础估算中心值
            # 更好的做法是检查 wacc_weight_mode_selector 的状态，但回调中可能状态未完全更新
            if all(v is not None for v in [rf, beta_val, mrp, rd, tax, debt_ratio]):
                 cost_of_equity = rf + beta_val * mrp
                 equity_ratio = 1.0 - debt_ratio
                 wacc_calculated = (equity_ratio * cost_of_equity) + (debt_ratio * rd * (1 - tax))
        except (TypeError, ValueError, AttributeError):
             wacc_calculated = None # 参数无效或缺失则无法计算

        # Row center
        if current_row_param_key == "wacc":
            # 如果前端计算成功，则使用计算值，否则使用默认值
            st.session_state.sens_row_center_value = wacc_calculated if wacc_calculated is not None else 0.08
        elif current_row_param_key == "exit_multiple":
            st.session_state.sens_row_center_value = float(base_exit_multiple_val)
        elif current_row_param_key == "perpetual_growth_rate":
            st.session_state.sens_row_center_value = float(base_pgr_val)
        
        # Col center
        if current_col_param_key == "wacc":
            # 如果前端计算成功，则使用计算值，否则使用默认值
            st.session_state.sens_col_center_value = wacc_calculated if wacc_calculated is not None else 0.08
        elif current_col_param_key == "exit_multiple":
            st.session_state.sens_col_center_value = float(base_exit_multiple_val)
        elif current_col_param_key == "perpetual_growth_rate":
            st.session_state.sens_col_center_value = float(base_pgr_val)
            
    except (TypeError, ValueError):
        # Handle cases where base values might be temporarily invalid during input
        st.session_state.sens_row_center_value = st.session_state.get('sens_row_center_value', 0.0) # Keep old or default
        st.session_state.sens_col_center_value = st.session_state.get('sens_col_center_value', 0.0)

    # 4. 获取步长和点数
    row_step_val = st.session_state.get("sens_row_step", 0.005 if current_row_param_key in ["wacc", "perpetual_growth_rate"] else 0.5)
    row_points_val = st.session_state.get("sens_row_points", 5)
    col_step_val = st.session_state.get("sens_col_step", 0.005 if current_col_param_key in ["wacc", "perpetual_growth_rate"] else 0.5)
    col_points_val = st.session_state.get("sens_col_points", 5)

    # 5. 生成新的轴值列表
    final_row_values = generate_axis_values(st.session_state.get('sens_row_center_value', 0.0), row_step_val, row_points_val)
    final_col_values = generate_axis_values(st.session_state.get('sens_col_center_value', 0.0), col_step_val, col_points_val)

    # 6. 更新轴值列表字符串到 session_state
    row_format_spec = ".4f" if current_row_param_key != "exit_multiple" else ".1f"
    col_format_spec = ".4f" if current_col_param_key != "exit_multiple" else ".1f"
    
    try:
        st.session_state.sens_row_values_str = ", ".join([format(float(v), row_format_spec) for v in final_row_values])
        st.session_state.sens_col_values_str = ", ".join([format(float(v), col_format_spec) for v in final_col_values])
    except (ValueError, TypeError):
         # Handle potential errors during formatting if values are unexpected
         st.session_state.sens_row_values_str = "Error generating list"
         st.session_state.sens_col_values_str = "Error generating list"


# --- 初始化 Session State (确保在控件声明前运行，且只运行一次) ---
if 'sensitivity_initialized' not in st.session_state:
    # 为敏感性分析相关 session state key 提供初始占位符或默认值
    # 这些值将在下面的控件声明时被控件的默认 value/index 覆盖
    # 然后 update_sensitivity_ui_elements 会基于这些控件的初始值进行计算
    st.session_state.sens_row_param = st.session_state.get('sens_row_param', "WACC")
    st.session_state.sens_col_param = st.session_state.get('sens_col_param', "退出乘数 (EBITDA)")
    
    _initial_row_param_key = supported_axis_params.get(st.session_state.sens_row_param, "wacc")
    _initial_col_param_key = supported_axis_params.get(st.session_state.sens_col_param, "exit_multiple")

    st.session_state.sens_row_step = st.session_state.get('sens_row_step', 0.005 if _initial_row_param_key in ["wacc", "perpetual_growth_rate"] else 0.5)
    st.session_state.sens_row_points = st.session_state.get('sens_row_points', 5)
    st.session_state.sens_col_step = st.session_state.get('sens_col_step', 0.005 if _initial_col_param_key in ["wacc", "perpetual_growth_rate"] else 0.5)
    st.session_state.sens_col_points = st.session_state.get('sens_col_points', 5)

    st.session_state.sens_row_center_value = 0.0 # Placeholder, will be calculated
    st.session_state.sens_col_center_value = 0.0 # Placeholder, will be calculated
    st.session_state.sens_row_values_str = ""    # Placeholder, will be calculated
    st.session_state.sens_col_values_str = ""    # Placeholder, will be calculated
    
    st.session_state.sensitivity_initialized = True
    # 注意：实际的第一次计算将在控件声明后，通过调用 update_sensitivity_ui_elements() 完成


# --- 函数：渲染估值结果 ---
def render_valuation_results(payload_filtered, current_ts_code, base_assumptions, selected_output_metric_keys_from_ui): # 添加参数传递选择的指标
    """
    渲染估值结果，包括基础结果和可选的敏感性分析。
    Args:
        payload_filtered (dict): 发送给 API 的请求体。
        current_ts_code (str): 当前股票代码。
        base_assumptions (dict): 用于显示中心值的基础假设。
        selected_output_metric_keys_from_ui (list): 用户在UI选择的敏感性分析输出指标key列表。
    """
    st.header("估值结果")
    st.info(f"正在为 {current_ts_code} 请求估值...")
    # st.json(payload_filtered) # Debugging: Show payload

    try:
        with st.spinner('正在调用后端 API 并进行计算...'):
            response = requests.post(API_ENDPOINT, json=payload_filtered, timeout=180) # 增加超时时间
        
        if response.status_code == 200:
            results = response.json()
            
            # --- 结果展示区域 ---
            if results.get("error"):
                st.error(f"估值计算出错: {results['error']}")
            else:
                stock_info = results.get("stock_info", {})
                valuation_results = results.get("valuation_results", {})
                dcf_details = valuation_results.get("dcf_forecast_details", {})
                llm_summary = valuation_results.get("llm_analysis_summary") # 修正缩进
                data_warnings = valuation_results.get("data_warnings") # 修正缩进

                # Store base calculated values for sensitivity center point highlighting
                base_wacc_used = dcf_details.get('wacc_used')
                base_exit_multiple_used = dcf_details.get('exit_multiple_used')
                base_pgr_used = dcf_details.get('perpetual_growth_rate_used')

                # 移除左右布局，改为垂直布局 (修正整个块的缩进)

                # 1. 数据处理警告区 (优先显示)
                if data_warnings:
                    with st.expander("⚠️ 数据处理警告", expanded=False):
                        for warning in data_warnings:
                            st.warning(warning)

                # 2. 股票基本信息区
                st.subheader(f"📊 {stock_info.get('name', 'N/A')} ({stock_info.get('ts_code', 'N/A')}) - 基本信息")
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("最新价格", f"{valuation_results.get('latest_price', 'N/A'):.2f}" if valuation_results.get('latest_price') else "N/A")
                col2.metric("当前 PE", f"{valuation_results.get('current_pe', 'N/A'):.2f}" if valuation_results.get('current_pe') else "N/A")
                col3.metric("当前 PB", f"{valuation_results.get('current_pb', 'N/A'):.2f}" if valuation_results.get('current_pb') else "N/A")
                col4.metric("所属行业", stock_info.get("industry", "N/A"))
                
                # 3. DCF 核心结果区
                st.subheader("核心 DCF 估值结果")
                col1_dcf, col2_dcf, col3_dcf, col4_dcf = st.columns(4)
                dcf_value = dcf_details.get('value_per_share')
                latest_price = valuation_results.get('latest_price')
                safety_margin = ((dcf_value / latest_price) - 1) * 100 if dcf_value is not None and latest_price is not None and latest_price > 0 else None
                
                col1_dcf.metric("每股价值 (DCF)", f"{dcf_value:.2f}" if dcf_value is not None else "N/A")
                col2_dcf.metric("安全边际", f"{safety_margin:.1f}%" if safety_margin is not None else "N/A", delta=f"{safety_margin:.1f}%" if safety_margin is not None else None, delta_color="normal")
                col3_dcf.metric("WACC", f"{dcf_details.get('wacc_used', 'N/A') * 100:.2f}%" if dcf_details.get('wacc_used') is not None else "N/A")
                col4_dcf.metric("Ke (股权成本)", f"{dcf_details.get('cost_of_equity_used', 'N/A') * 100:.2f}%" if dcf_details.get('cost_of_equity_used') is not None else "N/A")

                with st.expander("查看 DCF 详细构成"):
                    col1_detail, col2_detail = st.columns(2) # 保留这里的两列布局以紧凑显示
                    col1_detail.metric("企业价值 (EV)", f"{dcf_details.get('enterprise_value', 'N/A') / 1e8:.2f} 亿" if dcf_details.get('enterprise_value') is not None else "N/A")
                    col1_detail.metric("预测期 UFCF 现值", f"{dcf_details.get('pv_forecast_ufcf', 'N/A') / 1e8:.2f} 亿" if dcf_details.get('pv_forecast_ufcf') is not None else "N/A")
                    col1_detail.metric("终值 (TV)", f"{dcf_details.get('terminal_value', 'N/A') / 1e8:.2f} 亿" if dcf_details.get('terminal_value') is not None else "N/A")
                    
                    col2_detail.metric("股权价值", f"{dcf_details.get('equity_value', 'N/A') / 1e8:.2f} 亿" if dcf_details.get('equity_value') is not None else "N/A")
                    col2_detail.metric("终值现值 (PV of TV)", f"{dcf_details.get('pv_terminal_value', 'N/A') / 1e8:.2f} 亿" if dcf_details.get('pv_terminal_value') is not None else "N/A")
                    col2_detail.metric("净债务", f"{dcf_details.get('net_debt', 'N/A') / 1e8:.2f} 亿" if dcf_details.get('net_debt') is not None else "N/A")
                    
                    st.caption(f"终值计算方法: {dcf_details.get('terminal_value_method_used', 'N/A')}")
                    if dcf_details.get('terminal_value_method_used') == 'exit_multiple':
                        st.caption(f"退出乘数: {dcf_details.get('exit_multiple_used', 'N/A')}")
                    elif dcf_details.get('terminal_value_method_used') == 'perpetual_growth':
                        st.caption(f"永续增长率: {dcf_details.get('perpetual_growth_rate_used', 'N/A') * 100:.2f}%")

                # 详细预测表格展示
                st.subheader("预测期详细数据")
                detailed_forecast_table_data = valuation_results.get("detailed_forecast_table")
                if detailed_forecast_table_data:
                    try:
                        df_forecast = pd.DataFrame(detailed_forecast_table_data)
                        # 简单的格式化示例 (可以根据需要调整)
                        columns_to_format = ['revenue', 'cogs', 'gross_profit', 'sga_rd', 'ebit', 'income_tax', 'nopat', 'd_a', 'capex', 'accounts_receivable', 'inventories', 'accounts_payable', 'other_current_assets', 'other_current_liabilities', 'nwc', 'delta_nwc', 'ebitda', 'ufcf']
                        format_dict = {col: "{:,.0f}" for col in columns_to_format if col in df_forecast.columns} # 格式化为千位分隔符，无小数
                        if 'growth_rate' in df_forecast.columns:
                            format_dict['growth_rate'] = "{:.2%}" # 格式化为百分比
                        
                        # 选择要显示的列 (可以调整顺序和包含的列)
                        display_columns = ['year', 'revenue', 'growth_rate', 'ebit', 'nopat', 'd_a', 'capex', 'delta_nwc', 'ufcf', 'ebitda']
                        existing_display_columns = [col for col in display_columns if col in df_forecast.columns]
                        
                        st.dataframe(df_forecast[existing_display_columns].style.format(format_dict, na_rep='-'))
                    except Exception as e:
                        st.error(f"无法显示预测表格: {e}")
                else:
                    st.info("未找到详细的预测数据。")
                
                # 5. 敏感性分析结果区 (如果存在)
                sensitivity_data = valuation_results.get("sensitivity_analysis_result")
                # Check if sensitivity was enabled in the *request* that generated these results
                sensitivity_enabled_for_this_run = payload_filtered.get("sensitivity_analysis") is not None
                
                if sensitivity_data and sensitivity_enabled_for_this_run: 
                    st.subheader("🔬 敏感性分析结果")
                    try:
                        row_param = sensitivity_data['row_parameter']
                        col_param = sensitivity_data['column_parameter']
                        row_vals = sensitivity_data['row_values']
                        col_vals = sensitivity_data['column_values']
                        result_tables = sensitivity_data['result_tables'] # Get the dictionary of tables

                        # Determine center values from base assumptions used in the *API call*
                        # We passed base_assumptions dict to this function, let's use it
                        center_row_val = None
                        if row_param == 'wacc': center_row_val = base_wacc_used # Use the WACC calculated in base run
                        elif row_param == 'exit_multiple': center_row_val = base_assumptions.get('exit_multiple')
                        elif row_param == 'perpetual_growth_rate': center_row_val = base_assumptions.get('perpetual_growth_rate')
                        
                        center_col_val = None
                        if col_param == 'wacc': center_col_val = base_wacc_used
                        elif col_param == 'exit_multiple': center_col_val = base_assumptions.get('exit_multiple')
                        elif col_param == 'perpetual_growth_rate': center_col_val = base_assumptions.get('perpetual_growth_rate')

                        # Find indices of center values in the sensitivity axis lists
                        center_row_idx = find_closest_index(row_vals, center_row_val)
                        center_col_idx = find_closest_index(col_vals, center_col_val)

                        # 渲染用户选择的每个指标的表格
                        # 使用从UI传递过来的 selected_output_metric_keys_from_ui
                        for metric_key in selected_output_metric_keys_from_ui: 
                            if metric_key in result_tables:
                                table_data = result_tables[metric_key]
                                metric_display_name = next((k for k, v in supported_output_metrics.items() if v == metric_key), metric_key)
                                st.markdown(f"**指标: {metric_display_name}**") 
                                
                                df_sensitivity = pd.DataFrame(table_data, index=row_vals, columns=col_vals)
                                
                                # 格式化显示
                                row_format = "{:.2%}" if row_param == "wacc" or row_param == "perpetual_growth_rate" else "{:.1f}x"
                                col_format = "{:.2%}" if col_param == "wacc" or col_param == "perpetual_growth_rate" else "{:.1f}x"
                                
                                if metric_key == "value_per_share":
                                    cell_format = "{:,.2f}"
                                elif metric_key == "enterprise_value" or metric_key == "equity_value":
                                     cell_format = lambda x: f"{x/1e8:,.2f} 亿" if pd.notna(x) else "N/A"
                                elif metric_key == "ev_ebitda":
                                     cell_format = "{:.1f}x"
                                elif metric_key == "tv_ev_ratio":
                                     cell_format = "{:.1%}"
                                else:
                                     cell_format = "{:,.2f}"

                                df_sensitivity.index = df_sensitivity.index.map(lambda x: row_format.format(x) if pd.notna(x) else '-')
                                df_sensitivity.columns = df_sensitivity.columns.map(lambda x: col_format.format(x) if pd.notna(x) else '-')
                                
                                # 应用单元格格式化和高亮
                                styled_df = df_sensitivity.style
                                if isinstance(cell_format, str):
                                     styled_df = styled_df.format(cell_format, na_rep='N/A')
                                else: # Apply function formatter
                                     styled_df = styled_df.format(cell_format, na_rep='N/A')
                                
                                styled_df = styled_df.highlight_null(color='lightgrey')
                                
                                # Apply center cell highlighting using apply
                                styled_df = styled_df.apply(highlight_center_cell_apply, 
                                                            center_row_idx=center_row_idx, 
                                                            center_col_idx=center_col_idx, 
                                                            axis=None) # axis=None applies to the whole DataFrame

                                st.dataframe(styled_df)
                                
                                st.divider() # Add divider between tables
                            else:
                                st.warning(f"未找到指标 '{metric_key}' 的敏感性分析结果。")

                    except Exception as e:
                        st.error(f"无法显示敏感性分析表格: {e}")
                        # st.json(sensitivity_data) # Debugging

                # 6. LLM 分析与建议区 (移动到末尾)
                st.subheader("🤖 LLM 分析与投资建议摘要")
                st.caption("请结合以下分析判断投资价值。") # 添加引导说明
                if llm_summary:
                    st.markdown(llm_summary)
                else:
                    st.warning("未能获取 LLM 分析结果。")

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


# --- 用户输入区域 ---
with st.sidebar:
    st.header("估值参数输入")

    ts_code = st.text_input("股票代码 (例如 600519.SH):", "600519.SH", key="ts_code_input")
    valuation_date = st.date_input("估值基准日期:", value=pd.to_datetime("today"), key="valuation_date_input")

    st.subheader("DCF 核心假设")
    forecast_years = st.slider("预测期年数:", min_value=3, max_value=15, value=5, key="forecast_years_slider")
    
    with st.expander("收入预测假设", expanded=True):
        cagr_decay_rate = st.number_input("历史 CAGR 年衰减率 (0-1):", min_value=0.0, max_value=1.0, value=0.1, step=0.01, format="%.2f", help="用于基于历史CAGR预测未来收入时的年衰减比例。0表示不衰减，1表示第一年后增长为0。", key="cagr_decay")

    with st.expander("利润率与费用预测假设"):
        op_margin_forecast_mode = st.selectbox("营业利润率模式:", options=['historical_median', 'transition_to_target'], index=0, key="op_margin_mode", help="选择使用历史中位数，还是逐渐过渡到目标值。")
        target_operating_margin = st.number_input("目标营业利润率:", value=0.15, step=0.01, format="%.3f", key="target_op_margin", disabled=(op_margin_forecast_mode != 'transition_to_target')) if op_margin_forecast_mode == 'transition_to_target' else None
        op_margin_transition_years = st.number_input("利润率过渡年数:", min_value=1, value=forecast_years, step=1, key="op_margin_trans_years", disabled=(op_margin_forecast_mode != 'transition_to_target' or target_operating_margin is None)) if op_margin_forecast_mode == 'transition_to_target' else None

        sga_rd_ratio_forecast_mode = st.selectbox("SGA&RD 占收入比模式:", options=['historical_median', 'transition_to_target'], index=0, key="sga_rd_mode")
        target_sga_rd_to_revenue_ratio = st.number_input("目标 SGA&RD 占收入比:", value=0.20, step=0.01, format="%.3f", key="target_sga_rd_ratio", disabled=(sga_rd_ratio_forecast_mode != 'transition_to_target')) if sga_rd_ratio_forecast_mode == 'transition_to_target' else None
        sga_rd_transition_years = st.number_input("SGA&RD 比率过渡年数:", min_value=1, value=forecast_years, step=1, key="sga_rd_trans_years", disabled=(sga_rd_ratio_forecast_mode != 'transition_to_target' or target_sga_rd_to_revenue_ratio is None)) if sga_rd_ratio_forecast_mode == 'transition_to_target' else None

    with st.expander("资产与投资预测假设"):
        da_ratio_forecast_mode = st.selectbox("D&A 占收入比模式:", options=['historical_median', 'transition_to_target'], index=0, key="da_mode")
        target_da_to_revenue_ratio = st.number_input("目标 D&A 占收入比:", value=0.05, step=0.005, format="%.3f", key="target_da_ratio", disabled=(da_ratio_forecast_mode != 'transition_to_target')) if da_ratio_forecast_mode == 'transition_to_target' else None
        da_ratio_transition_years = st.number_input("D&A 比率过渡年数:", min_value=1, value=forecast_years, step=1, key="da_trans_years", disabled=(da_ratio_forecast_mode != 'transition_to_target' or target_da_to_revenue_ratio is None)) if da_ratio_forecast_mode == 'transition_to_target' else None

        capex_ratio_forecast_mode = st.selectbox("Capex 占收入比模式:", options=['historical_median', 'transition_to_target'], index=0, key="capex_mode")
        target_capex_to_revenue_ratio = st.number_input("目标 Capex 占收入比:", value=0.07, step=0.005, format="%.3f", key="target_capex_ratio", disabled=(capex_ratio_forecast_mode != 'transition_to_target')) if capex_ratio_forecast_mode == 'transition_to_target' else None
        capex_ratio_transition_years = st.number_input("Capex 比率过渡年数:", min_value=1, value=forecast_years, step=1, key="capex_trans_years", disabled=(capex_ratio_forecast_mode != 'transition_to_target' or target_capex_to_revenue_ratio is None)) if capex_ratio_forecast_mode == 'transition_to_target' else None

    with st.expander("营运资本预测假设"):
        nwc_days_forecast_mode = st.selectbox("核心 NWC 周转天数模式:", options=['historical_median', 'transition_to_target'], index=0, key="nwc_days_mode")
        target_accounts_receivable_days = st.number_input("目标 DSO:", value=30.0, step=1.0, format="%.1f", key="target_ar_days", disabled=(nwc_days_forecast_mode != 'transition_to_target')) if nwc_days_forecast_mode == 'transition_to_target' else None
        target_inventory_days = st.number_input("目标 DIO:", value=60.0, step=1.0, format="%.1f", key="target_inv_days", disabled=(nwc_days_forecast_mode != 'transition_to_target')) if nwc_days_forecast_mode == 'transition_to_target' else None
        target_accounts_payable_days = st.number_input("目标 DPO:", value=45.0, step=1.0, format="%.1f", key="target_ap_days", disabled=(nwc_days_forecast_mode != 'transition_to_target')) if nwc_days_forecast_mode == 'transition_to_target' else None
        nwc_days_transition_years = st.number_input("NWC 天数过渡年数:", min_value=1, value=forecast_years, step=1, key="nwc_days_trans_years", disabled=(nwc_days_forecast_mode != 'transition_to_target' or not any([target_accounts_receivable_days, target_inventory_days, target_accounts_payable_days]))) if nwc_days_forecast_mode == 'transition_to_target' else None

        other_nwc_ratio_forecast_mode = st.selectbox("其他 NWC 占收入比模式:", options=['historical_median', 'transition_to_target'], index=0, key="other_nwc_mode")
        target_other_current_assets_to_revenue_ratio = st.number_input("目标其他流动资产/收入:", value=0.05, step=0.005, format="%.3f", key="target_oca_ratio", disabled=(other_nwc_ratio_forecast_mode != 'transition_to_target')) if other_nwc_ratio_forecast_mode == 'transition_to_target' else None
        target_other_current_liabilities_to_revenue_ratio = st.number_input("目标其他流动负债/收入:", value=0.03, step=0.005, format="%.3f", key="target_ocl_ratio", disabled=(other_nwc_ratio_forecast_mode != 'transition_to_target')) if other_nwc_ratio_forecast_mode == 'transition_to_target' else None
        other_nwc_ratio_transition_years = st.number_input("其他 NWC 比率过渡年数:", min_value=1, value=forecast_years, step=1, key="other_nwc_trans_years", disabled=(other_nwc_ratio_forecast_mode != 'transition_to_target' or not any([target_other_current_assets_to_revenue_ratio, target_other_current_liabilities_to_revenue_ratio]))) if other_nwc_ratio_forecast_mode == 'transition_to_target' else None

    with st.expander("税率假设"):
        target_effective_tax_rate = st.number_input("目标有效所得税率:", min_value=0.0, max_value=1.0, value=0.25, step=0.01, format="%.2f", key="tax_rate")

    with st.expander("WACC 参数 (可选覆盖)"):
        wacc_weight_mode_ui = st.radio(
            "WACC 权重模式:", 
            options=["使用目标债务比例", "使用最新市场价值计算权重"], 
            index=0, 
            key="wacc_weight_mode_selector",
            help="选择使用预设的目标资本结构，还是基于最新的市值和负债动态计算资本结构权重。"
        )
        
        target_debt_ratio_disabled = (wacc_weight_mode_ui == "使用最新市场价值计算权重")
        target_debt_ratio = st.number_input(
            "目标债务比例 D/(D+E):", 
            min_value=0.0, 
            max_value=1.0, 
            value=0.45, 
            step=0.05, 
            format="%.2f", 
            help="仅在选择“使用目标债务比例”模式时有效。留空则使用后端默认值。", 
            key="wacc_debt_ratio",
            disabled=target_debt_ratio_disabled
        )
        
        cost_of_debt = st.number_input("税前债务成本 (Rd):", min_value=0.0, value=0.05, step=0.005, format="%.3f", help="留空则使用默认值", key="wacc_cost_debt")
        risk_free_rate = st.number_input("无风险利率 (Rf):", min_value=0.0, value=0.03, step=0.005, format="%.3f", help="留空则使用默认值", key="wacc_rf")
        beta = st.number_input("贝塔系数 (Beta):", value=1.0, step=0.1, format="%.2f", help="留空则使用数据库最新值或默认值", key="wacc_beta")
        market_risk_premium = st.number_input("市场风险溢价 (MRP):", min_value=0.0, value=0.06, step=0.005, format="%.3f", help="留空则使用默认值", key="wacc_mrp")
        # size_premium = st.number_input("规模溢价:", value=0.0, step=0.001, format="%.3f") # 暂时隐藏

    with st.expander("终值计算假设"):
        terminal_value_method = st.selectbox("终值计算方法:", options=['exit_multiple', 'perpetual_growth'], index=0, key="tv_method")
        # 添加 on_change 回调, 修改默认值为 6.0
        exit_multiple = st.number_input("退出乘数 (EBITDA):", min_value=0.1, value=6.0, step=0.5, format="%.1f", 
                                        key="tv_exit_multiple", 
                                        disabled=(terminal_value_method != 'exit_multiple'), 
                                        on_change=update_sensitivity_ui_elements) if terminal_value_method == 'exit_multiple' else None
        # 添加 on_change 回调
        perpetual_growth_rate = st.number_input("永续增长率:", min_value=0.0, max_value=0.05, value=0.025, step=0.001, format="%.3f", 
                                                key="tv_pg_rate", 
                                                disabled=(terminal_value_method != 'perpetual_growth'), 
                                                on_change=update_sensitivity_ui_elements) if terminal_value_method == 'perpetual_growth' else None

    # --- 敏感性分析配置 (移动到侧边栏) ---
    st.divider()
    st.subheader("🔬 敏感性分析 (可选)")
    # 默认启用敏感性分析
    enable_sensitivity = st.checkbox("启用敏感性分析", value=True, key="enable_sensitivity_cb")

    if enable_sensitivity:
        # 调用一次回调函数以确保初始状态正确显示
        # 需要确保此时 tv_exit_multiple 和 tv_pg_rate 已经有初始值在 session_state 中
        # if 'sensitivity_initialized' in st.session_state and st.session_state.sensitivity_initialized:
             # 避免在每次脚本运行时都调用，只在控件值改变时通过 on_change 调用
             # 但我们需要确保初始加载时 UI 是正确的。
             # 更好的方法可能是在控件声明后立即调用一次。
             # 或者依赖 on_change 在控件初始化时触发（如果 Streamlit 这样做的话）
             # 让我们尝试在控件声明后调用一次
             # pass # 移动调用位置到控件声明后

        # --- 轴定义 ---
        # 使用 st.columns 创建布局，但现在是在 sidebar 内部
        # col_sens1, col_sens2, col_sens3 = st.columns(3) # 在 sidebar 中可能不需要分三列，或者需要调整宽度
        
        # 为了简化，暂时不分列，直接在 sidebar 中垂直排列
        
        st.markdown("**行轴设置**")
        row_param_display = st.selectbox(
            "选择行轴参数:", 
            options=list(supported_axis_params.keys()), 
            index=0, 
            key="sens_row_param",
            on_change=update_sensitivity_ui_elements # 添加 on_change
        )
        # row_param_key = supported_axis_params[row_param_display] # Key 在回调函数内部获取

        row_step = st.number_input("步长:", 
                                   value=st.session_state.get("sens_row_step"), # 从 session_state 获取初始值
                                   step=0.001 if supported_axis_params.get(row_param_display) != "exit_multiple" else 0.1, 
                                   format="%.4f" if supported_axis_params.get(row_param_display) != "exit_multiple" else "%.1f", 
                                   key="sens_row_step",
                                   on_change=update_sensitivity_ui_elements) # 添加 on_change
                                   
        row_points = st.slider("点数 (奇数):", 
                               min_value=3, max_value=9, 
                               value=st.session_state.get("sens_row_points"), # 从 session_state 获取初始值
                               step=2, 
                               key="sens_row_points",
                               on_change=update_sensitivity_ui_elements) # 添加 on_change

        # 在这里调用一次回调来设置初始中心值和列表
        # 确保此时所有依赖的控件（tv_exit_multiple, tv_pg_rate, sens_row_param, sens_row_step, sens_row_points 等）
        # 已经声明并将其初始值放入了 session_state
        # if 'sensitivity_initialized' in st.session_state and st.session_state.sensitivity_initialized and 'sens_row_center_value' not in st.session_state:
             # 确保只在真正需要初始化时调用
             # 或者在脚本开始处初始化 session state 后调用一次
             # pass # 移动到 session state 初始化之后调用
        # 移动到下方控件声明之后调用

        # Display center value (disabled) - value comes from session state (由回调更新)
        st.number_input(f"中心值 ({row_param_display}):", 
                        value=float(st.session_state.get('sens_row_center_value', 0.0)), # 使用 .get 获取
                        key="sens_row_center_display", 
                        disabled=True, 
                        format="%.4f" if supported_axis_params.get(row_param_display) == "wacc" or supported_axis_params.get(row_param_display) == "perpetual_growth_rate" else "%.1f")

        # Text area for displaying/editing the generated list (由回调更新)
        row_values_str = st.text_area(
            "行轴值列表 (逗号分隔):", 
            value=st.session_state.get('sens_row_values_str', ""), # 使用 .get 获取
            key="sens_row_values_input" # 用户可能编辑，所以保留输入 key
            # 注意：如果用户编辑了这里，回调函数不会自动更新中心值等，
            # 点击“计算”时会使用用户编辑后的列表。这是预期的行为。
        )

        st.markdown("**列轴设置**")
        # Filter out the parameter selected for the row axis
        available_col_params_options = [k for k, v in supported_axis_params.items() if v != supported_axis_params.get(row_param_display)]
        # 确定列参数的默认索引
        current_col_display = st.session_state.get("sens_col_param", available_col_params_options[0] if available_col_params_options else list(supported_axis_params.keys())[0])
        col_default_index = available_col_params_options.index(current_col_display) if current_col_display in available_col_params_options else 0

        col_param_display = st.selectbox(
            "选择列轴参数:", 
            options=available_col_params_options, 
            index=col_default_index, 
            key="sens_col_param",
            on_change=update_sensitivity_ui_elements # 添加 on_change
        )
        # col_param_key = available_col_params[col_param_display] # Key 在回调函数内部获取

        col_step = st.number_input("步长:", 
                                   value=st.session_state.get("sens_col_step"), # 从 session_state 获取初始值
                                   step=0.001 if supported_axis_params.get(col_param_display) != "exit_multiple" else 0.1, 
                                   format="%.4f" if supported_axis_params.get(col_param_display) != "exit_multiple" else "%.1f", 
                                   key="sens_col_step",
                                   on_change=update_sensitivity_ui_elements) # 添加 on_change
                                   
        col_points = st.slider("点数 (奇数):", 
                               min_value=3, max_value=9, 
                               value=st.session_state.get("sens_col_points"), # 从 session_state 获取初始值
                               step=2, 
                               key="sens_col_points",
                               on_change=update_sensitivity_ui_elements) # 添加 on_change

        # Display center value (disabled) - value comes from session state (由回调更新)
        st.number_input(f"中心值 ({col_param_display}):", 
                        value=float(st.session_state.get('sens_col_center_value', 0.0)), # 使用 .get 获取
                        key="sens_col_center_display", 
                        disabled=True, 
                        format="%.4f" if supported_axis_params.get(col_param_display) == "wacc" or supported_axis_params.get(col_param_display) == "perpetual_growth_rate" else "%.1f")

        # Text area for displaying/editing the generated list (由回调更新)
        col_values_str = st.text_area(
            "列轴值列表 (逗号分隔):", 
            value=st.session_state.get('sens_col_values_str', ""), # 使用 .get 获取
            key="sens_col_values_input" # 用户可能编辑
        )

        st.markdown("**输出指标**")
        # Multi-select for output metrics, default to all selected
        selected_output_metric_displays = st.multiselect(
            "选择要显示的敏感性表格指标:", 
            options=list(supported_output_metrics.keys()), 
            default=list(supported_output_metrics.keys()), # Default to all
            key="sens_output_metrics_select"
        )
        # Get backend keys for selected metrics (移到按钮点击逻辑中，因为这里可能还未选择)
        # selected_output_metric_keys = [supported_output_metrics[d] for d in selected_output_metric_displays] 
        
        # 在所有相关控件声明后，调用一次回调以设置初始UI状态
        # 确保 sensitivity_initialized 标志存在
        if 'sensitivity_initialized' in st.session_state and st.session_state.sensitivity_initialized:
             # 检查是否是第一次加载UI（或者相关的基础值是否已设置）
             # 避免在每次交互的回调触发后再次调用
             if 'sens_ui_initialized_run' not in st.session_state:
                 update_sensitivity_ui_elements()
                 st.session_state.sens_ui_initialized_run = True # 标记已完成首次UI更新

    # --- 触发计算按钮现在应该在 sidebar 外部 ---
    # (移动敏感性分析块后，这部分代码保持在主区域不变)

    st.divider()
    st.caption("未来功能：情景分析")
    st.info("未来版本将支持对关键假设进行情景分析。")

# --- 删除主区域的敏感性分析配置 ---
# (这部分代码将被下面的空 REPLACE 块删除)


# --- 函数：渲染估值结果 ---
def render_valuation_results(payload_filtered, current_ts_code, base_assumptions, selected_output_metric_keys_from_ui): # 添加参数传递选择的指标
    """
    渲染估值结果，包括基础结果和可选的敏感性分析。
    Args:
        payload_filtered (dict): 发送给 API 的请求体。
        current_ts_code (str): 当前股票代码。
        base_assumptions (dict): 用于显示中心值的基础假设。
        selected_output_metric_keys_from_ui (list): 用户在UI选择的敏感性分析输出指标key列表。
    """
    st.header("估值结果")
    st.info(f"正在为 {current_ts_code} 请求估值...")
    # st.json(payload_filtered) # Debugging: Show payload

    try:
        with st.spinner('正在调用后端 API 并进行计算...'):
            response = requests.post(API_ENDPOINT, json=payload_filtered, timeout=180) # 增加超时时间
        
        if response.status_code == 200:
            results = response.json()
            
            # --- 结果展示区域 ---
            if results.get("error"):
                st.error(f"估值计算出错: {results['error']}")
            else:
                stock_info = results.get("stock_info", {})
                valuation_results = results.get("valuation_results", {})
                dcf_details = valuation_results.get("dcf_forecast_details", {})
                llm_summary = valuation_results.get("llm_analysis_summary") # 修正缩进
                data_warnings = valuation_results.get("data_warnings") # 修正缩进

                # Store base calculated values for sensitivity center point highlighting
                base_wacc_used = dcf_details.get('wacc_used')
                base_exit_multiple_used = dcf_details.get('exit_multiple_used')
                base_pgr_used = dcf_details.get('perpetual_growth_rate_used')

                # 移除左右布局，改为垂直布局 (修正整个块的缩进)

                # 1. 数据处理警告区 (优先显示)
                if data_warnings:
                    with st.expander("⚠️ 数据处理警告", expanded=False):
                        for warning in data_warnings:
                            st.warning(warning)

                # 2. 股票基本信息区
                st.subheader(f"📊 {stock_info.get('name', 'N/A')} ({stock_info.get('ts_code', 'N/A')}) - 基本信息")
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("最新价格", f"{valuation_results.get('latest_price', 'N/A'):.2f}" if valuation_results.get('latest_price') else "N/A")
                col2.metric("当前 PE", f"{valuation_results.get('current_pe', 'N/A'):.2f}" if valuation_results.get('current_pe') else "N/A")
                col3.metric("当前 PB", f"{valuation_results.get('current_pb', 'N/A'):.2f}" if valuation_results.get('current_pb') else "N/A")
                col4.metric("所属行业", stock_info.get("industry", "N/A"))
                
                # 3. DCF 核心结果区
                st.subheader("核心 DCF 估值结果")
                col1_dcf, col2_dcf, col3_dcf, col4_dcf = st.columns(4)
                dcf_value = dcf_details.get('value_per_share')
                latest_price = valuation_results.get('latest_price')
                safety_margin = ((dcf_value / latest_price) - 1) * 100 if dcf_value is not None and latest_price is not None and latest_price > 0 else None
                
                col1_dcf.metric("每股价值 (DCF)", f"{dcf_value:.2f}" if dcf_value is not None else "N/A")
                col2_dcf.metric("安全边际", f"{safety_margin:.1f}%" if safety_margin is not None else "N/A", delta=f"{safety_margin:.1f}%" if safety_margin is not None else None, delta_color="normal")
                col3_dcf.metric("WACC", f"{dcf_details.get('wacc_used', 'N/A') * 100:.2f}%" if dcf_details.get('wacc_used') is not None else "N/A")
                col4_dcf.metric("Ke (股权成本)", f"{dcf_details.get('cost_of_equity_used', 'N/A') * 100:.2f}%" if dcf_details.get('cost_of_equity_used') is not None else "N/A")

                with st.expander("查看 DCF 详细构成"):
                    col1_detail, col2_detail = st.columns(2) # 保留这里的两列布局以紧凑显示
                    col1_detail.metric("企业价值 (EV)", f"{dcf_details.get('enterprise_value', 'N/A') / 1e8:.2f} 亿" if dcf_details.get('enterprise_value') is not None else "N/A")
                    col1_detail.metric("预测期 UFCF 现值", f"{dcf_details.get('pv_forecast_ufcf', 'N/A') / 1e8:.2f} 亿" if dcf_details.get('pv_forecast_ufcf') is not None else "N/A")
                    col1_detail.metric("终值 (TV)", f"{dcf_details.get('terminal_value', 'N/A') / 1e8:.2f} 亿" if dcf_details.get('terminal_value') is not None else "N/A")
                    
                    col2_detail.metric("股权价值", f"{dcf_details.get('equity_value', 'N/A') / 1e8:.2f} 亿" if dcf_details.get('equity_value') is not None else "N/A")
                    col2_detail.metric("终值现值 (PV of TV)", f"{dcf_details.get('pv_terminal_value', 'N/A') / 1e8:.2f} 亿" if dcf_details.get('pv_terminal_value') is not None else "N/A")
                    col2_detail.metric("净债务", f"{dcf_details.get('net_debt', 'N/A') / 1e8:.2f} 亿" if dcf_details.get('net_debt') is not None else "N/A")
                    
                    st.caption(f"终值计算方法: {dcf_details.get('terminal_value_method_used', 'N/A')}")
                    if dcf_details.get('terminal_value_method_used') == 'exit_multiple':
                        st.caption(f"退出乘数: {dcf_details.get('exit_multiple_used', 'N/A')}")
                    elif dcf_details.get('terminal_value_method_used') == 'perpetual_growth':
                        st.caption(f"永续增长率: {dcf_details.get('perpetual_growth_rate_used', 'N/A') * 100:.2f}%")

                # 详细预测表格展示
                st.subheader("预测期详细数据")
                detailed_forecast_table_data = valuation_results.get("detailed_forecast_table")
                if detailed_forecast_table_data:
                    try:
                        df_forecast = pd.DataFrame(detailed_forecast_table_data)
                        # 简单的格式化示例 (可以根据需要调整)
                        columns_to_format = ['revenue', 'cogs', 'gross_profit', 'sga_rd', 'ebit', 'income_tax', 'nopat', 'd_a', 'capex', 'accounts_receivable', 'inventories', 'accounts_payable', 'other_current_assets', 'other_current_liabilities', 'nwc', 'delta_nwc', 'ebitda', 'ufcf']
                        format_dict = {col: "{:,.0f}" for col in columns_to_format if col in df_forecast.columns} # 格式化为千位分隔符，无小数
                        if 'growth_rate' in df_forecast.columns:
                            format_dict['growth_rate'] = "{:.2%}" # 格式化为百分比
                        
                        # 选择要显示的列 (可以调整顺序和包含的列)
                        display_columns = ['year', 'revenue', 'growth_rate', 'ebit', 'nopat', 'd_a', 'capex', 'delta_nwc', 'ufcf', 'ebitda']
                        existing_display_columns = [col for col in display_columns if col in df_forecast.columns]
                        
                        st.dataframe(df_forecast[existing_display_columns].style.format(format_dict, na_rep='-'))
                    except Exception as e:
                        st.error(f"无法显示预测表格: {e}")
                else:
                    st.info("未找到详细的预测数据。")
                
                # 5. 敏感性分析结果区 (如果存在)
                sensitivity_data = valuation_results.get("sensitivity_analysis_result")
                # Check if sensitivity was enabled in the *request* that generated these results
                sensitivity_enabled_for_this_run = payload_filtered.get("sensitivity_analysis") is not None
                
                if sensitivity_data and sensitivity_enabled_for_this_run: 
                    st.subheader("🔬 敏感性分析结果")
                    try:
                        row_param = sensitivity_data['row_parameter']
                        col_param = sensitivity_data['column_parameter']
                        row_vals = sensitivity_data['row_values']
                        col_vals = sensitivity_data['column_values']
                        result_tables = sensitivity_data['result_tables'] # Get the dictionary of tables

                        # Determine center values from base assumptions used in the *API call*
                        # We passed base_assumptions dict to this function, let's use it
                        center_row_val = None
                        if row_param == 'wacc': center_row_val = base_wacc_used # Use the WACC calculated in base run
                        elif row_param == 'exit_multiple': center_row_val = base_assumptions.get('exit_multiple')
                        elif row_param == 'perpetual_growth_rate': center_row_val = base_assumptions.get('perpetual_growth_rate')
                        
                        center_col_val = None
                        if col_param == 'wacc': center_col_val = base_wacc_used
                        elif col_param == 'exit_multiple': center_col_val = base_assumptions.get('exit_multiple')
                        elif col_param == 'perpetual_growth_rate': center_col_val = base_assumptions.get('perpetual_growth_rate')

                        # Find indices of center values in the sensitivity axis lists
                        center_row_idx = find_closest_index(row_vals, center_row_val)
                        center_col_idx = find_closest_index(col_vals, center_col_val)

                        # 渲染用户选择的每个指标的表格
                        # 使用从UI传递过来的 selected_output_metric_keys_from_ui
                        for metric_key in selected_output_metric_keys_from_ui: 
                            if metric_key in result_tables:
                                table_data = result_tables[metric_key]
                                metric_display_name = next((k for k, v in supported_output_metrics.items() if v == metric_key), metric_key)
                                st.markdown(f"**指标: {metric_display_name}**") 
                                
                                df_sensitivity = pd.DataFrame(table_data, index=row_vals, columns=col_vals)
                                
                                # 格式化显示
                                row_format = "{:.2%}" if row_param == "wacc" or row_param == "perpetual_growth_rate" else "{:.1f}x"
                                col_format = "{:.2%}" if col_param == "wacc" or col_param == "perpetual_growth_rate" else "{:.1f}x"
                                
                                if metric_key == "value_per_share":
                                    cell_format = "{:,.2f}"
                                elif metric_key == "enterprise_value" or metric_key == "equity_value":
                                     cell_format = lambda x: f"{x/1e8:,.2f} 亿" if pd.notna(x) else "N/A"
                                elif metric_key == "ev_ebitda":
                                     cell_format = "{:.1f}x"
                                elif metric_key == "tv_ev_ratio":
                                     cell_format = "{:.1%}"
                                else:
                                     cell_format = "{:,.2f}"

                                df_sensitivity.index = df_sensitivity.index.map(lambda x: row_format.format(x) if pd.notna(x) else '-')
                                df_sensitivity.columns = df_sensitivity.columns.map(lambda x: col_format.format(x) if pd.notna(x) else '-')
                                
                                # 应用单元格格式化和高亮
                                styled_df = df_sensitivity.style
                                if isinstance(cell_format, str):
                                     styled_df = styled_df.format(cell_format, na_rep='N/A')
                                else: # Apply function formatter
                                     styled_df = styled_df.format(cell_format, na_rep='N/A')
                                
                                styled_df = styled_df.highlight_null(color='lightgrey')
                                
                                # Apply center cell highlighting using apply
                                styled_df = styled_df.apply(highlight_center_cell_apply, 
                                                            center_row_idx=center_row_idx, 
                                                            center_col_idx=center_col_idx, 
                                                            axis=None) # axis=None applies to the whole DataFrame

                                st.dataframe(styled_df)
                                
                                st.divider() # Add divider between tables
                            else:
                                st.warning(f"未找到指标 '{metric_key}' 的敏感性分析结果。")

                    except Exception as e:
                        st.error(f"无法显示敏感性分析表格: {e}")
                        # st.json(sensitivity_data) # Debugging

                # 6. LLM 分析与建议区 (移动到末尾)
                st.subheader("🤖 LLM 分析与投资建议摘要")
                st.caption("请结合以下分析判断投资价值。") # 添加引导说明
                if llm_summary:
                    st.markdown(llm_summary)
                else:
                    st.warning("未能获取 LLM 分析结果。")

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


# --- 触发计算 ---
if st.button("🚀 开始估值计算", key="start_valuation_button"): # 将按钮移到主区域
    
    # --- 构建基础请求体 ---
    base_request_payload = {
        "ts_code": ts_code,
        "valuation_date": valuation_date.strftime('%Y-%m-%d') if valuation_date else None,
        "forecast_years": forecast_years,
        "cagr_decay_rate": cagr_decay_rate,
        # 利润率
        "op_margin_forecast_mode": op_margin_forecast_mode,
        "target_operating_margin": target_operating_margin,
        "op_margin_transition_years": op_margin_transition_years,
        # SGA & RD
        "sga_rd_ratio_forecast_mode": sga_rd_ratio_forecast_mode,
        "target_sga_rd_to_revenue_ratio": target_sga_rd_to_revenue_ratio,
        "sga_rd_transition_years": sga_rd_transition_years,
        # D&A
        "da_ratio_forecast_mode": da_ratio_forecast_mode, # 更正字典键名
        "target_da_to_revenue_ratio": target_da_to_revenue_ratio,
        "da_ratio_transition_years": da_ratio_transition_years,
        # Capex
        "capex_ratio_forecast_mode": capex_ratio_forecast_mode, # 更正字典键名
        "target_capex_to_revenue_ratio": target_capex_to_revenue_ratio,
        "capex_ratio_transition_years": capex_ratio_transition_years,
        # NWC Days
        "nwc_days_forecast_mode": nwc_days_forecast_mode,
        "target_accounts_receivable_days": target_accounts_receivable_days,
        "target_inventory_days": target_inventory_days,
        "target_accounts_payable_days": target_accounts_payable_days,
        "nwc_days_transition_years": nwc_days_transition_years,
        # Other NWC Ratios
        "other_nwc_ratio_forecast_mode": other_nwc_ratio_forecast_mode,
        "target_other_current_assets_to_revenue_ratio": target_other_current_assets_to_revenue_ratio,
        "target_other_current_liabilities_to_revenue_ratio": target_other_current_liabilities_to_revenue_ratio,
        "other_nwc_ratio_transition_years": other_nwc_ratio_transition_years,
        # Tax Rate
        "target_effective_tax_rate": target_effective_tax_rate,
        # WACC Params
        "wacc_weight_mode": "market" if wacc_weight_mode_ui == "使用最新市场价值计算权重" else "target", # 添加模式
        "target_debt_ratio": target_debt_ratio if not target_debt_ratio_disabled else None, # 仅在 target 模式下传递
        "cost_of_debt": cost_of_debt,
        "risk_free_rate": risk_free_rate,
        "beta": beta,
        "market_risk_premium": market_risk_premium,
        # Terminal Value
        "terminal_value_method": terminal_value_method,
        "exit_multiple": exit_multiple,
        "perpetual_growth_rate": perpetual_growth_rate,
        # Sensitivity Analysis (will be added below if enabled)
    }

    # --- 添加敏感性分析配置 (如果启用) ---
    sensitivity_payload = None
    if enable_sensitivity: # 使用侧边栏的 enable_sensitivity
        try:
            # --- Recalculate center values and generate lists based on base inputs ---
            # 这些值现在应该由回调函数更新到 session_state 中
            # 但为了确保在按钮点击时使用最新的值（以防回调有延迟或问题），可以重新计算或读取
            # 这里我们信任 session_state 已被回调更新
            
            # 获取行/列参数 key (从 session_state 读取，因为 display 值可能已改变)
            row_param_key_final = supported_axis_params.get(st.session_state.get("sens_row_param", "WACC"), "wacc")
            col_param_key_final = supported_axis_params.get(st.session_state.get("sens_col_param", "退出乘数 (EBITDA)"), "exit_multiple")

            # Parse the potentially user-edited values from the text area
            # Use the keys associated with the text_area widgets
            # 这些值现在由回调函数更新到 session_state.sens_row_values_str / sens_col_values_str
            # 用户也可以手动编辑 sens_row_values_input / sens_col_values_input
            # 我们应该优先使用用户可能编辑过的值
            row_values_input_str = st.session_state.get("sens_row_values_input", st.session_state.get("sens_row_values_str", ""))
            col_values_input_str = st.session_state.get("sens_col_values_input", st.session_state.get("sens_col_values_str", ""))
            
            row_values_parsed = [float(x.strip()) for x in row_values_input_str.split(',') if x.strip()] 
            col_values_parsed = [float(x.strip()) for x in col_values_input_str.split(',') if x.strip()] 

            # 获取在UI上选择的输出指标
            selected_output_metric_displays_final = st.session_state.get("sens_output_metrics_select", list(supported_output_metrics.keys()))
            selected_output_metric_keys_final = [supported_output_metrics[d] for d in selected_output_metric_displays_final]


            if not row_values_parsed or not col_values_parsed:
                 st.error("敏感性分析的行轴和列轴值列表不能为空或解析失败。")
            elif not selected_output_metric_keys_final:
                 st.error("请至少选择一个敏感性分析输出指标。")
            else:
                sensitivity_payload = {
                    "row_axis": {
                        "parameter_name": row_param_key_final, # 使用从 session_state 获取的 key
                        "values": row_values_parsed
                    },
                    "column_axis": {
                        "parameter_name": col_param_key_final, # 使用从 session_state 获取的 key
                        "values": col_values_parsed
                    },
                    # "output_metric" is no longer sent in the request
                }
                base_request_payload["sensitivity_analysis"] = sensitivity_payload
        except ValueError:
            st.error("无法解析敏感性分析的值列表，请确保输入的是逗号分隔的有效数字。")
            sensitivity_payload = None # Reset if parsing fails
            base_request_payload["sensitivity_analysis"] = None # Ensure it's not sent
        except Exception as e: # 添加通用异常捕获
             st.error(f"处理敏感性分析输入时出错: {e}")
             sensitivity_payload = None
             base_request_payload["sensitivity_analysis"] = None


    # 过滤掉基础 payload 中的 None 值 (敏感性部分已处理)
    request_payload_filtered = {k: v for k, v in base_request_payload.items() if v is not None}
    
    # 获取最终选择的输出指标列表 (即使敏感性分析未启用或失败，也需要传递空列表或默认值)
    selected_metrics_keys_for_render = []
    if enable_sensitivity and sensitivity_payload: # 仅在敏感性分析启用且 payload 构建成功时获取
        selected_output_metric_displays_render = st.session_state.get("sens_output_metrics_select", list(supported_output_metrics.keys()))
        selected_metrics_keys_for_render = [supported_output_metrics[d] for d in selected_output_metric_displays_render]
    elif enable_sensitivity: # 如果启用了但 payload 失败，传递空列表
         selected_metrics_keys_for_render = []
    # 如果未启用敏感性分析，render 函数内部的敏感性结果渲染逻辑不会执行

    # 渲染结果 (传递基础假设和选择的输出指标)
    render_valuation_results(request_payload_filtered, ts_code, base_assumptions=base_request_payload, selected_output_metric_keys_from_ui=selected_metrics_keys_for_render)
