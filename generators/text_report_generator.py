import numpy as np
from utils.report_utils import get_recommendation
from models.stock_data import StockData # 导入 StockData
from typing import List, Dict, Any # 导入类型提示

class TextReportGenerator:
    def __init__(self, stock_data: StockData):
        self.stock_data = stock_data

    def generate_valuation_report(self, 
                                  pe_range: List[str], 
                                  pb_range: List[str], 
                                  ev_ebitda_range: List[str]) -> str:
        """生成文本格式的估值报告"""
        report_lines = []
        sd = self.stock_data # 简化访问

        # 基本信息
        report_lines.append(f"股票代码: {sd.stock_info.get('ts_code', 'N/A')}")
        report_lines.append(f"股票名称: {sd.stock_info.get('name', 'N/A')}")
        report_lines.append(f"当前价格: {sd.latest_price:.2f} 元" if sd.latest_price is not None else "当前价格: N/A")
        report_lines.append(f"总股本: {sd.total_shares/100000000:.2f} 亿股" if sd.total_shares else "总股本: N/A")
        report_lines.append(f"市值: {sd.market_cap:.2f} 亿元" if sd.market_cap is not None else "市值: N/A")

        # PE估值
        report_lines.append("\nPE估值:")
        if sd.pe_history is not None and sd.pe_history != 0 and sd.latest_price is not None:
            current_eps = sd.latest_price / sd.pe_history
            report_lines.append(f"当前PE: {sd.pe_history:.2f} 倍 (基于此计算的EPS: {current_eps:.2f})")
            for pe_str in pe_range:
                try:
                    pe = float(pe_str)
                    value = pe * current_eps
                    premium = (value - sd.latest_price) / sd.latest_price * 100 if sd.latest_price else 0
                    report_lines.append(f"PE={pe_str}: {value:.2f} 元/股 ({premium:+.2f}%)")
                except ValueError:
                    report_lines.append(f"PE={pe_str}: 无效的PE值")
        else:
            report_lines.append("当前PE数据不足或为零，无法进行PE估值区间计算。")

        # PB估值
        report_lines.append("\nPB估值:")
        if sd.pb_history is not None and sd.pb_history != 0 and sd.latest_price is not None:
            current_bps = sd.latest_price / sd.pb_history
            report_lines.append(f"当前PB: {sd.pb_history:.2f} 倍 (基于此计算的BPS: {current_bps:.2f})")
            for pb_str in pb_range:
                try:
                    pb = float(pb_str)
                    value = pb * current_bps
                    premium = (value - sd.latest_price) / sd.latest_price * 100 if sd.latest_price else 0
                    report_lines.append(f"PB={pb_str}: {value:.2f} 元/股 ({premium:+.2f}%)")
                except ValueError:
                    report_lines.append(f"PB={pb_str}: 无效的PB值")
        else:
            report_lines.append("当前PB数据不足或为零，无法进行PB估值区间计算。")
        
        # DCF估值 (基于新的单一DCF结果)
        # fcff_full_vals 在 main.py 中被设置为 [dcf_results]
        report_lines.append("\nDCF估值 (基于预测期UFCF):")
        main_dcf_result = None
        if sd.fcff_full_vals and isinstance(sd.fcff_full_vals, list) and len(sd.fcff_full_vals) > 0:
            main_dcf_result = sd.fcff_full_vals[0] # 获取第一个（也是唯一一个）结果字典
        
        if main_dcf_result and main_dcf_result.get("error") is None:
            report_lines.append(f"  方法: {main_dcf_result.get('terminal_value_method_used', 'N/A')}")
            if main_dcf_result.get('terminal_value_method_used') == 'exit_multiple':
                report_lines.append(f"  退出乘数: {main_dcf_result.get('exit_multiple_used', 'N/A')}x")
            elif main_dcf_result.get('terminal_value_method_used') == 'perpetual_growth':
                report_lines.append(f"  永续增长率: {main_dcf_result.get('perpetual_growth_rate_used', 0):.2%}")
            report_lines.append(f"  WACC: {main_dcf_result.get('wacc_used', 0):.2%}")
            report_lines.append(f"  预测期: {main_dcf_result.get('forecast_period_years', 'N/A')} 年")
            report_lines.append(f"  企业价值 (EV): {main_dcf_result.get('enterprise_value', 0):,.2f}")
            report_lines.append(f"  净债务: {main_dcf_result.get('net_debt', 0):,.2f}")
            report_lines.append(f"  股权价值: {main_dcf_result.get('equity_value', 0):,.2f}")
            value_per_share = main_dcf_result.get('value_per_share')
            if value_per_share is not None:
                report_lines.append(f"  每股价值: {value_per_share:.2f} 元/股")
                if sd.latest_price is not None and sd.latest_price > 0:
                    premium = (value_per_share / sd.latest_price - 1) * 100
                    report_lines.append(f"  相对当前价格: {premium:+.2f}%")
            else:
                report_lines.append("  每股价值: N/A")
        elif main_dcf_result and main_dcf_result.get("error"):
            report_lines.append(f"  DCF估值计算失败: {main_dcf_result.get('error')}")
        else:
            report_lines.append("  无有效的DCF估值结果。")

        # EV/EBITDA估值
        report_lines.append("\nEV/EBITDA估值:")
        if sd.ev_to_ebitda is not None and sd.ebitda is not None and sd.enterprise_value is not None and sd.total_shares:
            report_lines.append(f"当前EV/EBITDA: {sd.ev_to_ebitda:.2f}")
            # EV = Market Cap + Total Debt - Cash & Cash Equivalents
            # Market Cap = enterprise_value - total_debt + cash
            # total_debt - cash = net_debt
            # Market Cap = enterprise_value - net_debt
            # Value per share = (Target EV - Net Debt) / Total Shares
            # Target EV = Target EV/EBITDA * EBITDA
            # Net Debt = EV_hist - MarketCap_hist (注意单位)
            # 或者使用 ValuationCalculator 中计算的 net_debt (如果一致)
            net_debt_for_ev_calc = main_dcf_result.get('net_debt') if main_dcf_result else (sd.enterprise_value - sd.market_cap * 100000000 if sd.enterprise_value and sd.market_cap else 0)

            for multiple_str in ev_ebitda_range:
                try:
                    multiple = float(multiple_str)
                    target_ev = multiple * sd.ebitda # sd.ebitda 应该是最新一期或预测第一期
                    equity_value = target_ev - net_debt_for_ev_calc
                    value = equity_value / sd.total_shares if sd.total_shares else 0
                    premium = (value - sd.latest_price) / sd.latest_price * 100 if sd.latest_price and sd.latest_price > 0 else 0
                    report_lines.append(f"EV/EBITDA={multiple_str}: {value:.2f} 元/股 ({premium:+.2f}%)")
                except ValueError:
                    report_lines.append(f"EV/EBITDA={multiple_str}: 无效的乘数")
        else:
            report_lines.append("EV/EBITDA数据不足，无法进行估值区间计算。")
        
        # 股息分析
        report_lines.append("\n股息分析:")
        report_lines.append(f"当前股息率: {sd.current_yield:.2f}%" if sd.current_yield is not None else "当前股息率: N/A")
        report_lines.append(f"3年平均分红: {sd.avg_div:.2f} 元/股" if sd.avg_div is not None else "3年平均分红: N/A")
        report_lines.append(f"分红支付率: {sd.payout_ratio:.2f}%" if sd.payout_ratio is not None else "分红支付率: N/A")
        
        # 增长分析 (从 stock_data.cagr 获取)
        report_lines.append("\n增长分析:")
        cagr_data = sd.cagr if isinstance(sd.cagr, dict) else {}
        report_lines.append(f"3年净利润CAGR: {cagr_data.get('income_3y', 0):.2f}%")
        report_lines.append(f"3年营收CAGR: {cagr_data.get('revenue_3y', 0):.2f}%")
        
        # DDM估值 (如果 stock_data.ddm_vals 包含新的单一DDM结果)
        report_lines.append("\nDDM估值(股利贴现模型):")
        # 假设 ddm_vals 结构与 fcff_full_vals 类似，是一个包含单个结果字典的列表
        main_ddm_result = None
        if sd.ddm_vals and isinstance(sd.ddm_vals, list) and len(sd.ddm_vals) > 0:
             main_ddm_result = sd.ddm_vals[0] # Placeholder if DDM is refactored similarly

        if main_ddm_result and main_ddm_result.get("error") is None:
            # Similar display logic as DCF if DDM provides these details
            report_lines.append(f"  每股价值: {main_ddm_result.get('value_per_share', 'N/A'):.2f} 元/股")
            # ... add more details if available from DDM result
        elif main_ddm_result and main_ddm_result.get("error"):
            report_lines.append(f"  DDM估值计算失败: {main_ddm_result.get('error')}")
        else:
            report_lines.append("  无有效的DDM估值结果或未执行。")
        
        # 综合分析 (基于 stock_data.combos_with_margin 和 stock_data.investment_advice)
        report_lines.append("\n\n=== 综合分析 ===")
        if hasattr(sd, 'combos_with_margin') and sd.combos_with_margin:
            report_lines.append("\n组合估值:")
            for combo_name, combo_data in sd.combos_with_margin.items():
                if combo_data and combo_data.get('value') is not None:
                    val_str = f"{combo_data['value']:.2f}"
                    margin_str = f"{combo_data['safety_margin_pct']:+.2f}%" if combo_data.get('safety_margin_pct') is not None else "N/A"
                    report_lines.append(f"  {combo_name}: {val_str} 元/股 (安全边际: {margin_str})")
                else:
                    report_lines.append(f"  {combo_name}: N/A")
        else:
            report_lines.append("\n组合估值: 无数据。")

        if hasattr(sd, 'investment_advice') and sd.investment_advice:
            report_lines.append("\n投资建议:")
            advice = sd.investment_advice
            report_lines.append(f"  建议: {advice.get('advice', 'N/A')}")
            report_lines.append(f"  理由: {advice.get('reason', 'N/A')}")
            report_lines.append(f"  基于: {advice.get('based_on', 'N/A')}")
            min_val = advice.get('min_intrinsic_value')
            avg_val = advice.get('avg_intrinsic_value')
            max_val = advice.get('max_intrinsic_value')
            if min_val is not None and max_val is not None:
                 report_lines.append(f"  核心估值区间 (基于建议): {min_val:.2f} - {max_val:.2f} 元/股")
            if avg_val is not None:
                 report_lines.append(f"  核心平均估值 (基于建议): {avg_val:.2f} 元/股")
            margin = advice.get('safety_margin_pct')
            if margin is not None:
                 report_lines.append(f"  安全边际 (基于建议): {margin:+.2f}%")
            report_lines.append(f"  参考信息: {advice.get('reference_info', 'N/A')}")
        else:
            report_lines.append("\n投资建议: 无数据。")
            
        return "\n".join(report_lines)
