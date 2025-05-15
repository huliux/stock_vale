import os
import pandas as pd
import tushare as ts
from dotenv import load_dotenv
from datetime import datetime, timedelta
import logging

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO) # Or use FastAPI's logger configuration

# Define the cache directory path relative to this file's package (services)
# Assuming cache should be at packages/fastapi-backend/data_cache_backend
# __file__ is services/stock_screener_service.py
# os.path.dirname(__file__) is services/
# os.path.join(os.path.dirname(__file__), "..") is fastapi-backend/
CACHE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data_cache_backend"))

class StockScreenerServiceError(Exception):
    """Custom exception for errors in the stock screener service."""
    pass

def ensure_cache_dir_exists():
    """Ensures that the cache directory exists."""
    if not os.path.exists(CACHE_DIR):
        try:
            os.makedirs(CACHE_DIR)
            logger.info(f"缓存目录 '{CACHE_DIR}' 已创建。")
        except OSError as e:
            logger.error(f"创建缓存目录 '{CACHE_DIR}' 失败: {e}")
            raise StockScreenerServiceError(f"无法创建缓存目录: {CACHE_DIR}")


# Ensure cache directory exists when this module is loaded
# This might be better called explicitly or handled by a setup function
# For now, let's call it here. If it fails, subsequent operations will fail.
try:
    ensure_cache_dir_exists()
except StockScreenerServiceError:
    logger.critical("Stock Screener Service 无法初始化缓存目录，服务可能无法正常工作。")
    # Depending on desired behavior, could re-raise or set a global error state.


# Load .env file from the fastapi-backend directory or project root if not already loaded
# Assuming .env is in packages/fastapi-backend or the project root
dotenv_path_backend = os.path.join(os.path.dirname(__file__), "..", ".env")
dotenv_path_root = os.path.join(os.path.dirname(__file__), "..", "..", ".env") # Project root

if os.path.exists(dotenv_path_backend):
    load_dotenv(dotenv_path=dotenv_path_backend, override=True)
    logger.info(f".env file loaded from {dotenv_path_backend}")
elif os.path.exists(dotenv_path_root):
    load_dotenv(dotenv_path=dotenv_path_root, override=True)
    logger.info(f".env file loaded from {dotenv_path_root}")
else:
    logger.warning(".env file not found in standard locations (packages/fastapi-backend/ or project root). TUSHARE_TOKEN might not be available.")


_pro_api_instance = None

def get_tushare_pro_api():
    """
    Initializes and returns the Tushare Pro API interface.
    Uses a module-level singleton to avoid re-initialization.
    Returns:
        ts.ProApi: Tushare Pro API object.
    Raises:
        StockScreenerServiceError: If initialization fails.
    """
    global _pro_api_instance
    if _pro_api_instance is not None:
        return _pro_api_instance

    tushare_token = os.getenv("TUSHARE_TOKEN")

    if not tushare_token:
        logger.error("错误：TUSHARE_TOKEN 未在 .env 文件中设置。")
        raise StockScreenerServiceError("TUSHARE_TOKEN 未配置。")
    
    try:
        pro = ts.pro_api(tushare_token)
        # Perform a simple test call to verify token and connectivity
        pro.trade_cal(exchange='', start_date='20200101', end_date='20200101')
        logger.info("Tushare Pro API 初始化并验证成功。")
        _pro_api_instance = pro
        return _pro_api_instance
    except Exception as e:
        logger.error(f"Tushare Pro API 初始化或验证失败: {e}")
        raise StockScreenerServiceError(f"Tushare Pro API 初始化失败: {e}")

def get_latest_valid_trade_date():
    """
    Gets the most recent valid trading date from Tushare.
    Tries today and goes back up to 7 days.

    Returns:
        str: The most recent valid trade date in 'YYYYMMDD' format.
    Raises:
        StockScreenerServiceError: If API is not initialized or no valid date is found.
    """
    pro = get_tushare_pro_api() # Ensures API is initialized
    
    for i in range(8): # Check today and previous 7 days
        date_obj = datetime.now() - timedelta(days=i)
        potential_trade_date = date_obj.strftime('%Y%m%d')
        try:
            df_cal = pro.trade_cal(exchange='SSE', start_date=potential_trade_date, end_date=potential_trade_date)
            if not df_cal.empty and df_cal['is_open'].iloc[0] == 1:
                test_ts_code = '000001.SZ' 
                df_check = pro.daily_basic(ts_code=test_ts_code, trade_date=potential_trade_date, fields='ts_code')
                if not df_check.empty:
                    logger.info(f"找到最新的有效交易日: {potential_trade_date}")
                    return potential_trade_date
                else:
                    logger.info(f"交易日 {potential_trade_date} 是交易日，但每日指标数据尚未发布，尝试前一天。")
            else:
                 logger.info(f"日期 {potential_trade_date} 不是交易日或交易所未开放，尝试前一天。")
        except Exception as e:
            logger.warning(f"检查交易日 {potential_trade_date} 时出错: {e}")
            continue
    
    logger.error("过去7天内未能找到有效的交易日数据。")
    raise StockScreenerServiceError("过去7天内未能找到有效的交易日数据。")


