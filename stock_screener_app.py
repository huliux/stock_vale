import streamlit as st
import pandas as pd
from stock_screener_data import (
    get_tushare_pro_api,
    get_latest_valid_trade_date,
    load_stock_basic,
    load_daily_basic,
    get_merged_stock_data
)
import os
from datetime import datetime

# --- Page Configuration ---
st.set_page_config(
    page_title="股票筛选器 | A股",
    page_icon="🔎",
    layout="wide"
)

# --- Initialize Tushare API ---
# Cache the API object to avoid re-initializing on every interaction
@st.cache_resource
def init_pro_api():
    return get_tushare_pro_api()

pro = init_pro_api()

# --- State Management ---
if 'latest_trade_date' not in st.session_state:
    st.session_state.latest_trade_date = None
if 'stock_basic_last_update' not in st.session_state:
    st.session_state.stock_basic_last_update = "N/A"
if 'daily_basic_last_update' not in st.session_state:
    st.session_state.daily_basic_last_update = "N/A"
if 'daily_basic_data_date' not in st.session_state:
    st.session_state.daily_basic_data_date = "N/A"
if 'merged_data' not in st.session_state:
    st.session_state.merged_data = pd.DataFrame()
if 'filtered_data' not in st.session_state:
    st.session_state.filtered_data = pd.DataFrame()


def update_data_status():
    """Updates the status of cached data."""
    # Stock Basic
    stock_basic_cache_path = os.path.join("data_cache", "stock_basic.feather")
    if os.path.exists(stock_basic_cache_path):
        st.session_state.stock_basic_last_update = datetime.fromtimestamp(
            os.path.getmtime(stock_basic_cache_path)
        ).strftime('%Y-%m-%d %H:%M:%S')
    else:
        st.session_state.stock_basic_last_update = "无本地缓存"

    # Daily Basic - check for the currently selected/latest trade date
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


# --- Sidebar ---
st.sidebar.title("股票筛选条件")
st.sidebar.markdown("---")

# Initialize latest_trade_date if not already set
if pro and st.session_state.latest_trade_date is None:
    with st.spinner("正在获取最新交易日..."):
        st.session_state.latest_trade_date = get_latest_valid_trade_date(pro)
    update_data_status() # Update status after getting trade date

# Data Update Section
st.sidebar.subheader("数据管理")
if st.sidebar.button("更新股票基础数据", key="update_stock_basic"):
    if pro:
        with st.spinner("正在更新股票基础数据... 请稍候..."):
            load_stock_basic(pro, force_update=True)
        st.sidebar.success("股票基础数据更新完成！")
        update_data_status()
        st.rerun() # Rerun to reflect updated status
    else:
        st.sidebar.error("Tushare API 未初始化。")

# Trade date selection for daily data
selected_trade_date_input = st.sidebar.text_input(
    "行情数据交易日 (YYYYMMDD)", 
    value=st.session_state.latest_trade_date if st.session_state.latest_trade_date else datetime.now().strftime('%Y%m%d'),
    help="输入您想获取行情数据的交易日，默认为最新可获取交易日。"
)

if st.sidebar.button("更新每日行情指标", key="update_daily_basic"):
    if pro and selected_trade_date_input:
        try:
            # Validate date format (basic check)
            datetime.strptime(selected_trade_date_input, '%Y%m%d')
            with st.spinner(f"正在更新交易日 {selected_trade_date_input} 的每日行情指标... 请稍候..."):
                load_daily_basic(pro, selected_trade_date_input, force_update=True)
            st.session_state.latest_trade_date = selected_trade_date_input # Update session state if user inputs a new date
            st.sidebar.success(f"交易日 {selected_trade_date_input} 的每日行情指标更新完成！")
            update_data_status()
            st.rerun()
        except ValueError:
            st.sidebar.error("日期格式无效，请输入 YYYYMMDD 格式。")
    elif not pro:
        st.sidebar.error("Tushare API 未初始化。")
    else:
        st.sidebar.error("请输入有效的交易日期。")


st.sidebar.markdown("---")
st.sidebar.caption(f"股票基础数据最后更新: {st.session_state.stock_basic_last_update}")
st.sidebar.caption(f"每日行情数据日期: {st.session_state.daily_basic_data_date}")
st.sidebar.caption(f"每日行情缓存最后更新: {st.session_state.daily_basic_last_update}")
st.sidebar.markdown("---")


# Filter Criteria
st.sidebar.subheader("筛选指标")
pe_min = st.sidebar.number_input("最低PE (市盈率)", min_value=0.0, value=0.1, step=0.1, format="%.2f")
pe_max = st.sidebar.number_input("最高PE (市盈率)", min_value=0.0, value=30.0, step=1.0, format="%.2f")

pb_min = st.sidebar.number_input("最低PB (市净率)", min_value=0.0, value=0.1, step=0.1, format="%.2f")
pb_max = st.sidebar.number_input("最高PB (市净率)", min_value=0.0, value=3.0, step=0.1, format="%.2f")

