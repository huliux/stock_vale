import argparse
import argparse
import matplotlib
from data_fetcher import DataFetcher
from valuation_calculator import ValuationCalculator
from report_generator import ReportGenerator
from models.stock_data import StockData  # 导入 StockData 类

matplotlib.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
matplotlib.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='股票绝对估值计算工具')
    # 使用从 config.ini.example 获取的默认值
    parser.add_argument('--stock', type=str, help='股票代码，例如：600519.SH', default='600519.SH')
    parser.add_argument('--pe', type=str, help='PE估值倍数，用逗号分隔，例如：5,8,12', default='5,8,12')
    parser.add_argument('--pb', type=str, help='PB估值倍数，用逗号分隔，例如：0.8,1.2,1.5', default='0.8,1.2,1.5')
    parser.add_argument('--growth', type=str, help='增长率，用逗号分隔，例如：0.05,0.08,0.1', default='0.05,0.08,0.1')
    parser.add_argument('--discount', type=str, help='折现率，用逗号分隔，例如：0.1,0.12,0.15', default='0.1,0.12,0.15')
    parser.add_argument('--ev-ebitda', type=str, help='EV/EBITDA倍数，用逗号分隔，例如：6,8,10', default='6,8,10')
    parser.add_argument('--html', action='store_true', help='生成HTML格式报告')

    return parser.parse_args()

# 不再需要 read_config 函数

def main():
    """主程序入口"""
    args = parse_arguments() # 不再需要 config
    
    # 解析参数
    pe_range = args.pe.split(',')
    pb_range = args.pb.split(',')
    growth_rates = args.growth.split(',')
    discount_rates = args.discount.split(',')
    ev_ebitda_range = args.ev_ebitda.split(',')
    
    # 获取数据
    data_fetcher = DataFetcher(args.stock)
    stock_info = data_fetcher.get_stock_info()
    latest_price = data_fetcher.get_latest_price()
    total_shares = data_fetcher.get_total_shares()
    financials = data_fetcher.get_financial_data()
    dividends = data_fetcher.get_dividend_data()
    market_cap = latest_price * total_shares / 100000000  # 转为亿元
    
    # 计算估值
    calculator = ValuationCalculator(
        stock_info=stock_info,
        latest_price=latest_price,
        total_shares=total_shares,
        financials=financials,
        dividends=dividends,
        market_cap=market_cap
    )
    
    # 确保所有计算结果不为 None
    pe_history = calculator.calculate_pe_ratio() or 0
    pb_history = calculator.calculate_pb_ratio() or 0
    income_growth, revenue_growth, cagr = calculator.calculate_growth_rate()
    latest_fcff, latest_fcfe, fcff_history, fcfe_history = calculator.calculate_fcff_fcfe()
    enterprise_value, ebitda, ev_to_ebitda = calculator.calculate_ev() or (0, 0, 0)
    current_yield, dividend_history, avg_div, payout_ratio = calculator.calculate_dividend_yield() or (0, [], 0, 0)
    ddm_vals, _ = calculator.calculate_ddm_valuation(growth_rates, discount_rates) or ([], "")
    fcff_full_vals, _ = calculator.perform_fcff_valuation_full_capex(growth_rates, discount_rates) or ([], "")
    fcfe_full_vals, _ = calculator.perform_fcfe_valuation_full_capex(growth_rates, discount_rates) or ([], "")
    fcfe_vals, _ = calculator.perform_fcfe_valuation_adjusted(growth_rates, discount_rates) or ([], "")
    fcff_vals, _ = calculator.perform_fcff_valuation_adjusted(growth_rates, discount_rates) or ([], "")
    
    # 创建 StockData 对象
    stock_data = StockData(
        stock_info=stock_info,
        latest_price=latest_price,
        total_shares=total_shares,
        market_cap=market_cap,
        pe_history=pe_history,
        pb_history=pb_history,
        income_growth=income_growth,
        revenue_growth=revenue_growth,
        cagr=cagr,
        latest_fcff=latest_fcff,
        latest_fcfe=latest_fcfe,
        fcff_history=fcff_history,
        fcfe_history=fcfe_history,
        enterprise_value=enterprise_value or 0,
        ebitda=ebitda or 0,
        ev_to_ebitda=ev_to_ebitda or 0,
        current_yield=current_yield or 0,
        dividend_history=dividend_history or [],
        avg_div=avg_div or 0,
        payout_ratio=payout_ratio or 0,
        ddm_vals=ddm_vals or [],
        fcff_full_vals=fcff_full_vals or [],
        fcfe_full_vals=fcfe_full_vals or [],
        fcfe_vals=fcfe_vals or [],
        fcff_vals=fcff_vals or []
    )
    
    # 生成报告
    report_generator = ReportGenerator(stock_data)
    
    # 创建 reports 文件夹路径
    reports_folder = "reports"
    
    # 生成并打印估值报告
    report = report_generator.generate_valuation_report(
        pe_range=pe_range,
        pb_range=pb_range,
        growth_rates=growth_rates,
        discount_rates=discount_rates,
        ev_ebitda_range=ev_ebitda_range
    )
    
    print("\n" + "="*50 + " 股票估值报告 " + "="*50)
    print(report)
    print("="*112)
    
    # 生成Markdown报告
    md_report_path = f"{reports_folder}/{args.stock}_valuation_report.md"
    md_report = report_generator.generate_markdown_report()
    
    with open(md_report_path, "w", encoding="utf-8") as f:
        f.write(md_report)
    
    print(f"\nMarkdown报告已生成: {md_report_path}")
    
    # 生成HTML报告
    html_report_path = f"{reports_folder}/{args.stock}_valuation_report.html"
    html_report = report_generator.generate_html_report()
    
    with open(html_report_path, "w", encoding="utf-8") as f:
        f.write(html_report)
    print(f"HTML报告已生成: {html_report_path}")

if __name__ == "__main__":
    main()
