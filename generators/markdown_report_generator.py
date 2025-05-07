import pandas as pd
import numpy as np
from utils.report_utils import get_recommendation
from models.stock_data import StockData # 导入 StockData
from typing import List, Dict, Any # 导入类型提示

class MarkdownReportGenerator:
    def __init__(self, stock_data: StockData):
        """
        初始化 Markdown 报告生成器。
        Args:
            stock_data (StockData): 包含所有计算好的估值和分析数据的对象。
        """
        if not isinstance(stock_data, StockData):
            raise ValueError("stock_data must be an instance of StockData")
        self.stock_data = stock_data
        # 相对估值范围可以从 stock_data 获取（如果 main.py 设置了它们）
        # 或者使用默认值，或者要求在 generate 方法中传入
        # 为简单起见，暂时使用默认值，但理想情况下应由调用者控制或在 stock_data 中设置
        self.pe_range = getattr(stock_data, 'pe_range', ['5', '8', '12', '15', '20']) # 示例默认值
        self.pb_range = getattr(stock_data, 'pb_range', ['0.8', '1.2', '1.5', '2.0', '2.5']) # 示例默认值
        self.ev_ebitda_range = getattr(stock_data, 'ev_ebitda_range', ['6', '8', '10', '12', '15']) # 示例默认值

    def generate_markdown_report(self) -> str:
        """生成Markdown格式的估值报告"""
        sd = self.stock_data
        md_lines = []

        md_lines.append(f"# 股票估值报告 - {sd.stock_info.get('ts_code', 'N/A')} {sd.stock_info.get('name', 'N/A')}")
        md_lines.append(f"\n*生成日期: {pd.Timestamp.now().strftime('%Y年%m月%d日')}*")

        # --- 基本信息 ---
        md_lines.append("\n## 基本信息")
        md_lines.append("\n| 项目 | 数值 |")
        md_lines.append("|------|------|")
        md_lines.append(f"| 股票代码 | {sd.stock_info.get('ts_code', 'N/A')} |")
        md_lines.append(f"| 股票名称 | {sd.stock_info.get('name', 'N/A')} |")
        md_lines.append(f"| 当前价格 | {sd.latest_price:.2f} 元 |" if sd.latest_price is not None else "| 当前价格 | N/A |")
        md_lines.append(f"| 总股本 | {sd.total_shares/100000000:.2f} 亿股 |" if sd.total_shares else "| 总股本 | N/A |")
        md_lines.append(f"| 市值 | {sd.market_cap:.2f} 亿元 |" if sd.market_cap is not None else "| 市值 | N/A |")

        # --- 相对估值 ---
        md_lines.append("\n## 相对估值")

        # PE估值
        md_lines.append("\n### PE估值")
        md_lines.append("\n| 指标 | 估值 | 相对当前价格 |")
        md_lines.append("|------|------|------------|")
        if sd.pe_history is not None and sd.pe_history != 0 and sd.latest_price is not None:
            current_eps = sd.latest_price / sd.pe_history
            md_lines.append(f"| 当前PE | {sd.pe_history:.2f} | - |")
            for pe_str in self.pe_range:
                try:
                    pe = float(pe_str)
                    value = pe * current_eps
                    premium = (value - sd.latest_price) / sd.latest_price * 100 if sd.latest_price else 0
                    md_lines.append(f"| PE={pe_str} | {value:.2f} 元/股 | {premium:+.2f}% |")
                except ValueError:
                    md_lines.append(f"| PE={pe_str} | 无效PE值 | - |")
        else:
            md_lines.append("| 当前PE | N/A | - |")
            md_lines.append("| PE估值 | 数据不足 | - |")

        # PB估值
        md_lines.append("\n### PB估值")
        md_lines.append("\n| 指标 | 估值 | 相对当前价格 |")
        md_lines.append("|------|------|------------|")
        if sd.pb_history is not None and sd.pb_history != 0 and sd.latest_price is not None:
            current_bps = sd.latest_price / sd.pb_history
            md_lines.append(f"| 当前PB | {sd.pb_history:.2f} | - |")
            for pb_str in self.pb_range:
                try:
                    pb = float(pb_str)
                    value = pb * current_bps
                    premium = (value - sd.latest_price) / sd.latest_price * 100 if sd.latest_price else 0
                    md_lines.append(f"| PB={pb_str} | {value:.2f} 元/股 | {premium:+.2f}% |")
                except ValueError:
                    md_lines.append(f"| PB={pb_str} | 无效PB值 | - |")
        else:
            md_lines.append("| 当前PB | N/A | - |")
            md_lines.append("| PB估值 | 数据不足 | - |")

        # EV/EBITDA估值
        md_lines.append("\n### EV/EBITDA估值")
        md_lines.append("\n| 指标 | 估值 | 相对当前价格 |")
        md_lines.append("|------|------|------------|")
        if sd.ev_to_ebitda is not None and sd.ebitda is not None and sd.total_shares and sd.latest_price is not None:
            md_lines.append(f"| 当前EV/EBITDA | {sd.ev_to_ebitda:.2f} | - |")
            # 尝试从 DCF 结果获取净债务，否则从历史数据估算
            main_dcf_result = sd.fcff_full_vals[0] if sd.fcff_full_vals and isinstance(sd.fcff_full_vals, list) and len(sd.fcff_full_vals) > 0 else {}
            net_debt_for_ev_calc = main_dcf_result.get('net_debt') if main_dcf_result.get('net_debt') is not None else (sd.enterprise_value - sd.market_cap * 100000000 if sd.enterprise_value and sd.market_cap else 0)

            for multiple_str in self.ev_ebitda_range:
                try:
                    multiple = float(multiple_str)
                    target_ev = multiple * sd.ebitda
                    equity_value = target_ev - net_debt_for_ev_calc
                    value = equity_value / sd.total_shares if sd.total_shares else 0
                    premium = (value - sd.latest_price) / sd.latest_price * 100 if sd.latest_price > 0 else 0
                    md_lines.append(f"| EV/EBITDA={multiple_str} | {value:.2f} 元/股 | {premium:+.2f}% |")
                except ValueError:
                    md_lines.append(f"| EV/EBITDA={multiple_str} | 无效乘数 | - |")
        else:
            md_lines.append("| 当前EV/EBITDA | N/A | - |")
            md_lines.append("| EV/EBITDA估值 | 数据不足 | - |")

        # --- 绝对估值 ---
        md_lines.append("\n## 绝对估值")

        # DCF估值 (基于新的单一DCF结果)
        md_lines.append("\n### DCF估值 (基于预测期UFCF)")
        md_lines.append("\n| 指标 | 数值 |")
        md_lines.append("|------|------|")
        main_dcf_result = sd.fcff_full_vals[0] if sd.fcff_full_vals and isinstance(sd.fcff_full_vals, list) and len(sd.fcff_full_vals) > 0 else None

        if main_dcf_result and main_dcf_result.get("error") is None:
            md_lines.append(f"| 终值方法 | {main_dcf_result.get('terminal_value_method_used', 'N/A')} |")
            if main_dcf_result.get('terminal_value_method_used') == 'exit_multiple':
                md_lines.append(f"| 退出乘数 | {main_dcf_result.get('exit_multiple_used', 'N/A')}x |")
            elif main_dcf_result.get('terminal_value_method_used') == 'perpetual_growth':
                md_lines.append(f"| 永续增长率 | {main_dcf_result.get('perpetual_growth_rate_used', 0):.2%} |")
            md_lines.append(f"| WACC | {main_dcf_result.get('wacc_used', 0):.2%} |")
            md_lines.append(f"| 预测期 | {main_dcf_result.get('forecast_period_years', 'N/A')} 年 |")
            md_lines.append(f"| 企业价值 (EV) | {main_dcf_result.get('enterprise_value', 0):,.2f} |")
            md_lines.append(f"| 净债务 | {main_dcf_result.get('net_debt', 0):,.2f} |")
            md_lines.append(f"| 股权价值 | {main_dcf_result.get('equity_value', 0):,.2f} |")
            value_per_share = main_dcf_result.get('value_per_share')
            if value_per_share is not None:
                md_lines.append(f"| **每股价值** | **{value_per_share:.2f} 元/股** |")
                if sd.latest_price is not None and sd.latest_price > 0:
                    premium = (value_per_share / sd.latest_price - 1) * 100
                    md_lines.append(f"| 相对当前价格 | {premium:+.2f}% |")
            else:
                md_lines.append("| 每股价值 | N/A |")
        elif main_dcf_result and main_dcf_result.get("error"):
            md_lines.append(f"| 错误 | DCF估值计算失败: {main_dcf_result.get('error')} |")
        else:
            md_lines.append("| 结果 | 无有效的DCF估值结果。 |")

        # DDM估值 (如果 stock_data.ddm_vals 包含新的单一DDM结果)
        md_lines.append("\n### DDM估值(股利贴现模型)")
        md_lines.append("\n| 指标 | 数值 |")
        md_lines.append("|------|------|")
        main_ddm_result = sd.ddm_vals[0] if sd.ddm_vals and isinstance(sd.ddm_vals, list) and len(sd.ddm_vals) > 0 else None

        if main_ddm_result and main_ddm_result.get("error") is None:
            # Display DDM results similarly if available
            value_per_share_ddm = main_ddm_result.get('value_per_share') # Assuming DDM result has this key
            if value_per_share_ddm is not None:
                 md_lines.append(f"| **每股价值** | **{value_per_share_ddm:.2f} 元/股** |")
                 if sd.latest_price is not None and sd.latest_price > 0:
                     premium_ddm = (value_per_share_ddm / sd.latest_price - 1) * 100
                     md_lines.append(f"| 相对当前价格 | {premium_ddm:+.2f}% |")
            else:
                 md_lines.append("| 每股价值 | N/A |")
            # Add other relevant DDM details if present in the result dict
        elif main_ddm_result and main_ddm_result.get("error"):
            md_lines.append(f"| 错误 | DDM估值计算失败: {main_ddm_result.get('error')} |")
        else:
            md_lines.append("| 结果 | 无有效的DDM估值结果或未执行。 |")

        # --- 其他分析 ---
        md_lines.append("\n## 其他分析")

        # 股息分析
        md_lines.append("\n### 股息分析")
        md_lines.append("\n| 指标 | 数值 |")
        md_lines.append("|------|------|")
        md_lines.append(f"| 当前股息率 | {sd.current_yield:.2f}% |" if sd.current_yield is not None else "| 当前股息率 | N/A |")
        md_lines.append(f"| 3年平均分红 | {sd.avg_div:.2f} 元/股 |" if sd.avg_div is not None else "| 3年平均分红 | N/A |")
        md_lines.append(f"| 分红支付率 | {sd.payout_ratio:.2f}% |" if sd.payout_ratio is not None else "| 分红支付率 | N/A |")

        # 增长分析
        md_lines.append("\n### 增长分析")
        md_lines.append("\n| 指标 | 数值 |")
        md_lines.append("|------|------|")
        cagr_data = sd.cagr if isinstance(sd.cagr, dict) else {}
        md_lines.append(f"| 3年净利润CAGR | {cagr_data.get('income_3y', 0):.2f}% |")
        md_lines.append(f"| 3年营收CAGR | {cagr_data.get('revenue_3y', 0):.2f}% |")

        # --- 综合分析 ---
        md_lines.append("\n## 综合分析")

        # 组合估值
        if hasattr(sd, 'combos_with_margin') and sd.combos_with_margin:
            md_lines.append("\n### 组合估值")
            md_lines.append("\n| 组合 | 估值 (元/股) | 安全边际 |")
            md_lines.append("|------|--------------|----------|")
            for combo_name, combo_data in sd.combos_with_margin.items():
                if combo_data and combo_data.get('value') is not None:
                    val_str = f"{combo_data['value']:.2f}"
                    margin_str = f"{combo_data['safety_margin_pct']:+.2f}%" if combo_data.get('safety_margin_pct') is not None else "N/A"
                    md_lines.append(f"| {combo_name} | {val_str} | {margin_str} |")
                else:
                    md_lines.append(f"| {combo_name} | N/A | N/A |")
        else:
            md_lines.append("\n组合估值: 无数据。")

        # 投资建议
        if hasattr(sd, 'investment_advice') and sd.investment_advice:
            md_lines.append("\n### 投资建议")
            advice = sd.investment_advice
            md_lines.append(f"\n**建议:** {advice.get('advice', 'N/A')}")
            md_lines.append(f"\n**理由:** {advice.get('reason', 'N/A')}")
            
            min_val = advice.get('min_intrinsic_value')
            max_val = advice.get('max_intrinsic_value')
            avg_val = advice.get('avg_intrinsic_value')
            margin = advice.get('safety_margin_pct')
            
            md_lines.append("\n| 指标 | 数值 |")
            md_lines.append("|------|------|")
            if min_val is not None and max_val is not None:
                 md_lines.append(f"| 核心估值区间 | {min_val:.2f} - {max_val:.2f} 元/股 |")
            if avg_val is not None:
                 md_lines.append(f"| 核心平均估值 | {avg_val:.2f} 元/股 |")
            if margin is not None:
                 md_lines.append(f"| 安全边际 | {margin:+.2f}% |")
            md_lines.append(f"| 基于 | {advice.get('based_on', 'N/A')} |")
            
            md_lines.append(f"\n**参考信息:** {advice.get('reference_info', 'N/A')}")
        else:
            md_lines.append("\n投资建议: 无数据。")

        return "\n".join(md_lines)
