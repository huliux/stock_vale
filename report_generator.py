"""模块文档字符串：包含生成不同格式股票估值报告的功能"""

import generators.text_report_generator
import generators.markdown_report_generator
import generators.html_report_generator
from models.stock_data import StockData

class ReportGenerator:
    """类文档字符串：用于生成股票的文本和Markdown格式的估值报告"""
    def __init__(self, stock_data):
        if not isinstance(stock_data, StockData):
            raise ValueError("stock_data must be an instance of StockData")
        self.stock_data = stock_data

    def generate_valuation_report(self, pe_range, pb_range, growth_rates, discount_rates, ev_ebitda_range):
        """生成估值报告并计算组合估值"""
        # 设置估值范围
        self.stock_data.pe_range = pe_range
        self.stock_data.pb_range = pb_range
        self.stock_data.ev_ebitda_range = ev_ebitda_range
        
        # 计算组合估值
        self._calculate_combo_valuations()
        
        text_report_generator = generators.text_report_generator.TextReportGenerator(
            self.stock_data.stock_info, self.stock_data.latest_price, self.stock_data.total_shares,
            self.stock_data.market_cap, self.stock_data.pe_history, self.stock_data.pb_history,
            self.stock_data.income_growth, self.stock_data.revenue_growth, self.stock_data.cagr,
            self.stock_data.latest_fcff, self.stock_data.latest_fcfe, self.stock_data.fcff_history,
            self.stock_data.fcfe_history, self.stock_data.enterprise_value, self.stock_data.ebitda,
            self.stock_data.ev_to_ebitda, self.stock_data.current_yield, self.stock_data.dividend_history,
            self.stock_data.avg_div, self.stock_data.payout_ratio, self.stock_data.ddm_vals,
            self.stock_data.fcff_full_vals, self.stock_data.fcfe_full_vals, self.stock_data.fcfe_vals,
            self.stock_data.fcff_vals
        )
        return text_report_generator.generate_valuation_report(
            pe_range, pb_range, growth_rates, discount_rates, ev_ebitda_range
        )

    def _calculate_combo_valuations(self):
        """计算六种估值组合"""
        # print("\n[DEBUG] 开始计算组合估值...")
        # 收集所有估值结果
        all_valuations = []
        
        # PE估值
        pe_vals = [float(pe) * (self.stock_data.latest_fcff / 100000000) / (self.stock_data.total_shares / 100000000) 
                  for pe in self.stock_data.pe_range]
        all_valuations.extend(pe_vals)
        
        # PB估值
        pb_vals = [float(pb) * self.stock_data.latest_price / self.stock_data.pb_history 
                  for pb in self.stock_data.pb_range]
        all_valuations.extend(pb_vals)
        
        # EV/EBITDA估值
        ev_vals = [(float(multiple) * self.stock_data.ebitda - (self.stock_data.enterprise_value - self.stock_data.market_cap * 100000000)) / self.stock_data.total_shares
                  for multiple in self.stock_data.ev_ebitda_range]
        all_valuations.extend(ev_vals)
        
        # DCF估值 (FCFF基本版)
        if self.stock_data.fcff_vals:
            all_valuations.extend([val['value'] for val in self.stock_data.fcff_vals])
        
        # DCF估值 (FCFF完整版)
        if self.stock_data.fcff_full_vals:
            all_valuations.extend([val['value'] for val in self.stock_data.fcff_full_vals])
        
        # DCF估值 (FCFE基本版)
        if self.stock_data.fcfe_vals:
            all_valuations.extend([val['value'] for val in self.stock_data.fcfe_vals])
        
        # DCF估值 (FCFE完整版)
        if self.stock_data.fcfe_full_vals:
            all_valuations.extend([val['value'] for val in self.stock_data.fcfe_full_vals])
        
        # DDM估值
        if self.stock_data.ddm_vals:
            all_valuations.extend([val['value'] for val in self.stock_data.ddm_vals])
        
        # 计算各组合估值
        if all_valuations:
            # 组合1: 全部方法
            self.stock_data.combo_valuations['综合'] = sum(all_valuations) / len(all_valuations)
            
            # 组合2: 完整DCF + 传统方法
            full_dcf_vals = []
            if self.stock_data.fcff_full_vals:
                full_dcf_vals.extend([val['value'] for val in self.stock_data.fcff_full_vals])
            if self.stock_data.fcfe_full_vals:
                full_dcf_vals.extend([val['value'] for val in self.stock_data.fcfe_full_vals])
            if full_dcf_vals and pe_vals and pb_vals and ev_vals:
                self.stock_data.combo_valuations['绝对(完整)+相对'] = (sum(full_dcf_vals) * 0.4 + sum(pe_vals) * 0.2 + sum(pb_vals) * 0.2 + sum(ev_vals) * 0.2) / (len(full_dcf_vals) * 0.4 + len(pe_vals) * 0.2 + len(pb_vals) * 0.2 + len(ev_vals) * 0.2)
            
            # 组合3: 基本DCF + 传统方法
            basic_dcf_vals = []
            if self.stock_data.fcff_vals:
                basic_dcf_vals.extend([val['value'] for val in self.stock_data.fcff_vals])
            if self.stock_data.fcfe_vals:
                basic_dcf_vals.extend([val['value'] for val in self.stock_data.fcfe_vals])
            if basic_dcf_vals and pe_vals and pb_vals and ev_vals:
                self.stock_data.combo_valuations['绝对(基本)+相对'] = (sum(basic_dcf_vals) * 0.4 + sum(pe_vals) * 0.2 + sum(pb_vals) * 0.2 + sum(ev_vals) * 0.2) / (len(basic_dcf_vals) * 0.4 + len(pe_vals) * 0.2 + len(pb_vals) * 0.2 + len(ev_vals) * 0.2)
            
            # 组合4: 完整DCF + DDM
            if full_dcf_vals and self.stock_data.ddm_vals:
                self.stock_data.combo_valuations['绝对(完整)+股息'] = (sum(full_dcf_vals) * 0.7 + sum([val['value'] for val in self.stock_data.ddm_vals]) * 0.3) / (len(full_dcf_vals) * 0.7 + len(self.stock_data.ddm_vals) * 0.3)
            
            # 组合5: 基本DCF + DDM
            if basic_dcf_vals and self.stock_data.ddm_vals:
                self.stock_data.combo_valuations['绝对(基本)+股息'] = (sum(basic_dcf_vals) * 0.7 + sum([val['value'] for val in self.stock_data.ddm_vals]) * 0.3) / (len(basic_dcf_vals) * 0.7 + len(self.stock_data.ddm_vals) * 0.3)
            
            # 组合6: 仅传统方法
            if pe_vals and pb_vals and ev_vals:
                self.stock_data.combo_valuations['相对'] = (sum(pe_vals) * 0.4 + sum(pb_vals) * 0.3 + sum(ev_vals) * 0.3) / (len(pe_vals) * 0.4 + len(pb_vals) * 0.3 + len(ev_vals) * 0.3)
            
        # print(f"[DEBUG] 组合估值结果: {self.stock_data.combo_valuations}")

    def generate_html_report(self):
        """生成HTML格式的估值报告"""
        # 先填充估值数据
        self.generate_valuation_report(
            pe_range=[5, 10, 15, 20, 25, 30],
            pb_range=[0.5, 1.0, 1.5, 2.0, 2.5, 3.0],
            growth_rates=[0.03, 0.05, 0.07, 0.10],
            discount_rates=[0.08, 0.10, 0.12, 0.15],
            ev_ebitda_range=[5, 10, 15, 20, 25, 30]
        )
        
        html_report_generator = generators.html_report_generator.HtmlReportGenerator(
            self.stock_data
        )
        return html_report_generator.generate_html_report()

    def export_html_report(self):
        """导出HTML格式的估值报告到文件"""
        html_report_generator = generators.html_report_generator.HtmlReportGenerator(
            self.stock_data
        )
        return html_report_generator.export_report()

    def generate_markdown_report(self):
        """生成Markdown格式的估值报告"""
        markdown_report_generator = generators.markdown_report_generator.MarkdownReportGenerator(
            self.stock_data
        )
        return markdown_report_generator.generate_markdown_report()
