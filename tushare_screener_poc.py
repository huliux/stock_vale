import os
import pandas as pd
import tushare as ts
from dotenv import load_dotenv
from datetime import datetime, timedelta

def run_tushare_poc():
    """
    Tushare Pro API Proof of Concept for Stock Screener.
    - Connects to Tushare Pro API.
    - Fetches stock basic information.
    - Fetches daily basic metrics for a recent trade date.
    - Prints sample data and basic info.
    """
    # Load environment variables from .env file
    load_dotenv()

    # Get Tushare Pro token
    tushare_token = os.getenv("TUSHARE_TOKEN")

    if not tushare_token:
        print("错误：TUSHARE_TOKEN 未在 .env 文件中设置。")
        print("请在项目根目录下创建 .env 文件，并添加 TUSHARE_TOKEN = 'your_token_here'")
        return

    print(f"成功加载 Tushare Token: {tushare_token[:4]}...{tushare_token[-4:]}\n")

    # Initialize Tushare Pro
    try:
        pro = ts.pro_api(tushare_token)
        print("Tushare Pro API 初始化成功。\n")
    except Exception as e:
        print(f"Tushare Pro API 初始化失败: {e}")
        return

    # 1. Fetch stock basic information
    print("正在获取股票基本信息 (stock_basic)...")
    try:
        stock_basic_df = pro.stock_basic(
            list_status='L', 
            fields='ts_code,symbol,name,area,industry,list_date'
        )
        if not stock_basic_df.empty:
            print("成功获取股票基本信息。")
            print(f"获取到 {len(stock_basic_df)} 条股票基本数据。")
            print("前5条数据示例:")
            print(stock_basic_df.head())
            print("\n股票基本信息 DataFrame Info:")
            stock_basic_df.info(verbose=False, memory_usage="deep")
            print("-" * 50 + "\n")
        else:
            print("未能获取到股票基本信息，返回的 DataFrame 为空。")
            print("-" * 50 + "\n")
            return # Exit if stock_basic fails, as daily_basic depends on it for context
    except Exception as e:
        print(f"获取 stock_basic 数据时出错: {e}")
        print("-" * 50 + "\n")
        return

    # 2. Fetch daily basic metrics for a recent trade date
    # Attempt to get the most recent trading day, trying back up to 7 days
    print("正在获取每日行情指标 (daily_basic)...")
    trade_date_to_fetch = None
    for i in range(7):
        date_obj = datetime.now() - timedelta(days=i)
        potential_trade_date = date_obj.strftime('%Y%m%d')
        print(f"尝试获取交易日 {potential_trade_date} 的数据...")
        try:
            # A small test call to check if the date has data
            # Using a common stock to minimize data transfer for the test
            # If stock_basic_df is not empty and has data
            test_ts_code = '000001.SZ' # Default test code
            if not stock_basic_df.empty and 'ts_code' in stock_basic_df.columns and len(stock_basic_df) > 0:
                 test_ts_code = stock_basic_df['ts_code'].iloc[0]
            
            df_check = pro.daily_basic(ts_code=test_ts_code, trade_date=potential_trade_date, fields='ts_code')
            if not df_check.empty:
                trade_date_to_fetch = potential_trade_date
                print(f"找到有效交易日: {trade_date_to_fetch}")
                break
            else:
                print(f"交易日 {potential_trade_date} 无数据，尝试前一天。")
        except Exception as e:
            print(f"检查交易日 {potential_trade_date} 数据时出错: {e}")
            continue
    
    if not trade_date_to_fetch:
        print("错误：过去7天内未能找到有效的交易日数据。请检查Tushare API状态或日期。")
        print("-" * 50 + "\n")
        return

    try:
        daily_basic_df = pro.daily_basic(
            trade_date=trade_date_to_fetch,
            fields='ts_code,trade_date,close,pe,pb,total_mv,circ_mv,dv_ratio,turnover_rate' 
            # Added dv_ratio and turnover_rate for more context, can be removed if not needed
        )
        if not daily_basic_df.empty:
            print(f"成功获取交易日 {trade_date_to_fetch} 的每日行情指标。")
            print(f"获取到 {len(daily_basic_df)} 条每日行情数据。")
            print("前5条数据示例:")
            print(daily_basic_df.head())
            print("\n每日行情指标 DataFrame Info:")
            daily_basic_df.info(verbose=False, memory_usage="deep")
            print("-" * 50 + "\n")
        else:
            print(f"未能获取到交易日 {trade_date_to_fetch} 的每日行情指标，返回的 DataFrame 为空。")
            print("-" * 50 + "\n")
            return
    except Exception as e:
        print(f"获取 daily_basic 数据时出错 (交易日: {trade_date_to_fetch}): {e}")
        print("-" * 50 + "\n")
        return

    # 3. Preliminary data processing test (Optional but recommended)
    print("开始初步数据合并与筛选测试...")
    if not stock_basic_df.empty and not daily_basic_df.empty:
        try:
            # Merge data
            merged_df = pd.merge(stock_basic_df, daily_basic_df, on='ts_code', how='inner')
            print(f"数据合并完成。合并后共有 {len(merged_df)} 条记录。")
            print("合并后数据前5条示例:")
            print(merged_df.head())
            print("\n合并后 DataFrame Info:")
            merged_df.info(verbose=False, memory_usage="deep")
            print("-" * 50 + "\n")

            # Apply a simple filter (e.g., PE < 20 and PB > 0)
            # Ensure 'pe' and 'pb' columns exist and are numeric
            if 'pe' in merged_df.columns and 'pb' in merged_df.columns:
                # Convert to numeric, coercing errors to NaN
                merged_df['pe'] = pd.to_numeric(merged_df['pe'], errors='coerce')
                merged_df['pb'] = pd.to_numeric(merged_df['pb'], errors='coerce')

                # Drop rows where PE or PB could not be converted (became NaN)
                # or if they were non-positive for PB as an example
                filtered_df = merged_df.dropna(subset=['pe', 'pb'])
                filtered_df = filtered_df[(filtered_df['pe'] < 20) & (filtered_df['pe'] > 0) & (filtered_df['pb'] > 0)]
                
                print(f"应用筛选条件 (0 < PE < 20 and PB > 0) 后，剩余 {len(filtered_df)} 条记录。")
                if not filtered_df.empty:
                    print("筛选后数据前5条示例 (ts_code, name, pe, pb, total_mv):")
                    print(filtered_df[['ts_code', 'name', 'pe', 'pb', 'total_mv']].head())
                else:
                    print("没有满足筛选条件的股票。")
            else:
                print("错误: 合并后的 DataFrame 中缺少 'pe' 或 'pb' 列，无法进行筛选。")
            
            print("-" * 50 + "\n")

        except Exception as e:
            print(f"数据合并或筛选时出错: {e}")
            print("-" * 50 + "\n")
    else:
        print("由于 stock_basic 或 daily_basic 数据为空，跳过数据合并与筛选测试。")
        print("-" * 50 + "\n")

    print("Tushare PoC 脚本执行完毕。")