def load_stock_basic(force_update=False):
    """
    Loads stock basic information from cache or Tushare API.

    Args:
        force_update (bool): If True, always fetch from API and update cache.

    Returns:
        pd.DataFrame: DataFrame containing stock basic information.
    Raises:
        StockScreenerServiceError: If an error occurs.
    """
    pro = get_tushare_pro_api()
    cache_file_path = os.path.join(CACHE_DIR, "stock_basic.feather")
    
    if not force_update and os.path.exists(cache_file_path):
        try:
            df = pd.read_feather(cache_file_path)
            logger.info(f"从缓存文件 '{cache_file_path}' 加载股票基本信息。")
            # last_updated_timestamp = os.path.getmtime(cache_file_path)
            # df['last_updated_local'] = datetime.fromtimestamp(last_updated_timestamp).strftime('%Y-%m-%d %H:%M:%S')
            return df
        except Exception as e:
            logger.warning(f"从缓存文件 '{cache_file_path}' 加载股票基本信息失败: {e}。将尝试从API获取。")

    logger.info("正在从 Tushare API 获取股票基本信息 (stock_basic)...")
    try:
        stock_basic_df = pro.stock_basic(
            list_status='L',
            fields='ts_code,symbol,name,area,industry,list_date,market,exchange'
        )
        if not stock_basic_df.empty:
            logger.info(f"成功从 API 获取 {len(stock_basic_df)} 条股票基本数据。")
            stock_basic_df.to_feather(cache_file_path) # ensure_cache_dir_exists called at module load
            logger.info(f"股票基本信息已缓存到 '{cache_file_path}'。")
            return stock_basic_df
        else:
            logger.warning("未能从 Tushare API 获取到股票基本信息，返回的 DataFrame 为空。")
            raise StockScreenerServiceError("未能从API获取股票基本信息。")
    except Exception as e:
        logger.error(f"从 Tushare API 获取 stock_basic 数据时出错: {e}")
        raise StockScreenerServiceError(f"获取 stock_basic API数据出错: {e}")

def load_daily_basic(trade_date, force_update=False):
    """
    Loads daily basic metrics for a specific trade date from cache or Tushare API.

    Args:
        trade_date (str): The trade date in 'YYYYMMDD' format.
        force_update (bool): If True, always fetch from API and update cache.

    Returns:
        pd.DataFrame: DataFrame containing daily basic metrics.
    Raises:
        StockScreenerServiceError: If an error occurs.
    """
    pro = get_tushare_pro_api()
    if not trade_date:
        logger.error("未提供交易日期，无法加载每日行情指标。")
        raise StockScreenerServiceError("未提供交易日期。")

    cache_file_name = f"daily_basic_{trade_date}.feather"
    cache_file_path = os.path.join(CACHE_DIR, cache_file_name)

    if not force_update and os.path.exists(cache_file_path):
        try:
            df = pd.read_feather(cache_file_path)
            logger.info(f"从缓存文件 '{cache_file_path}' 加载交易日 {trade_date} 的每日行情指标。")
            # df['data_trade_date'] = trade_date 
            return df
        except Exception as e:
            logger.warning(f"从缓存文件 '{cache_file_path}' 加载每日行情指标失败: {e}。将尝试从API获取。")

    logger.info(f"正在从 Tushare API 获取交易日 {trade_date} 的每日行情指标 (daily_basic)...")
    try:
        daily_basic_fields = 'ts_code,trade_date,close,turnover_rate,turnover_rate_f,volume_ratio,pe,pe_ttm,pb,ps,ps_ttm,dv_ratio,dv_ttm,total_share,float_share,free_share,total_mv,circ_mv'
        daily_basic_df = pro.daily_basic(
            trade_date=trade_date,
            fields=daily_basic_fields
        )
        if not daily_basic_df.empty:
            logger.info(f"成功从 API 获取交易日 {trade_date} 的 {len(daily_basic_df)} 条每日行情数据。")
            daily_basic_df.to_feather(cache_file_path)
            logger.info(f"每日行情指标已缓存到 '{cache_file_path}'。")
            return daily_basic_df
        else:
            logger.warning(f"未能从 Tushare API 获取到交易日 {trade_date} 的每日行情指标，返回的 DataFrame 为空。")
            raise StockScreenerServiceError(f"未能从API获取交易日 {trade_date} 的每日行情指标。")
    except Exception as e:
        logger.error(f"从 Tushare API 获取 daily_basic 数据时出错 (交易日: {trade_date}): {e}")
        raise StockScreenerServiceError(f"获取 daily_basic API数据出错 (交易日: {trade_date}): {e}")

