import os
import pandas as pd
import tushare as ts
from dotenv import load_dotenv
from datetime import datetime, timedelta
import streamlit as st # Will be used for st.cache_data later

# Define the cache directory path
CACHE_DIR = "data_cache"

def ensure_cache_dir_exists():
    """Ensures that the cache directory exists."""
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)
        print(f"缓存目录 '{CACHE_DIR}' 已创建。")

def get_tushare_pro_api():
    """
    Initializes and returns the Tushare Pro API interface.
    Returns:
        ts.ProApi: Tushare Pro API object, or None if initialization fails.
    """
    load_dotenv()
    tushare_token = os.getenv("TUSHARE_TOKEN")

    if not tushare_token:
        st.error("错误：TUSHARE_TOKEN 未在 .env 文件中设置。请在项目根目录配置。")
        print("错误：TUSHARE_TOKEN 未在 .env 文件中设置。")
        return None
    
    try:
        pro = ts.pro_api(tushare_token)
        # Perform a simple test call to verify token and connectivity
        pro.trade_cal(exchange='', start_date='20200101', end_date='20200101')
        print("Tushare Pro API 初始化并验证成功。")
        return pro
    except Exception as e:
        st.error(f"Tushare Pro API 初始化或验证失败: {e}")
        print(f"Tushare Pro API 初始化或验证失败: {e}")
        return None

def get_latest_valid_trade_date(pro):
    """
    Gets the most recent valid trading date from Tushare.
    Tries today and goes back up to 7 days.

    Args:
        pro (ts.ProApi): Initialized Tushare Pro API object.

    Returns:
        str: The most recent valid trade date in 'YYYYMMDD' format, or None if not found.
    """
    if pro is None:
        return None
    for i in range(8): # Check today and previous 7 days
        date_obj = datetime.now() - timedelta(days=i)
        potential_trade_date = date_obj.strftime('%Y%m%d')
        try:
            # Check if it's a trading day
            df_cal = pro.trade_cal(exchange='SSE', start_date=potential_trade_date, end_date=potential_trade_date)
            if not df_cal.empty and df_cal['is_open'].iloc[0] == 1:
                # Further check if daily_basic data exists for this day for a common stock
                # This is to handle cases where a day is a trade_cal day but no daily_basic data is published yet
                # (e.g. early morning of a trading day)
                test_ts_code = '000001.SZ' 
                df_check = pro.daily_basic(ts_code=test_ts_code, trade_date=potential_trade_date, fields='ts_code')
                if not df_check.empty:
                    print(f"找到最新的有效交易日: {potential_trade_date}")
                    return potential_trade_date
                else:
                    print(f"交易日 {potential_trade_date} 是交易日，但每日指标数据尚未发布，尝试前一天。")
            else:
                 print(f"日期 {potential_trade_date} 不是交易日或交易所未开放，尝试前一天。")
        except Exception as e:
            print(f"检查交易日 {potential_trade_date} 时出错: {e}")
            continue
    st.warning("过去7天内未能找到有效的交易日数据。请稍后再试或检查API状态。")
    print("错误：过去7天内未能找到有效的交易日数据。")
    return None

def load_stock_basic(pro, force_update=False):
    """
    Loads stock basic information from cache or Tushare API.

    Args:
        pro (ts.ProApi): Initialized Tushare Pro API object.
        force_update (bool): If True, always fetch from API and update cache.

    Returns:
        pd.DataFrame: DataFrame containing stock basic information, or None if an error occurs.
    """
    if pro is None:
        st.error("Tushare API 未初始化，无法加载股票基本信息。")
        return None

    cache_file_path = os.path.join(CACHE_DIR, "stock_basic.feather")
    
    if not force_update and os.path.exists(cache_file_path):
        try:
            df = pd.read_feather(cache_file_path)
            print(f"从缓存文件 '{cache_file_path}' 加载股票基本信息。")
            # Add a column for last updated time based on file modification
            last_updated_timestamp = os.path.getmtime(cache_file_path)
            df['last_updated_local'] = datetime.fromtimestamp(last_updated_timestamp).strftime('%Y-%m-%d %H:%M:%S')
            return df
        except Exception as e:
            print(f"从缓存文件 '{cache_file_path}' 加载股票基本信息失败: {e}。将尝试从API获取。")

    print("正在从 Tushare API 获取股票基本信息 (stock_basic)...")
    try:
        stock_basic_df = pro.stock_basic(
            list_status='L',
            fields='ts_code,symbol,name,area,industry,list_date,market,exchange' # Added market and exchange
        )
        if not stock_basic_df.empty:
            print(f"成功从 API 获取 {len(stock_basic_df)} 条股票基本数据。")
            ensure_cache_dir_exists() # Ensure cache dir exists before saving
            stock_basic_df.to_feather(cache_file_path)
            print(f"股票基本信息已缓存到 '{cache_file_path}'。")
            # Add a column for last updated time
            last_updated_timestamp = os.path.getmtime(cache_file_path)
            stock_basic_df['last_updated_local'] = datetime.fromtimestamp(last_updated_timestamp).strftime('%Y-%m-%d %H:%M:%S')
            return stock_basic_df
        else:
            st.warning("未能从 Tushare API 获取到股票基本信息，返回的 DataFrame 为空。")
            print("未能从 Tushare API 获取到股票基本信息，返回的 DataFrame 为空。")
            return None
    except Exception as e:
        st.error(f"从 Tushare API 获取 stock_basic 数据时出错: {e}")
        print(f"从 Tushare API 获取 stock_basic 数据时出错: {e}")
        return None

