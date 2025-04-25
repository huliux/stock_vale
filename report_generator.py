"""模块文档字符串：包含生成不同格式股票估值报告的功能"""

import generators.text_report_generator
import generators.markdown_report_generator
from models.stock_data import StockData

class ReportGenerator:
    """类文档字符串：用于生成股票的文本和Markdown格式的估值报告"""
    def __init__(self, stock_data):
        if not isinstance(stock_data, StockData):
            raise ValueError("stock_data must be an instance of StockData")
        self.stock_data = stock_data

    def generate_valuation_report(self, pe_range, pb_range, growth_rates, discount_rates, ev_ebitda_range):
        """生成估值报告"""
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

    def generate_markdown_report(self, pe_range, pb_range, growth_rates, discount_rates, ev_ebitda_range):
        """生成Markdown格式的估值报告"""
        markdown_report_generator = generators.markdown_report_generator.MarkdownReportGenerator(
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
        return markdown_report_generator.generate_markdown_report(
            pe_range, pb_range, growth_rates, discount_rates, ev_ebitda_range
        )