def get_merged_stock_data(trade_date, force_update_basic=False, force_update_daily=False):
    """
    Loads, merges, and pre-processes stock_basic and daily_basic data.

    Args:
        trade_date (str): The trade date for daily_basic data in 'YYYYMMDD' format.
        force_update_basic (bool): Force update for stock_basic data.
        force_update_daily (bool): Force update for daily_basic data for the given trade_date.

    Returns:
        pd.DataFrame: Merged and pre-processed DataFrame.
    Raises:
        StockScreenerServiceError: If an error occurs.
    """
    if not trade_date: # pro is fetched by called functions
        logger.error("未提供交易日期，无法获取合并数据。")
        raise StockScreenerServiceError("未提供交易日期以获取合并数据。")

    df_basic = load_stock_basic(force_update=force_update_basic)
    df_daily = load_daily_basic(trade_date, force_update=force_update_daily)

    logger.info(f"开始合并 {len(df_basic)} 条股票基本信息和 {len(df_daily)} 条每日行情数据 (交易日: {trade_date})...")
    try:
        df_basic['ts_code'] = df_basic['ts_code'].astype(str)
        df_daily['ts_code'] = df_daily['ts_code'].astype(str)
        
        merged_df = pd.merge(df_basic, df_daily, on='ts_code', how='inner', suffixes=('_basic', '_daily'))
        logger.info(f"数据合并完成。合并后共有 {len(merged_df)} 条记录。")
        
        # Log some sample data after merge, before rename and conversion
        if not merged_df.empty:
            logger.info(f"合并后数据样本 (前5行，关注 close, total_mv, ts_code):\n{merged_df[['ts_code', 'name', 'close', 'total_mv']].head()}")

        if 'trade_date_daily' in merged_df.columns:
            merged_df.rename(columns={'trade_date_daily': 'trade_date'}, inplace=True)
        elif 'trade_date_x' in merged_df.columns:
             merged_df.rename(columns={'trade_date_x': 'trade_date'}, inplace=True)

        metrics_to_convert = [
            'close', 'turnover_rate', 'turnover_rate_f', 'volume_ratio', 
            'pe', 'pe_ttm', 'pb', 'ps', 'ps_ttm', 'dv_ratio', 'dv_ttm',
            'total_share', 'float_share', 'free_share', 'total_mv', 'circ_mv'
        ]
        for metric in metrics_to_convert:
            if metric in merged_df.columns:
                # Log before conversion for problematic columns
                if metric in ['close', 'total_mv'] and not merged_df.empty:
                    logger.info(f"列 '{metric}' 转换前数据样本 (前5行):\n{merged_df[['ts_code', 'name', metric]].head()}")
                merged_df[metric] = pd.to_numeric(merged_df[metric], errors='coerce')
                # Log after conversion for problematic columns
                if metric in ['close', 'total_mv'] and not merged_df.empty:
                    logger.info(f"列 '{metric}' 转换后数据样本 (前5行):\n{merged_df[['ts_code', 'name', metric]].head()}")
                    # Check for NaNs introduced by conversion
                    if merged_df[metric].isnull().any():
                        logger.warning(f"列 '{metric}' 在 to_numeric 转换后包含 NaN 值。")
            else:
                logger.warning(f"警告: 列 '{metric}' 在合并后的DataFrame中不存在，跳过转换。")
        
        if 'total_mv' in merged_df.columns:
            merged_df['market_cap_billion'] = merged_df['total_mv'] / 10000 
            if not merged_df.empty:
                 logger.info(f"列 'market_cap_billion' 计算后数据样本 (前5行):\n{merged_df[['ts_code', 'name', 'total_mv', 'market_cap_billion']].head()}")
        
        if 'circ_mv' in merged_df.columns:
            merged_df['circ_market_cap_billion'] = merged_df['circ_mv'] / 10000

        logger.info("数据预处理完成 (指标转换为数值型，市值单位转换)。")
        
        # Log final sample data for the relevant columns before returning
        if not merged_df.empty:
            logger.info(f"返回前最终数据样本 (前5行，关注 close, market_cap_billion, ts_code):\n{merged_df[['ts_code', 'name', 'close', 'market_cap_billion']].head()}")
            
            # Specifically check if 'close' or 'market_cap_billion' are all NaN for some reason
            if merged_df['close'].isnull().all():
                logger.error("错误：处理后 'close' 列全部为 NaN。")
            if 'market_cap_billion' in merged_df.columns and merged_df['market_cap_billion'].isnull().all():
                logger.error("错误：处理后 'market_cap_billion' 列全部为 NaN。")
            elif 'market_cap_billion' not in merged_df.columns:
                 logger.error("错误：处理后 'market_cap_billion' 列不存在。")


        return merged_df

    except Exception as e:
        logger.error(f"数据合并或预处理时出错: {e}")
        raise StockScreenerServiceError(f"数据合并或预处理时出错: {e}")