def load_daily_basic(pro, trade_date, force_update=False):
    """
    Loads daily basic metrics for a specific trade date from cache or Tushare API.

    Args:
        pro (ts.ProApi): Initialized Tushare Pro API object.
        trade_date (str): The trade date in 'YYYYMMDD' format.
        force_update (bool): If True, always fetch from API and update cache.

    Returns:
        pd.DataFrame: DataFrame containing daily basic metrics, or None if an error occurs.
    """
    if pro is None:
        st.error("Tushare API 未初始化，无法加载每日行情指标。")
        return None
    if not trade_date:
        st.error("未提供交易日期，无法加载每日行情指标。")
        return None

    cache_file_name = f"daily_basic_{trade_date}.feather"
    cache_file_path = os.path.join(CACHE_DIR, cache_file_name)

    if not force_update and os.path.exists(cache_file_path):
        try:
            df = pd.read_feather(cache_file_path)
            print(f"从缓存文件 '{cache_file_path}' 加载交易日 {trade_date} 的每日行情指标。")
            last_updated_timestamp = os.path.getmtime(cache_file_path)
            df['last_updated_local'] = datetime.fromtimestamp(last_updated_timestamp).strftime('%Y-%m-%d %H:%M:%S')
            df['data_trade_date'] = trade_date # Add a column for the data's trade date
            return df
        except Exception as e:
            print(f"从缓存文件 '{cache_file_path}' 加载每日行情指标失败: {e}。将尝试从API获取。")

    print(f"正在从 Tushare API 获取交易日 {trade_date} 的每日行情指标 (daily_basic)...")
    try:
        daily_basic_fields = 'ts_code,trade_date,close,turnover_rate,turnover_rate_f,volume_ratio,pe,pe_ttm,pb,ps,ps_ttm,dv_ratio,dv_ttm,total_share,float_share,free_share,total_mv,circ_mv'
        daily_basic_df = pro.daily_basic(
            trade_date=trade_date,
            fields=daily_basic_fields
        )
        if not daily_basic_df.empty:
            print(f"成功从 API 获取交易日 {trade_date} 的 {len(daily_basic_df)} 条每日行情数据。")
            ensure_cache_dir_exists()
            daily_basic_df.to_feather(cache_file_path)
            print(f"每日行情指标已缓存到 '{cache_file_path}'。")
            last_updated_timestamp = os.path.getmtime(cache_file_path)
            daily_basic_df['last_updated_local'] = datetime.fromtimestamp(last_updated_timestamp).strftime('%Y-%m-%d %H:%M:%S')
            daily_basic_df['data_trade_date'] = trade_date # Add a column for the data's trade date
            return daily_basic_df
        else:
            st.warning(f"未能从 Tushare API 获取到交易日 {trade_date} 的每日行情指标，返回的 DataFrame 为空。")
            print(f"未能从 Tushare API 获取到交易日 {trade_date} 的每日行情指标，返回的 DataFrame 为空。")
            # Return an empty DataFrame with expected columns if API returns empty, to avoid downstream errors if needed
            # However, for this function, returning None might be better to signal data unavailability.
            return None
    except Exception as e:
        st.error(f"从 Tushare API 获取 daily_basic 数据时出错 (交易日: {trade_date}): {e}")
        print(f"从 Tushare API 获取 daily_basic 数据时出错 (交易日: {trade_date}): {e}")
        return None

