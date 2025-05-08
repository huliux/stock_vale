import streamlit as st
import requests
import pandas as pd
import json
import traceback
import os # 导入 os 以使用 getenv

# --- 配置 ---
API_ENDPOINT = os.getenv("API_ENDPOINT", "http://127.0.0.1:8124/api/v1/valuation") 

# --- 页面配置 ---
st.set_page_config(page_title="股票估值分析工具", layout="wide")

st.title("📈 股票估值分析工具 (DCF + LLM)")
st.caption("结合基本面数据、DCF 模型和 LLM 分析")

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
        target_debt_ratio = st.number_input("目标债务比例 D/(D+E):", min_value=0.0, max_value=1.0, value=0.45, step=0.05, format="%.2f", help="留空则使用默认值", key="wacc_debt_ratio")
        cost_of_debt = st.number_input("税前债务成本 (Rd):", min_value=0.0, value=0.05, step=0.005, format="%.3f", help="留空则使用默认值", key="wacc_cost_debt")
        risk_free_rate = st.number_input("无风险利率 (Rf):", min_value=0.0, value=0.03, step=0.005, format="%.3f", help="留空则使用默认值", key="wacc_rf")
        beta = st.number_input("贝塔系数 (Beta):", value=1.0, step=0.1, format="%.2f", help="留空则使用数据库最新值或默认值", key="wacc_beta")
        market_risk_premium = st.number_input("市场风险溢价 (MRP):", min_value=0.0, value=0.06, step=0.005, format="%.3f", help="留空则使用默认值", key="wacc_mrp")
        # size_premium = st.number_input("规模溢价:", value=0.0, step=0.001, format="%.3f") # 暂时隐藏

    with st.expander("终值计算假设"):
        terminal_value_method = st.selectbox("终值计算方法:", options=['exit_multiple', 'perpetual_growth'], index=0, key="tv_method")
        exit_multiple = st.number_input("退出乘数 (EBITDA):", min_value=0.1, value=8.0, step=0.5, format="%.1f", key="tv_exit_multiple", disabled=(terminal_value_method != 'exit_multiple')) if terminal_value_method == 'exit_multiple' else None
        perpetual_growth_rate = st.number_input("永续增长率:", min_value=0.0, max_value=0.05, value=0.025, step=0.001, format="%.3f", key="tv_pg_rate", disabled=(terminal_value_method != 'perpetual_growth')) if terminal_value_method == 'perpetual_growth' else None

    # --- 触发计算 ---
    # 将按钮移出 sidebar，或者将结果展示部分移出 if 块并在主区域渲染
    # 当前选择将结果展示移出 sidebar
    
    st.divider()
    st.caption("未来功能：情景分析")
    st.info("未来版本将支持对关键假设进行情景分析。")


# --- 函数：渲染估值结果 ---
def render_valuation_results(payload_filtered, current_ts_code):
    st.header("估值结果")
    st.info(f"正在为 {current_ts_code} 请求估值...")
    # st.json(payload_filtered) # 调试时可以取消注释

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

                # 4. LLM 分析与建议区 (移动到末尾)
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
if st.sidebar.button("🚀 开始估值计算", key="start_valuation_button"): # 按钮保留在 sidebar
    # 构建请求体 - 包含所有可能的输入参数
    # 注意：所有输入变量 (ts_code, valuation_date 等) 仍然从 sidebar 中获取
    request_payload = {
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
        "target_debt_ratio": target_debt_ratio,
        "cost_of_debt": cost_of_debt,
        "risk_free_rate": risk_free_rate,
        "beta": beta,
        "market_risk_premium": market_risk_premium,
        # Terminal Value
        "terminal_value_method": terminal_value_method,
        "exit_multiple": exit_multiple,
        "perpetual_growth_rate": perpetual_growth_rate
    }
    # 过滤掉 None 值
    request_payload_filtered = {k: v for k, v in request_payload.items() if v is not None}
    render_valuation_results(request_payload_filtered, ts_code)