# Example test logic (can be run if this file is executed directly)
if __name__ == '__main__':
    logger.info("正在测试 stock_screener_service.py 模块功能...")
    
    # Ensure .env is loaded for testing (assuming it's in project root or fastapi-backend)
    # The module-level load_dotenv should handle this.
    
    try:
        pro = get_tushare_pro_api() # Test API initialization
        
        logger.info("\n测试获取最新有效交易日...")
        latest_date = get_latest_valid_trade_date()
        logger.info(f"获取到的最新有效交易日是: {latest_date}")

        logger.info("\n测试加载股票基本信息 (强制更新)...")
        df_basic_first = load_stock_basic(force_update=True)
        logger.info(f"首次加载成功，共 {len(df_basic_first)} 条数据。")

        logger.info("\n测试加载股票基本信息 (从缓存加载)...")
        df_basic_cached = load_stock_basic(force_update=False)
        logger.info(f"从缓存加载成功，共 {len(df_basic_cached)} 条数据。")

        logger.info(f"\n测试加载交易日 {latest_date} 的每日行情指标 (强制更新)...")
        df_daily_first = load_daily_basic(latest_date, force_update=True)
        logger.info(f"首次加载每日行情成功，共 {len(df_daily_first)} 条数据。")

        logger.info(f"\n测试加载交易日 {latest_date} 的每日行情指标 (从缓存加载)...")
        df_daily_cached = load_daily_basic(latest_date, force_update=False)
        logger.info(f"从缓存加载每日行情成功，共 {len(df_daily_cached)} 条数据。")
        
        logger.info(f"\n测试获取合并后的股票数据 (交易日: {latest_date})...")
        merged_data = get_merged_stock_data(latest_date, force_update_basic=True, force_update_daily=True)
        if not merged_data.empty:
            logger.info(f"成功获取并合并数据，共 {len(merged_data)} 条记录。")
            logger.info("合并后数据的前3行:")
            logger.info(merged_data.head(3))
            
            if 'pe_ttm' in merged_data.columns and 'market_cap_billion' in merged_data.columns:
                filtered_sample = merged_data[(merged_data['pe_ttm'].notna()) & (merged_data['pe_ttm'] > 0) & (merged_data['pe_ttm'] < 10) & (merged_data['market_cap_billion'].notna()) & (merged_data['market_cap_billion'] > 100)]
                logger.info(f"\n应用筛选条件 (0 < PE_TTM < 10 and 市值 > 100亿) 后，示例剩余 {len(filtered_sample)} 条记录。")
                if not filtered_sample.empty:
                    logger.info(filtered_sample[['ts_code', 'name', 'pe_ttm', 'pb', 'market_cap_billion']].head())
                else:
                    logger.info("没有满足示例筛选条件的股票。")
        else:
            logger.error("未能获取或合并数据。")

    except StockScreenerServiceError as se:
        logger.error(f"服务层错误: {se}")
    except Exception as ex:
        logger.error(f"测试过程中发生意外错误: {ex}")
    
    logger.info("\nstock_screener_service.py 模块功能测试完毕。")