def get_merged_stock_data(pro, trade_date, force_update_basic=False, force_update_daily=False):
    """
    Loads, merges, and pre-processes stock_basic and daily_basic data.

    Args:
        pro (ts.ProApi): Initialized Tushare Pro API object.
        trade_date (str): The trade date for daily_basic data in 'YYYYMMDD' format.
        force_update_basic (bool): Force update for stock_basic data.
        force_update_daily (bool): Force update for daily_basic data for the given trade_date.

    Returns:
        pd.DataFrame: Merged and pre-processed DataFrame, or None if an error occurs.
    """
    if pro is None or not trade_date:
        st.error("API未初始化或未提供交易日期，无法获取合并数据。")
        return None

    df_basic = load_stock_basic(pro, force_update=force_update_basic)
    if df_basic is None or df_basic.empty:
        st.warning("未能加载股票基本信息，无法进行合并。")
        return None

    df_daily = load_daily_basic(pro, trade_date, force_update=force_update_daily)
    if df_daily is None or df_daily.empty:
        st.warning(f"未能加载交易日 {trade_date} 的每日行情数据，无法进行合并。")
        return None

    print(f"开始合并 {len(df_basic)} 条股票基本信息和 {len(df_daily)} 条每日行情数据 (交易日: {trade_date})...")
    try:
        # Ensure 'ts_code' is string type in both dataframes before merging
        df_basic['ts_code'] = df_basic['ts_code'].astype(str)
        df_daily['ts_code'] = df_daily['ts_code'].astype(str)
        
        merged_df = pd.merge(df_basic, df_daily, on='ts_code', how='inner', suffixes=('_basic', '_daily'))
        print(f"数据合并完成。合并后共有 {len(merged_df)} 条记录。")

        # --- Data Pre-processing ---
        # Rename columns for clarity if needed (e.g., if 'trade_date_daily' exists)
        if 'trade_date_daily' in merged_df.columns:
            merged_df.rename(columns={'trade_date_daily': 'trade_date'}, inplace=True)
        elif 'trade_date_x' in merged_df.columns: # Suffixes might create _x, _y
             merged_df.rename(columns={'trade_date_x': 'trade_date'}, inplace=True)


        # Convert key financial metrics to numeric, coercing errors to NaN
        metrics_to_convert = [
            'close', 'turnover_rate', 'turnover_rate_f', 'volume_ratio', 
            'pe', 'pe_ttm', 'pb', 'ps', 'ps_ttm', 'dv_ratio', 'dv_ttm',
            'total_share', 'float_share', 'free_share', 'total_mv', 'circ_mv'
        ]
        for metric in metrics_to_convert:
            if metric in merged_df.columns:
                merged_df[metric] = pd.to_numeric(merged_df[metric], errors='coerce')
            else:
                # This case should ideally not happen if fields are correctly requested and merged
                print(f"警告: 列 '{metric}' 在合并后的DataFrame中不存在，跳过转换。")
        
        # Add a 'market_cap_billion' column for easier filtering (total_mv is in 万 RMB)
        if 'total_mv' in merged_df.columns:
            merged_df['market_cap_billion'] = merged_df['total_mv'] / 10000 # Convert 万 RMB to 亿 RMB
        
        if 'circ_mv' in merged_df.columns:
            merged_df['circ_market_cap_billion'] = merged_df['circ_mv'] / 10000 # Convert 万 RMB to 亿 RMB


        print("数据预处理完成 (指标转换为数值型，市值单位转换)。")
        print("合并和预处理后的数据前5条示例:")
        print(merged_df.head())
        return merged_df

    except Exception as e:
        st.error(f"数据合并或预处理时出错: {e}")
        print(f"数据合并或预处理时出错: {e}")
        return None

# Ensure cache directory exists when this module is loaded
ensure_cache_dir_exists()