market_cap_min_billion = st.sidebar.number_input("最低市值 (亿元)", min_value=0.0, value=50.0, step=10.0, format="%.2f")
market_cap_max_billion = st.sidebar.number_input("最高市值 (亿元)", min_value=0.0, value=10000.0, step=100.0, format="%.2f")

# Market type selection (placeholder for now, can be expanded)
# market_options = ['全部', '主板', '科创板', '创业板']
# selected_market = st.sidebar.selectbox("板块选择", market_options, index=0)

if st.sidebar.button("开始筛选", type="primary", key="filter_stocks"):
    if pro and st.session_state.latest_trade_date:
        with st.spinner("正在加载并合并数据进行筛选..."):
            st.session_state.merged_data = get_merged_stock_data(
                pro, 
                st.session_state.latest_trade_date, # Use the date from session state (which might be updated by user)
                force_update_basic=False, # Usually, don't force update during filtering
                force_update_daily=False
            )
        
        if st.session_state.merged_data is not None and not st.session_state.merged_data.empty:
            df_to_filter = st.session_state.merged_data.copy()
            
            # Apply filters
            # Ensure PE and PB are positive for meaningful filtering
            conditions = (
                (df_to_filter['pe'] >= pe_min) & (df_to_filter['pe'] <= pe_max) & (df_to_filter['pe'] > 0) &
                (df_to_filter['pb'] >= pb_min) & (df_to_filter['pb'] <= pb_max) & (df_to_filter['pb'] > 0) &
                (df_to_filter['market_cap_billion'] >= market_cap_min_billion) &
                (df_to_filter['market_cap_billion'] <= market_cap_max_billion)
            )
            # Add market filter if implemented
            # if selected_market != '全部' and 'market' in df_to_filter.columns:
            #     conditions &= (df_to_filter['market'] == selected_market) # This needs mapping from Tushare market codes

            st.session_state.filtered_data = df_to_filter[conditions]
            st.success(f"筛选完成！找到 {len(st.session_state.filtered_data)} 只符合条件的股票。")
        else:
            st.error("未能加载或合并数据，无法进行筛选。请先尝试更新数据。")
    elif not pro:
        st.error("Tushare API 未初始化。")
    else:
        st.error("未能确定行情数据的交易日，请先更新每日行情指标。")


# --- Main Content Area ---
st.title("A股股票筛选器 🔎")
st.markdown("使用侧边栏设置筛选条件并管理数据，然后点击“开始筛选”。")

if not st.session_state.filtered_data.empty:
    st.subheader(f"筛选结果 ({len(st.session_state.filtered_data)} 只股票)")
    
    # Columns to display - select relevant ones
    display_columns = [
        'ts_code', 'name', 'industry', 'area', 'market',
        'close', 'pe', 'pe_ttm', 'pb', 'ps', 'ps_ttm', 
        'dv_ratio', 'dv_ttm', 
        'market_cap_billion', 'circ_market_cap_billion',
        'turnover_rate', 'turnover_rate_f', 'volume_ratio',
        'total_share', 'float_share', 'free_share',
        'list_date', 'trade_date'
    ]
    # Filter out columns that might not exist if data loading failed partially
    existing_display_columns = [col for col in display_columns if col in st.session_state.filtered_data.columns]
    
    # Define formatting for the columns
    format_dict = {
        'close': "{:.2f}",
        'pe': "{:.2f}",
        'pe_ttm': "{:.2f}",
        'pb': "{:.2f}",
        'ps': "{:.2f}",
        'ps_ttm': "{:.2f}",
        'dv_ratio': "{:.2f}%",
        'dv_ttm': "{:.2f}%",
        'market_cap_billion': "{:,.2f}亿",
        'circ_market_cap_billion': "{:,.2f}亿",
        'turnover_rate': "{:.2f}%",
        'turnover_rate_f': "{:.2f}%",
        'volume_ratio': "{:.2f}",
        'total_share': "{:,.0f}万股",
        'float_share': "{:,.0f}万股",
        'free_share': "{:,.0f}万股",
    }
    # Apply formatting only for existing columns to avoid errors
    active_format_dict = {k: v for k, v in format_dict.items() if k in existing_display_columns}

    st.dataframe(
        st.session_state.filtered_data[existing_display_columns].style.format(active_format_dict), 
        height=600,
        use_container_width=True
    )
elif st.session_state.merged_data is not None and not st.session_state.merged_data.empty and "filter_stocks" in st.session_state and st.session_state.filter_stocks:
    # This condition means filtering was attempted but resulted in no stocks
    st.info("没有找到符合当前筛选条件的股票。请尝试调整筛选范围。")


# Initial data status update on first load
if 'initial_load_done' not in st.session_state:
    update_data_status()
    st.session_state.initial_load_done = True

# For debugging:
# st.subheader("Session State")
# st.json(st.session_state)
