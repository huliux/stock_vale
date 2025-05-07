import argparse
import matplotlib
from data_fetcher import DataFetcher
from data_processor import DataProcessor # 新增导入
from financial_forecaster import FinancialForecaster # 新增导入
from valuation_calculator import ValuationCalculator
from report_generator import ReportGenerator
from models.stock_data import StockData  # 导入 StockData 类
import os # 导入 os 用于创建文件夹

matplotlib.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
matplotlib.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='股票绝对估值计算工具')
    # 使用从 config.ini.example 获取的默认值
    parser.add_argument('--stock', type=str, help='股票代码，例如：600519.SH', default='600519.SH')
    parser.add_argument('--pe', type=str, help='PE估值倍数，用逗号分隔，例如：5,8,12', default='5,8,12')
    parser.add_argument('--pb', type=str, help='PB估值倍数，用逗号分隔，例如：0.8,1.2,1.5', default='0.8,1.2,1.5')
    # 调整增长率参数，以适应多阶段模型 (简化处理，只取第一个作为高速增长期)
    parser.add_argument('--growth', type=str, help='高速增长期增长率(单个值或逗号分隔的多阶段)，例如：0.15 或 0.2,0.1,0.05', default='0.1')
    parser.add_argument('--growth-duration', type=str, help='各增长阶段持续年数(逗号分隔)，例如：2,3', default='5') # 默认一个阶段持续5年
    parser.add_argument('--forecast-years', type=int, help='总预测年限', default=5)
    parser.add_argument('--discount', type=str, help='折现率(WACC)，单个值', default='0.1') # 简化为单个WACC值
    parser.add_argument('--ev-ebitda', type=str, help='EV/EBITDA倍数，用逗号分隔，例如：6,8,10', default='6,8,10')
    parser.add_argument('--html', action='store_true', help='生成HTML格式报告')
    
    # 新增DCF终值相关参数
    parser.add_argument('--terminal-value-method', type=str, choices=['exit_multiple', 'perpetual_growth'], default='exit_multiple', help="终值计算方法 ('exit_multiple' 或 'perpetual_growth')")
    parser.add_argument('--exit-multiple', type=float, help="退出乘数 (用于 exit_multiple 方法)", default=None)
    parser.add_argument('--perpetual-growth-rate', type=float, help="永续增长率 (用于 perpetual_growth 方法)", default=None)
    # 可以添加更多参数来控制预测假设，如调整比例、目标天数等

    # 新增WACC相关参数 (用于 get_combo_valuations)
    parser.add_argument('--target-debt-ratio', type=float, help="目标债务比率 (用于WACC计算)", default=None) # None表示使用默认值
    parser.add_argument('--cost-of-debt', type=float, help="债务成本 (用于WACC计算)", default=None)
    parser.add_argument('--tax-rate', type=float, help="有效税率 (用于WACC计算)", default=None)
    parser.add_argument('--risk-free-rate', type=float, help="无风险利率 (用于WACC计算)", default=None)
    parser.add_argument('--beta', type=float, help="Beta值 (用于WACC计算)", default=None)
    parser.add_argument('--market-risk-premium', type=float, help="市场风险溢价 (用于WACC计算)", default=None)
    parser.add_argument('--size-premium', type=float, help="规模溢价 (用于WACC计算)", default=None)


    return parser.parse_args()

# 不再需要 read_config 函数