if __name__ == '__main__':
    # Test functions
    print("正在测试 stock_screener_data.py 模块功能...")
    
    # Create a dummy .env file for PoC if it doesn't exist, using the provided token
    if not os.path.exists(".env"):
        print("检测到 .env 文件不存在，将使用任务描述中提供的Token创建一个临时的 .env 文件用于测试。")
        with open(".env", "w") as f:
            f.write("TUSHARE_TOKEN=81eb13f7d031a9b20379eb72ebc057179c709d59549abfb08c78424d\n")
        print(".env 文件已创建。\n")
    else:
        with open(".env", "r+") as f:
            content = f.read()
            if "TUSHARE_TOKEN" not in content:
                print("检测到 .env 文件中缺少 TUSHARE_TOKEN，将添加任务描述中提供的Token。")
                if content and not content.endswith('\n'):
                    f.write('\n')
                f.write("TUSHARE_TOKEN=81eb13f7d031a9b20379eb72ebc057179c709d59549abfb08c78424d\n")
                print("TUSHARE_TOKEN 已添加到 .env 文件。\n")

    pro_api = get_tushare_pro_api()
    if pro_api:
        print("\n测试获取最新有效交易日...")
        latest_date = get_latest_valid_trade_date(pro_api)
        if latest_date:
            print(f"获取到的最新有效交易日是: {latest_date}")
        else:
            print("未能获取到最新有效交易日。")

        print("\n测试加载股票基本信息 (首次加载)...")
        df_basic_first = load_stock_basic(pro_api, force_update=True) # Force update for first test
        if df_basic_first is not None:
            print(f"首次加载成功，共 {len(df_basic_first)} 条数据。")
            # print(df_basic_first.head(3))
            # if 'last_updated_local' in df_basic_first.columns:
            #      print(f"数据最后更新于 (本地文件时间): {df_basic_first['last_updated_local'].iloc[0]}")

        print("\n测试加载股票基本信息 (从缓存加载)...")
        df_basic_cached = load_stock_basic(pro_api, force_update=False)
        if df_basic_cached is not None:
            print(f"从缓存加载成功，共 {len(df_basic_cached)} 条数据。")
            # print(df_basic_cached.head(3))
            # if 'last_updated_local' in df_basic_cached.columns:
            #      print(f"数据最后更新于 (本地文件时间): {df_basic_cached['last_updated_local'].iloc[0]}")

        if latest_date:
            print(f"\n测试加载交易日 {latest_date} 的每日行情指标 (首次加载)...")
            df_daily_first = load_daily_basic(pro_api, latest_date, force_update=True)
            if df_daily_first is not None:
                print(f"首次加载每日行情成功，共 {len(df_daily_first)} 条数据。")
                # print(df_daily_first.head(3))
                # if 'last_updated_local' in df_daily_first.columns:
                #     print(f"数据最后更新于 (本地文件时间): {df_daily_first['last_updated_local'].iloc[0]}")
                # if 'data_trade_date' in df_daily_first.columns:
                #     print(f"数据对应的交易日: {df_daily_first['data_trade_date'].iloc[0]}")


            print(f"\n测试加载交易日 {latest_date} 的每日行情指标 (从缓存加载)...")
            df_daily_cached = load_daily_basic(pro_api, latest_date, force_update=False)
            if df_daily_cached is not None:
                print(f"从缓存加载每日行情成功，共 {len(df_daily_cached)} 条数据。")
                # print(df_daily_cached.head(3))
                # if 'last_updated_local' in df_daily_cached.columns:
                #     print(f"数据最后更新于 (本地文件时间): {df_daily_cached['last_updated_local'].iloc[0]}")
                # if 'data_trade_date' in df_daily_cached.columns:
                #     print(f"数据对应的交易日: {df_daily_cached['data_trade_date'].iloc[0]}")
            
            print(f"\n测试获取合并后的股票数据 (交易日: {latest_date})...")
            # For testing, force update both to ensure fresh data merge
            merged_data = get_merged_stock_data(pro_api, latest_date, force_update_basic=True, force_update_daily=True)
            if merged_data is not None and not merged_data.empty:
                print(f"成功获取并合并数据，共 {len(merged_data)} 条记录。")
                print("合并后数据的前3行:")
                print(merged_data.head(3))
                print("\n合并后数据的列信息:")
                merged_data.info(verbose=False)
                
                # Test a simple filter
                if 'pe' in merged_data.columns and 'market_cap_billion' in merged_data.columns:
                    filtered_sample = merged_data[(merged_data['pe'] > 0) & (merged_data['pe'] < 10) & (merged_data['market_cap_billion'] > 100)]
                    print(f"\n应用筛选条件 (0 < PE < 10 and 市值 > 100亿) 后，示例剩余 {len(filtered_sample)} 条记录。")
                    if not filtered_sample.empty:
                        print(filtered_sample[['ts_code', 'name', 'pe', 'pb', 'market_cap_billion']].head())
                    else:
                        print("没有满足示例筛选条件的股票。")
            else:
                print("未能获取或合并数据。")

        else:
            print("\n未能获取到最新有效交易日，跳过每日行情指标加载和合并数据测试。")

    else:
        print("未能初始化 Tushare Pro API，跳过后续测试。")
    
    print("\nstock_screener_data.py 模块功能测试完毕。")