if __name__ == "__main__":
    # For the PoC, we'll directly use the Tushare token provided in the task description.
    # In a real application, this should be securely managed.
    # The .env file should contain: TUSHARE_TOKEN=81eb13f7d031a9b20379eb72ebc057179c709d59549abfb08c78424d
    
    # Create a dummy .env file for PoC if it doesn't exist, using the provided token
    if not os.path.exists(".env"):
        print("检测到 .env 文件不存在，将使用任务描述中提供的Token创建一个临时的 .env 文件用于PoC。")
        with open(".env", "w") as f:
            f.write("TUSHARE_TOKEN=81eb13f7d031a9b20379eb72ebc057179c709d59549abfb08c78424d\n")
            f.write("# 其他环境变量可以放在这里\n")
        print(".env 文件已创建。\n")
    else:
        # Check if TUSHARE_TOKEN is in .env, if not, add it.
        with open(".env", "r+") as f:
            content = f.read()
            if "TUSHARE_TOKEN" not in content:
                print("检测到 .env 文件中缺少 TUSHARE_TOKEN，将添加任务描述中提供的Token。")
                # Append token if not found, ensuring it's on a new line if file not empty
                if content and not content.endswith('\n'):
                    f.write('\n')
                f.write("TUSHARE_TOKEN=81eb13f7d031a9b20379eb72ebc057179c709d59549abfb08c78424d\n")
                print("TUSHARE_TOKEN 已添加到 .env 文件。\n")
            else:
                print(".env 文件已存在且包含 TUSHARE_TOKEN。\n")


    run_tushare_poc()