def main():
    """主程序入口"""
    args = parse_arguments() # 不再需要 config
    
    # 解析参数
    pe_range = args.pe.split(',')
    pb_range = args.pb.split(',')
    wacc = float(args.discount) # 使用单个WACC值 (用于主DCF计算)
    ev_ebitda_range = args.ev_ebitda.split(',')
    
    # --- 新增：数据获取、处理和预测流程 ---
    print("\n--- [1] 获取数据 ---")
    data_fetcher = DataFetcher(args.stock)
    
    # 获取基础数据
    stock_info = data_fetcher.get_stock_info()
    latest_price = data_fetcher.get_latest_price()
    total_shares = data_fetcher.get_total_shares()
    dividends = data_fetcher.get_dividend_data()
    market_cap = latest_price * total_shares / 100000000 if total_shares and latest_price is not None else 0 # 转为亿元

    # 获取原始财务报表数据
    try:
        raw_financial_data = data_fetcher.get_raw_financial_data(years=args.forecast_years + 1) 
    except Exception as e:
        print(f"错误：获取原始财务数据失败: {e}")
        raw_financial_data = {} 

    if not raw_financial_data or \
       raw_financial_data.get('balance_sheet') is None or raw_financial_data['balance_sheet'].empty or \
       raw_financial_data.get('income_statement') is None or raw_financial_data['income_statement'].empty or \
       raw_financial_data.get('cash_flow') is None or raw_financial_data['cash_flow'].empty:
        print("警告：获取到的原始财务数据不完整或为空，无法进行精细化预测。请检查数据库连接和数据可用性。")
        return 

    print("\n--- [2] 处理数据和计算历史比率 ---")
    processor = DataProcessor(raw_financial_data)
    processed_data = processor.clean_data() 
    historical_ratios = processor.calculate_historical_ratios_and_turnovers() 
    
    if 'income_statement' in processed_data and not processed_data['income_statement'].empty:
         historical_ratios['last_actual_revenue'] = processed_data['income_statement']['total_revenue'].iloc[-1] 
    else:
         historical_ratios['last_actual_revenue'] = 0 

    print("\n--- [2.5] 初始化估值计算器 ---")
    calculator = ValuationCalculator(
        stock_info=stock_info,
        latest_price=latest_price,
        total_shares=total_shares,
        financials=processed_data, 
        dividends=dividends,
        market_cap=market_cap
    )

    print("\n--- [3] 准备预测假设 ---")
    growth_rates_str = args.growth.split(',')
    growth_durations_str = args.growth_duration.split(',')
    
    revenue_growth_stages = []
    total_duration = 0
    for i, rate_str in enumerate(growth_rates_str):
        rate = float(rate_str)
        duration = int(growth_durations_str[i]) if i < len(growth_durations_str) else args.forecast_years - total_duration
        if duration <= 0: continue
        revenue_growth_stages.append({"duration": duration, "growth_rate": rate})
        total_duration += duration
        if total_duration >= args.forecast_years: break
        
    if total_duration < args.forecast_years and revenue_growth_stages:
         remaining_duration = args.forecast_years - total_duration
         last_rate = revenue_growth_stages[-1]['growth_rate']
         revenue_growth_stages.append({"duration": remaining_duration, "growth_rate": last_rate})
    elif not revenue_growth_stages: 
         revenue_growth_stages.append({"duration": args.forecast_years, "growth_rate": 0.05}) 

    forecast_assumptions = {
        "forecast_years": args.forecast_years,
        "revenue_growth_stages": revenue_growth_stages,
        "effective_tax_rate": historical_ratios.get('effective_tax_rate', 0.25), 
    }
    print("预测假设:", forecast_assumptions)

    print("\n--- [4] 执行财务预测 ---")
    last_actual_revenue = historical_ratios.get('last_actual_revenue', 0)
    if last_actual_revenue == 0:
         print("警告：无法获取最后一期实际收入，预测可能不准确。")

    forecaster = FinancialForecaster(
        last_actual_revenue=last_actual_revenue,
        historical_ratios=historical_ratios,
        forecast_assumptions=forecast_assumptions
    )
    full_forecast_data = forecaster.get_full_forecast() 

    print("\n--- [5] 计算估值 (基于新预测) ---")
    dcf_results = {} # Initialize dcf_results
    combos_with_margin = {}
    investment_advice = {}

    if 'fcf_components' in full_forecast_data and not full_forecast_data['fcf_components'].empty:
        forecast_df = full_forecast_data['fcf_components']
        required_cols = ['noplat', 'depreciation_amortization', 'capital_expenditures', 'delta_net_working_capital']
        if all(col in forecast_df.columns for col in required_cols):
            forecast_df['ufcf'] = forecast_df['noplat'] + forecast_df['depreciation_amortization'] \
                                  - forecast_df['capital_expenditures'] - forecast_df['delta_net_working_capital']
            print("预测的UFCF:\n", forecast_df[['year', 'ufcf']])
            
            print(f"使用的WACC (折现率): {wacc:.2%}")

            # --- 调用新的 DCF 计算方法 ---
            dcf_parameters = {
                "forecast_df": forecast_df,
                "wacc": wacc,
                "terminal_value_method": args.terminal_value_method
            }
            if args.terminal_value_method == 'exit_multiple':
                if args.exit_multiple is not None:
                    dcf_parameters["exit_multiple"] = args.exit_multiple
                else:
                    try:
                        exit_multiples_from_range = [float(m) for m in ev_ebitda_range]
                        fallback_exit_multiple = exit_multiples_from_range[len(exit_multiples_from_range)//2] if exit_multiples_from_range else 8.0
                    except:
                        fallback_exit_multiple = 8.0
                        print(f"警告：无法解析EV/EBITDA范围 '{args.ev_ebitda}' 作为退出乘数备选，将使用默认备选值 {fallback_exit_multiple}")
                    dcf_parameters["exit_multiple"] = fallback_exit_multiple
                    print(f"提示：未直接提供 --exit-multiple，已使用EV/EBITDA范围中间值或默认值作为备选: {fallback_exit_multiple}")
                dcf_parameters["perpetual_growth_rate"] = None 
            elif args.terminal_value_method == 'perpetual_growth':
                if args.perpetual_growth_rate is not None:
                    dcf_parameters["perpetual_growth_rate"] = args.perpetual_growth_rate
                else:
                    fallback_pg_rate = calculator.risk_free_rate * 0.7 if calculator.risk_free_rate else 0.02 
                    dcf_parameters["perpetual_growth_rate"] = fallback_pg_rate
                    print(f"提示：未直接提供 --perpetual-growth-rate，已使用默认备选值: {fallback_pg_rate:.2%}")
                dcf_parameters["exit_multiple"] = None
            
            dcf_results = calculator.calculate_dcf_valuation_from_forecast(**dcf_parameters)

            print("\n--- 基于新预测的DCF估值结果 ---")
            if dcf_results and dcf_results.get("error") is None:
                print(f"  企业价值 (EV): {dcf_results.get('enterprise_value'):,.2f}")
                print(f"  股权价值: {dcf_results.get('equity_value'):,.2f}")
                print(f"  每股价值: {dcf_results.get('value_per_share'):,.2f}")
                print(f"  预测期FCF现值: {dcf_results.get('pv_forecast_ufcf'):,.2f}")
                print(f"  终值: {dcf_results.get('terminal_value'):,.2f} (方法: {dcf_results.get('terminal_value_method_used')})")
                print(f"  终值现值: {dcf_results.get('pv_terminal_value'):,.2f}")
                print(f"  计算所用净债务: {dcf_results.get('net_debt'):,.2f}")
            else:
                print(f"  DCF估值计算失败: {dcf_results.get('error', '未知错误')}")

            # --- 调用组合估值计算 ---
            print("\n--- [6] 计算组合估值和投资建议 ---")
            # 构建 wacc_params 字典，只包含用户通过命令行指定的值
            wacc_calc_params = {k: v for k, v in vars(args).items() if v is not None and k in [
                'target_debt_ratio', 'cost_of_debt', 'tax_rate', 'risk_free_rate', 
                'beta', 'market_risk_premium', 'size_premium'
            ]}
            combos_with_margin, investment_advice = calculator.get_combo_valuations(
                main_dcf_result_dict=dcf_results,
                pe_multiples=pe_range,
                pb_multiples=pb_range,
                ev_ebitda_multiples=ev_ebitda_range,
                wacc_params=wacc_calc_params # 传递用户指定的WACC参数
            )
            print("组合估值（含安全边际）:", combos_with_margin)
            print("投资建议:", investment_advice)

        else:
            print("错误：预测结果中缺少计算UFCF所需的列。")
    else:
        print("错误：未能生成详细的财务预测数据。")


    # --- 准备 StockData 对象 ---
    print("\n--- [7] 准备报告数据 ---")
    # 计算历史指标（部分可能已在 calculator 中计算，这里可能重复或用于确认）
    pe_current = calculator.calculate_pe_ratio() 
    pb_current = calculator.calculate_pb_ratio() 
    income_growth_hist, revenue_growth_hist, cagr_hist = calculator.calculate_growth_rate() 
    enterprise_value_hist, ebitda_hist, ev_to_ebitda_hist = calculator.calculate_ev() 
    current_yield, dividend_history, avg_div, payout_ratio = calculator.calculate_dividend_yield()
    latest_fcff_hist, latest_fcfe_hist, fcff_history_hist, fcfe_history_hist, _ = calculator.calculate_fcff_fcfe()

    stock_data = StockData(
        stock_info=stock_info,
        latest_price=latest_price,
        total_shares=total_shares,
        market_cap=market_cap,
        pe_history=pe_current, 
        pb_history=pb_current, 
        income_growth=income_growth_hist, 
        revenue_growth=revenue_growth_hist, 
        cagr=cagr_hist, 
        latest_fcff=latest_fcff_hist, 
        latest_fcfe=latest_fcfe_hist, 
        fcff_history=fcff_history_hist, 
        fcfe_history=fcfe_history_hist,
        enterprise_value=enterprise_value_hist, 
        ebitda=ebitda_hist, 
        ev_to_ebitda=ev_to_ebitda_hist,
        current_yield=current_yield,
        dividend_history=dividend_history,
        avg_div=avg_div,
        payout_ratio=payout_ratio,
        pe_range=pe_range, # 传递范围给 StockData
        pb_range=pb_range,
        ev_ebitda_range=ev_ebitda_range,
        # 传递新的估值结果
        main_dcf_result=dcf_results, 
        combos_with_margin=combos_with_margin,
        investment_advice=investment_advice
    )

    # --- 报告生成部分 ---
    print("\n--- [8] 生成报告 ---")
    report_generator = ReportGenerator(stock_data) 
    
    reports_folder = "reports"
    if not os.path.exists(reports_folder):
        os.makedirs(reports_folder)

    # 生成并打印文本报告
    try:
        report = report_generator.generate_text_report(
            pe_range=pe_range, # 传递范围用于表格
            pb_range=pb_range,
            ev_ebitda_range=ev_ebitda_range
        )
        print("\n" + "="*50 + " 股票估值报告 " + "="*50)
        print(report)
        print("="*112)
    except Exception as e:
        print(f"生成文本报告时出错: {e}")
        traceback.print_exc()
    
    # 生成Markdown报告
    try:
        md_report_path = f"{reports_folder}/{args.stock}_valuation_report.md"
        md_report = report_generator.generate_markdown_report()
        with open(md_report_path, "w", encoding="utf-8") as f:
            f.write(md_report) 
        print(f"\nMarkdown报告已生成: {md_report_path}")
    except Exception as e:
        print(f"生成Markdown报告时出错: {e}")
        traceback.print_exc()
    
    # 生成HTML报告 (如果指定了 --html)
    if args.html:
        try:
            html_report_path = f"{reports_folder}/{args.stock}_valuation_report.html"
            html_report = report_generator.generate_html_report()
            with open(html_report_path, "w", encoding="utf-8") as f:
                f.write(html_report) 
            print(f"HTML报告已生成: {html_report_path}")
        except Exception as e:
            print(f"生成HTML报告时出错: {e}")
            traceback.print_exc()

if __name__ == "__main__":
    main()
