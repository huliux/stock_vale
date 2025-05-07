import os
import numpy as np
import pandas as pd
from datetime import datetime
from models.stock_data import StockData # 导入 StockData
from typing import List, Dict, Any # 导入类型提示
# 移除 BaseReportGenerator 导入
# from .base_report_generator import BaseReportGenerator 

# get_recommendation 函数可以保留在此文件或移至 utils
def get_recommendation(premium):
    """根据溢价率返回投资建议"""
    if premium is None:
        return "无法评估"
    if premium > 20:
        return "强烈买入"
    elif premium > 10:
        return "买入"
    elif premium > -10:
        return "持有"
    elif premium > -20:
        return "卖出"
    else:
        return "强烈卖出"

class HtmlReportGenerator: # 移除继承
    def __init__(self, stock_data: StockData):
        """
        初始化 HTML 报告生成器。
        Args:
            stock_data (StockData): 包含所有计算好的估值和分析数据的对象。
        """
        # 不再调用 super().__init__
        if not isinstance(stock_data, StockData):
            raise ValueError("stock_data must be an instance of StockData")
        self.stock_data = stock_data
        self.stock_info = stock_data.stock_info
        self.stock_code = stock_data.stock_info.get('ts_code', 'N/A')
        self.stock_name = stock_data.stock_info.get('name', '未知名称')
        # 相对估值范围可以从 stock_data 获取或使用默认值
        self.pe_range = getattr(stock_data, 'pe_range', ['5', '8', '12', '15', '20'])
        self.pb_range = getattr(stock_data, 'pb_range', ['0.8', '1.2', '1.5', '2.0', '2.5'])
        self.ev_ebitda_range = getattr(stock_data, 'ev_ebitda_range', ['6', '8', '10', '12', '15'])

    def export_report(self):
        """导出HTML报告到文件"""
        html_content = self.generate_html_report()
        os.makedirs('reports', exist_ok=True)
        filename = f"reports/{self.stock_code}_valuation_report.html"
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html_content)
            return filename
        except IOError as e:
            raise RuntimeError(f"导出HTML报告失败: {str(e)}")

    def _generate_table_rows(self, data_list, value_key='value', premium_key='premium', prefix='', suffix='元/股'):
        """辅助函数生成表格行"""
        rows = ""
        if data_list and isinstance(data_list, list):
            for item in data_list:
                 if isinstance(item, dict):
                     label = item.get('label', '') # Assume label might exist for some data
                     val = item.get(value_key)
                     prem = item.get(premium_key)
                     val_str = f"{val:.2f} {suffix}" if val is not None else "N/A"
                     prem_str = f"{prem:+.2f}%" if prem is not None else "N/A"
                     # Example: Use growth/discount rate as label for DCF/DDM
                     if 'growth_rate' in item and 'discount_rate' in item:
                         label = f"g={item['growth_rate']:.1%}, r={item['discount_rate']:.1%}"
                     
                     rows += f"<tr><td>{prefix}{label}</td><td>{val_str}</td><td>{prem_str}</td></tr>\n"
        return rows if rows else f"<tr><td colspan='3'>无数据</td></tr>"


    def generate_html_report(self):
        """生成HTML报告，确保与Markdown报告使用相同的数据和计算逻辑"""
        sd = self.stock_data
        
        # --- 基本信息 ---
        basic_info = f"""
        <div class="container">
            <h1>股票估值报告 - {self.stock_code} {self.stock_name}</h1>
            <p><em>生成日期: {datetime.now().strftime('%Y年%m月%d日')}</em></p>
            
            <h2>基本信息</h2>
            <table>
                <tr><th>项目</th><th>数值</th></tr>
                <tr><td>股票代码</td><td>{sd.stock_info.get('ts_code', 'N/A')}</td></tr>
                <tr><td>股票名称</td><td>{sd.stock_info.get('name', 'N/A')}</td></tr>
                <tr><td>当前价格</td><td>{sd.latest_price:.2f} 元</td></tr>
                <tr><td>总股本</td><td>{sd.total_shares/100000000:.2f} 亿股</td></tr>
                <tr><td>市值</td><td>{sd.market_cap:.2f} 亿元</td></tr>
            </table>
        """

        # --- 相对估值 ---
        relative_valuation = "<h2>相对估值</h2>"

        # PE估值
        relative_valuation += """
            <h3>PE估值</h3>
            <table>
                <tr><th>指标</th><th>估值</th><th>相对当前价格</th></tr>
        """
        if sd.pe_history is not None and sd.pe_history != 0 and sd.latest_price is not None:
            current_eps = sd.latest_price / sd.pe_history
            relative_valuation += f"<tr><td>当前PE</td><td>{sd.pe_history:.2f}</td><td>-</td></tr>"
            for pe_str in self.pe_range:
                try:
                    pe = float(pe_str)
                    value = pe * current_eps
                    premium = (value - sd.latest_price) / sd.latest_price * 100 if sd.latest_price else 0
                    relative_valuation += f"<tr><td>PE={pe_str}</td><td>{value:.2f} 元/股</td><td>{premium:+.2f}%</td></tr>\n"
                except ValueError:
                    relative_valuation += f"<tr><td>PE={pe_str}</td><td>无效PE值</td><td>-</td></tr>\n"
        else:
            relative_valuation += "<tr><td>当前PE</td><td>N/A</td><td>-</td></tr>\n"
            relative_valuation += "<tr><td colspan='3'>数据不足，无法进行PE估值区间计算。</td></tr>\n"
        relative_valuation += "</table>"

        # PB估值
        relative_valuation += """
            <h3>PB估值</h3>
            <table>
                <tr><th>指标</th><th>估值</th><th>相对当前价格</th></tr>
        """
        if sd.pb_history is not None and sd.pb_history != 0 and sd.latest_price is not None:
            current_bps = sd.latest_price / sd.pb_history
            relative_valuation += f"<tr><td>当前PB</td><td>{sd.pb_history:.2f}</td><td>-</td></tr>"
            for pb_str in self.pb_range:
                try:
                    pb = float(pb_str)
                    value = pb * current_bps
                    premium = (value - sd.latest_price) / sd.latest_price * 100 if sd.latest_price else 0
                    relative_valuation += f"<tr><td>PB={pb_str}</td><td>{value:.2f} 元/股</td><td>{premium:+.2f}%</td></tr>\n"
                except ValueError:
                    relative_valuation += f"<tr><td>PB={pb_str}</td><td>无效PB值</td><td>-</td></tr>\n"
        else:
            relative_valuation += "<tr><td>当前PB</td><td>N/A</td><td>-</td></tr>\n"
            relative_valuation += "<tr><td colspan='3'>数据不足，无法进行PB估值区间计算。</td></tr>\n"
        relative_valuation += "</table>"

        # EV/EBITDA估值
        relative_valuation += """
            <h3>EV/EBITDA估值</h3>
            <table>
                <tr><th>指标</th><th>估值</th><th>相对当前价格</th></tr>
        """
        if sd.ev_to_ebitda is not None and sd.ebitda is not None and sd.total_shares and sd.latest_price is not None:
            relative_valuation += f"<tr><td>当前EV/EBITDA</td><td>{sd.ev_to_ebitda:.2f}</td><td>-</td></tr>"
            main_dcf_result = sd.fcff_full_vals[0] if sd.fcff_full_vals and isinstance(sd.fcff_full_vals, list) and len(sd.fcff_full_vals) > 0 else {}
            net_debt_for_ev_calc = main_dcf_result.get('net_debt') if main_dcf_result.get('net_debt') is not None else (sd.enterprise_value - sd.market_cap * 100000000 if sd.enterprise_value and sd.market_cap else 0)
            for multiple_str in self.ev_ebitda_range:
                try:
                    multiple = float(multiple_str)
                    target_ev = multiple * sd.ebitda
                    equity_value = target_ev - net_debt_for_ev_calc
                    value = equity_value / sd.total_shares if sd.total_shares else 0
                    premium = (value - sd.latest_price) / sd.latest_price * 100 if sd.latest_price > 0 else 0
                    relative_valuation += f"<tr><td>EV/EBITDA={multiple_str}</td><td>{value:.2f} 元/股</td><td>{premium:+.2f}%</td></tr>\n"
                except ValueError:
                    relative_valuation += f"<tr><td>EV/EBITDA={multiple_str}</td><td>无效乘数</td><td>-</td></tr>\n"
        else:
            relative_valuation += "<tr><td>当前EV/EBITDA</td><td>N/A</td><td>-</td></tr>\n"
            relative_valuation += "<tr><td colspan='3'>数据不足，无法进行EV/EBITDA估值区间计算。</td></tr>\n"
        relative_valuation += "</table>"

        # --- 绝对估值 ---
        absolute_valuation = "<h2>绝对估值</h2>"

        # DCF估值
        absolute_valuation += """
            <h3>DCF估值 (基于预测期UFCF)</h3>
            <table>
                <tr><th>指标</th><th>数值</th></tr>
        """
        main_dcf_result = sd.fcff_full_vals[0] if sd.fcff_full_vals and isinstance(sd.fcff_full_vals, list) and len(sd.fcff_full_vals) > 0 else None
        if main_dcf_result and main_dcf_result.get("error") is None:
            absolute_valuation += f"<tr><td>终值方法</td><td>{main_dcf_result.get('terminal_value_method_used', 'N/A')}</td></tr>"
            if main_dcf_result.get('terminal_value_method_used') == 'exit_multiple':
                absolute_valuation += f"<tr><td>退出乘数</td><td>{main_dcf_result.get('exit_multiple_used', 'N/A')}x</td></tr>"
            elif main_dcf_result.get('terminal_value_method_used') == 'perpetual_growth':
                absolute_valuation += f"<tr><td>永续增长率</td><td>{main_dcf_result.get('perpetual_growth_rate_used', 0):.2%}</td></tr>"
            absolute_valuation += f"<tr><td>WACC</td><td>{main_dcf_result.get('wacc_used', 0):.2%}</td></tr>"
            absolute_valuation += f"<tr><td>预测期</td><td>{main_dcf_result.get('forecast_period_years', 'N/A')} 年</td></tr>"
            absolute_valuation += f"<tr><td>企业价值 (EV)</td><td>{main_dcf_result.get('enterprise_value', 0):,.2f}</td></tr>"
            absolute_valuation += f"<tr><td>净债务</td><td>{main_dcf_result.get('net_debt', 0):,.2f}</td></tr>"
            absolute_valuation += f"<tr><td>股权价值</td><td>{main_dcf_result.get('equity_value', 0):,.2f}</td></tr>"
            value_per_share = main_dcf_result.get('value_per_share')
            if value_per_share is not None:
                absolute_valuation += f"<tr><td><b>每股价值</b></td><td><b>{value_per_share:.2f} 元/股</b></td></tr>"
                if sd.latest_price is not None and sd.latest_price > 0:
                    premium = (value_per_share / sd.latest_price - 1) * 100
                    absolute_valuation += f"<tr><td>相对当前价格</td><td>{premium:+.2f}%</td></tr>"
            else:
                absolute_valuation += "<tr><td>每股价值</td><td>N/A</td></tr>"
        elif main_dcf_result and main_dcf_result.get("error"):
            absolute_valuation += f"<tr><td>错误</td><td>DCF估值计算失败: {main_dcf_result.get('error')}</td></tr>"
        else:
            absolute_valuation += "<tr><td>结果</td><td>无有效的DCF估值结果。</td></tr>"
        absolute_valuation += "</table>"

        # DDM估值
        absolute_valuation += """
            <h3>DDM估值(股利贴现模型)</h3>
            <table>
                <tr><th>指标</th><th>数值</th></tr>
        """
        main_ddm_result = sd.ddm_vals[0] if sd.ddm_vals and isinstance(sd.ddm_vals, list) and len(sd.ddm_vals) > 0 else None
        if main_ddm_result and main_ddm_result.get("error") is None:
            value_per_share_ddm = main_ddm_result.get('value_per_share')
            if value_per_share_ddm is not None:
                 absolute_valuation += f"<tr><td><b>每股价值</b></td><td><b>{value_per_share_ddm:.2f} 元/股</b></td></tr>"
                 if sd.latest_price is not None and sd.latest_price > 0:
                     premium_ddm = (value_per_share_ddm / sd.latest_price - 1) * 100
                     absolute_valuation += f"<tr><td>相对当前价格</td><td>{premium_ddm:+.2f}%</td></tr>"
            else:
                 absolute_valuation += "<tr><td>每股价值</td><td>N/A</td></tr>"
        elif main_ddm_result and main_ddm_result.get("error"):
            absolute_valuation += f"<tr><td>错误</td><td>DDM估值计算失败: {main_ddm_result.get('error')}</td></tr>"
        else:
            absolute_valuation += "<tr><td>结果</td><td>无有效的DDM估值结果或未执行。</td></tr>"
        absolute_valuation += "</table>"

        # --- 其他分析 ---
        other_analysis = f"""
            <h2>其他分析</h2>
            <h3>股息分析</h3>
            <table>
                <tr><th>指标</th><th>数值</th></tr>
                <tr><td>当前股息率</td><td>{sd.current_yield:.2f}%</td></tr>
                <tr><td>3年平均分红</td><td>{sd.avg_div:.2f} 元/股</td></tr>
                <tr><td>分红支付率</td><td>{sd.payout_ratio:.2f}%</td></tr>
            </table>
            <h3>增长分析</h3>
            <table>
                <tr><th>指标</th><th>数值</th></tr>
                <tr><td>3年净利润CAGR</td><td>{sd.cagr.get('income_3y', 0):.2f}%</td></tr>
                <tr><td>3年营收CAGR</td><td>{sd.cagr.get('revenue_3y', 0):.2f}%</td></tr>
            </table>
        """

        # --- 综合分析 ---
        comprehensive_analysis = "<h2>综合分析</h2>"
        
        # 组合估值
        if hasattr(sd, 'combos_with_margin') and sd.combos_with_margin:
            comprehensive_analysis += """
                <h3>组合估值</h3>
                <table>
                    <tr><th>组合</th><th>估值 (元/股)</th><th>安全边际</th></tr>
            """
            for combo_name, combo_data in sd.combos_with_margin.items():
                if combo_data and combo_data.get('value') is not None:
                    val_str = f"{combo_data['value']:.2f}"
                    margin_str = f"{combo_data['safety_margin_pct']:+.2f}%" if combo_data.get('safety_margin_pct') is not None else "N/A"
                    comprehensive_analysis += f"<tr><td>{combo_name}</td><td>{val_str}</td><td>{margin_str}</td></tr>\n"
                else:
                    comprehensive_analysis += f"<tr><td>{combo_name}</td><td>N/A</td><td>N/A</td></tr>\n"
            comprehensive_analysis += "</table>"
        else:
            comprehensive_analysis += "<p>组合估值: 无数据。</p>"

        # 投资建议
        if hasattr(sd, 'investment_advice') and sd.investment_advice:
            comprehensive_analysis += "<h3>投资建议</h3>"
            advice = sd.investment_advice
            comprehensive_analysis += f"<p><b>建议:</b> {advice.get('advice', 'N/A')}</p>"
            comprehensive_analysis += f"<p><b>理由:</b> {advice.get('reason', 'N/A')}</p>"
            
            min_val = advice.get('min_intrinsic_value')
            max_val = advice.get('max_intrinsic_value')
            avg_val = advice.get('avg_intrinsic_value')
            margin = advice.get('safety_margin_pct')
            
            comprehensive_analysis += "<table><tr><th>指标</th><th>数值</th></tr>"
            if min_val is not None and max_val is not None:
                 comprehensive_analysis += f"<tr><td>核心估值区间</td><td>{min_val:.2f} - {max_val:.2f} 元/股</td></tr>"
            if avg_val is not None:
                 comprehensive_analysis += f"<tr><td>核心平均估值</td><td>{avg_val:.2f} 元/股</td></tr>"
            if margin is not None:
                 comprehensive_analysis += f"<tr><td>安全边际</td><td>{margin:+.2f}%</td></tr>"
            comprehensive_analysis += f"<tr><td>基于</td><td>{advice.get('based_on', 'N/A')}</td></tr></table>"
            comprehensive_analysis += f"<p><b>参考信息:</b> {advice.get('reference_info', 'N/A')}</p>"
        else:
            comprehensive_analysis += "<p>投资建议: 无数据。</p>"
        comprehensive_analysis += "</div>" # Close container

        # --- HTML 结构 ---
        html_content = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>股票估值报告 - {self.stock_code}</title>
            <style>
                /* 保持原有样式 */
                :root {{ --primary-color: #0071e3; --background-color: #f5f5f7; --text-color: #1d1d1f; }}
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Helvetica Neue', sans-serif; margin: 0; padding: 0; color: var(--text-color); background-color: var(--background-color); line-height: 1.6; }}
                .container {{ max-width: 980px; margin: 2rem auto; background: white; padding: 2rem 3rem; border-radius: 18px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }}
                h1 {{ font-size: 2em; color: var(--text-color); margin-bottom: 0.5em; }}
                h2 {{ font-size: 1.5em; color: var(--text-color); border-bottom: 2px solid var(--primary-color); padding-bottom: 0.3em; margin-top: 2em; margin-bottom: 1em; }}
                h3 {{ font-size: 1.2em; color: var(--text-color); margin-top: 1.5em; margin-bottom: 0.8em; }}
                table {{ width: 100%; border-collapse: collapse; margin-bottom: 1.5em; font-size: 0.95em; }}
                th {{ background-color: #eef0f2; color: #555; text-align: left; padding: 0.8em 1em; border-bottom: 1px solid #d2d2d7; font-weight: 600; }}
                td {{ padding: 0.8em 1em; border-bottom: 1px solid #e5e5e5; }}
                tr:last-child td {{ border-bottom: none; }}
                tr:nth-child(even) {{ background-color: #fcfcfd; }}
                p {{ margin-bottom: 1em; }}
                em {{ color: #6e6e73; font-size: 0.9em; }}
                b, strong {{ font-weight: 600; }}
            </style>
        </head>
        <body>
            {basic_info}
            {relative_valuation}
            {absolute_valuation}
            {other_analysis}
            {comprehensive_analysis}
        </body>
        </html>
        """
        return html_content
