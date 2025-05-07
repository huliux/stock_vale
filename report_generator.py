"""模块文档字符串：包含生成不同格式股票估值报告的功能"""

import generators.text_report_generator
import generators.markdown_report_generator
import generators.html_report_generator
from models.stock_data import StockData
from typing import List, Dict, Any # 确保类型提示可用

class ReportGenerator:
    """类文档字符串：用于生成股票的文本、Markdown和HTML格式的估值报告"""
    def __init__(self, stock_data: StockData):
        if not isinstance(stock_data, StockData):
            raise ValueError("stock_data must be an instance of StockData")
        self.stock_data = stock_data
        # combo_valuations 和 investment_advice 现在应该由 ValuationCalculator 计算并填充到 stock_data 中
        # 例如: self.stock_data.detailed_combo_valuations 和 self.stock_data.investment_advice

    def generate_text_report(self, 
                             pe_range: List[str], 
                             pb_range: List[str], 
                             ev_ebitda_range: List[str]) -> str:
        """
        生成文本格式的估值报告。
        组合估值和核心DCF结果应已存在于 self.stock_data 中。
        pe_range, pb_range, ev_ebitda_range 用于生成相关的相对估值表格。
        """
        # 假设 TextReportGenerator 的构造函数现在接受 stock_data
        # 并且其 generate_report 方法接受必要的范围参数用于表格显示
        text_report_gen = generators.text_report_generator.TextReportGenerator(self.stock_data)
        
        # TextReportGenerator 的 generate_valuation_report 方法签名也需要相应调整
        # 它可能不再需要 growth_rates, discount_rates 作为核心计算参数
        # 而是从 stock_data.main_dcf_result 或 stock_data.detailed_combo_valuations 获取
        # 此处暂时保留旧的参数传递方式，但 TextReportGenerator 内部实现需要大改
        # TODO: Refactor TextReportGenerator and its method signature
        
        # 简化调用，假设 TextReportGenerator 的 generate_report 方法处理这些范围
        # 或者 TextReportGenerator 从 stock_data 中获取这些范围（如果它们被设置在那里）
        # 为了最小化当前步骤的更改，我们假设 TextReportGenerator 仍然需要这些范围
        # 但它将从 stock_data 获取核心估值数据
        
        # 临时传递旧的 growth_rates 和 discount_rates 为空列表或None，因为它们不再由这里驱动
        # 实际的 WACC 和增长假设在 ValuationCalculator 中处理，并体现在 dcf_results 中
        return text_report_gen.generate_valuation_report(
            pe_range=pe_range,
            pb_range=pb_range,
            growth_rates=[], # 不再由 ReportGenerator 控制核心DCF增长率
            discount_rates=[], # 不再由 ReportGenerator 控制核心DCF折现率
            ev_ebitda_range=ev_ebitda_range
        )

    def generate_markdown_report(self) -> str:
        """生成Markdown格式的估值报告"""
        # 假设 MarkdownReportGenerator 的构造函数现在接受 stock_data
        markdown_report_gen = generators.markdown_report_generator.MarkdownReportGenerator(self.stock_data)
        # 假设其 generate_markdown_report 方法现在从 stock_data 中获取所有需要的信息
        return markdown_report_gen.generate_markdown_report()

    def generate_html_report(self) -> str:
        """生成HTML格式的估值报告"""
        # 假设 HtmlReportGenerator 的构造函数现在接受 stock_data
        html_report_gen = generators.html_report_generator.HtmlReportGenerator(self.stock_data)
        # 假设其 generate_html_report 方法现在从 stock_data 中获取所有需要的信息
        return html_report_gen.generate_html_report()

    def export_html_report(self) -> str:
        """导出HTML格式的估值报告到文件"""
        # 假设 HtmlReportGenerator 的构造函数现在接受 stock_data
        html_report_gen = generators.html_report_generator.HtmlReportGenerator(self.stock_data)
        # 假设其 export_report 方法现在从 stock_data 中获取所有需要的信息
        return html_report_gen.export_report()
