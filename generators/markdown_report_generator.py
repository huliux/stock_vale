import pandas as pd
import numpy as np
from utils.report_utils import get_recommendation
from .base_report_generator import BaseReportGenerator

class MarkdownReportGenerator(BaseReportGenerator):
    def __init__(self, stock_data):
        super().__init__(stock_data)
        # Ensure all required attributes are correctly inherited from BaseReportGenerator
        self.min_val = 0 # Specific calculation result holder
        self.max_val = 0 # Specific calculation result holder
        self.latest_price = getattr(stock_data, 'latest_price', None)
        self.pb_history = getattr(stock_data, 'pb_history', None)
        
        # Initialize default ranges if not set by BaseReportGenerator
        self.pe_range = getattr(self, 'pe_range', [5, 8, 12])
        self.pb_range = getattr(self, 'pb_range', [0.8, 1.2, 1.5])
        self.ev_ebitda_range = getattr(self, 'ev_ebitda_range', [6, 8, 10])

    def generate_markdown_report(self):
        """生成Markdown格式的估值报告"""
        md = f"""# 股票估值报告 - {self.stock_data.stock_info['ts_code']} {self.stock_data.stock_info['name']}

*生成日期: {pd.Timestamp.now().strftime('%Y年%m月%d日')}*

## 基本信息

| 项目 | 数值 |
|------|------|
| 股票代码 | {self.stock_data.stock_info['ts_code']} |
| 股票名称 | {self.stock_data.stock_info['name']} |
| 当前价格 | {self.stock_data.latest_price:.2f} 元 |
| 总股本 | {self.stock_data.total_shares/100000000:.2f} 亿股 |
| 市值 | {self.stock_data.market_cap:.2f} 亿元 |

## 相对估值

### PE估值

| 指标 | 估值 | 相对当前价格 |
|------|------|------------|
| 当前PE | {self.stock_data.pe_history:.2f} | - |
"""
        
        # PE估值
        pe_vals = self._calculate_pe_valuations()
        for val in pe_vals:
            md += f"| PE={val['pe']} | {val['value']:.2f} 元/股 | {val['premium']:+.2f}% |\n"
        
        md += f"""
### PB估值

| 指标 | 估值 | 相对当前价格 |
|------|------|------------|
| 当前PB | {self.stock_data.pb_history:.2f} | - |
"""
        
        # PB估值
        pb_vals = self._calculate_pb_valuations()
        for val in pb_vals:
            md += f"| PB={val['pb']} | {val['value']:.2f} 元/股 | {val['premium']:+.2f}% |\n"
        
        md += f"""
### EV/EBITDA估值

| 指标 | 估值 | 相对当前价格 |
|------|------|------------|
| 当前EV/EBITDA | {self.stock_data.ev_to_ebitda:.2f} | - |
"""
        
        # EV/EBITDA估值
        ev_vals = self._calculate_ev_valuations()
        for val in ev_vals:
            md += f"| EV/EBITDA={val['ev_ebitda']} | {val['value']:.2f} 元/股 | {val['premium']:+.2f}% |\n"
        
        md += """
## 绝对估值

### DCF估值(FCFF基本资本性支出)

| 增长率 | 折现率 | 估值 | 相对当前价格 |
|-------|-------|------|------------|
"""

        # DCF估值 (FCFF基本)
        if self.fcff_vals is None:
            md += "| - | - | FCFF为负或零，无法进行DCF估值 | - |\n"
        else:
            for val in self.fcff_vals:
                md += f"| {val['growth_rate']:.1%} | {val['discount_rate']:.1%} | {val['value']:.2f} 元/股 | {val['premium']:+.2f}% |\n"
        
        md += """
### DCF估值(FCFF完整资本性支出)

| 增长率 | 折现率 | 估值 | 相对当前价格 |
|-------|-------|------|------------|
"""

        # DCF估值 (FCFF完整)
        if self.fcff_full_vals is None:
            md += "| - | - | FCFF为负或零，无法进行DCF估值 | - |\n"
        else:
            for val in self.fcff_full_vals:
                md += f"| {val['growth_rate']:.1%} | {val['discount_rate']:.1%} | {val['value']:.2f} 元/股 | {val['premium']:+.2f}% |\n"
        
        md += """
### DCF估值(FCFE基本资本性支出)

| 增长率 | 折现率 | 估值 | 相对当前价格 |
|-------|-------|------|------------|
"""

        # DCF估值 (FCFE基本)
        if self.fcfe_vals is None:
            md += "| - | - | FCFE为负或零，无法进行DCF估值 | - |\n"
        else:
            for val in self.fcfe_vals:
                md += f"| {val['growth_rate']:.1%} | {val['discount_rate']:.1%} | {val['value']:.2f} 元/股 | {val['premium']:+.2f}% |\n"
        
        md += """
### DCF估值(FCFE完整资本性支出)

| 增长率 | 折现率 | 估值 | 相对当前价格 |
|-------|-------|------|------------|
"""

        # DCF估值 (FCFE完整)
        if self.fcfe_full_vals is None:
            md += "| - | - | FCFE为负或零，无法进行DCF估值 | - |\n"
        else:
            for val in self.fcfe_full_vals:
                md += f"| {val['growth_rate']:.1%} | {val['discount_rate']:.1%} | {val['value']:.2f} 元/股 | {val['premium']:+.2f}% |\n"
        
        md += """
### DDM估值(股利贴现模型)

| 增长率 | 折现率 | 估值 | 相对当前价格 |
|-------|-------|------|------------|
"""

        # DDM估值
        if self.ddm_vals is None:
            md += "| - | - | 无有效分红数据，无法进行DDM估值 | - |\n"
        else:
            for val in self.ddm_vals:
                md += f"| {val['growth_rate']:.1%} | {val['discount_rate']:.1%} | {val['value']:.2f} 元/股 | {val['premium']:+.2f}% |\n"
        
        md += f"""
## 其他分析

### 股息分析

| 指标 | 数值 |
|------|------|
| 当前股息率 | {self.stock_data.current_yield:.2f}% |
| 3年平均分红 | {self.stock_data.avg_div:.2f} 元/股 |
| 分红支付率 | {self.stock_data.payout_ratio:.2f}% |

### 增长分析

| 指标 | 数值 |
|------|------|
| 3年净利润CAGR | {self.stock_data.cagr.get('income_3y', 0):.2f}% |
| 3年营收CAGR | {self.stock_data.cagr.get('revenue_3y', 0):.2f}% |

## 综合分析

**估值区间: {self.min_val:.2f} - {self.max_val:.2f} 元/股**

**当前价格: {self.stock_data.latest_price:.2f} 元/股**

### 六种估值组合

| 组合 | 综合估值 | 相对当前价格 | 投资建议 |
|------|---------|------------|---------|
"""

        # 收集所有估值结果
        all_valuations = []
        
        # PE估值
        pe_valuations = []
        if self.latest_fcff != 0 and self.total_shares != 0:
            for pe in self.pe_range:
                value = float(pe) * (self.latest_fcff / 100000000) / (self.total_shares / 100000000)
                all_valuations.append(('PE', value))
                pe_valuations.append(value)
        
        # PB估值
        pb_valuations = []
        if self.pb_history != 0:
            for pb in self.pb_range:
                value = float(pb) * self.latest_price / self.pb_history
                all_valuations.append(('PB', value))
                pb_valuations.append(value)
        
        # DCF估值 (FCFF基本版)
        fcff_basic_valuations = []
        if self.fcff_vals:
            for val in self.fcff_vals:
                all_valuations.append(('DCF(FCFF基本)', val['value']))
                fcff_basic_valuations.append(val['value'])
        
        # DCF估值 (FCFF完整版)
        fcff_full_valuations = []
        if self.fcff_full_vals:
            for val in self.fcff_full_vals:
                all_valuations.append(('DCF(FCFF完整)', val['value']))
                fcff_full_valuations.append(val['value'])
        
        # DCF估值 (FCFE基本版)
        fcfe_basic_valuations = []
        if self.fcfe_vals:
            for val in self.fcfe_vals:
                all_valuations.append(('DCF(FCFE基本)', val['value']))
                fcfe_basic_valuations.append(val['value'])
        
        # DCF估值 (FCFE完整版)
        fcfe_full_valuations = []
        if self.fcfe_full_vals:
            for val in self.fcfe_full_vals:
                all_valuations.append(('DCF(FCFE完整)', val['value']))
                fcfe_full_valuations.append(val['value'])
        
        # DDM估值
        ddm_valuations = []
        if self.ddm_vals:
            for val in self.ddm_vals:
                all_valuations.append(('DDM', val['value']))
                ddm_valuations.append(val['value'])
        
        # EV/EBITDA估值
        ev_ebitda_valuations = []
        for multiple in self.ev_ebitda_range:
            value = (float(multiple) * self.ebitda - (self.enterprise_value - self.market_cap * 100000000)) / self.total_shares
            all_valuations.append(('EV/EBITDA', value))
            ev_ebitda_valuations.append(value)
        
        # 计算各方法的中位数
        method_medians = {}
        if pe_valuations:
            method_medians['PE'] = np.median(pe_valuations)
        if pb_valuations:
            method_medians['PB'] = np.median(pb_valuations)
        if fcff_basic_valuations:
            method_medians['DCF(FCFF基本)'] = np.median(fcff_basic_valuations)
        if fcff_full_valuations:
            method_medians['DCF(FCFF完整)'] = np.median(fcff_full_valuations)
        if fcfe_basic_valuations:
            method_medians['DCF(FCFE基本)'] = np.median(fcfe_basic_valuations)
        if fcfe_full_valuations:
            method_medians['DCF(FCFE完整)'] = np.median(fcfe_full_valuations)
        if ddm_valuations:
            method_medians['DDM'] = np.median(ddm_valuations)
        if ev_ebitda_valuations:
            method_medians['EV/EBITDA'] = np.median(ev_ebitda_valuations)
        
        # 计算估值区间
        all_values = [v for _, v in all_valuations]
        self.min_val = min(all_values)
        self.max_val = max(all_values)
        
        # 1. 全部方法
        weights_all = {
            'DCF(FCFF基本)': 0.1, 'DCF(FCFE基本)': 0.1,
            'DCF(FCFF完整)': 0.1, 'DCF(FCFE完整)': 0.1,
            'DDM': 0.2, 'PE': 0.15, 'PB': 0.1, 'EV/EBITDA': 0.15
        }
        weighted_sum = 0
        total_weight = 0
        for method, median in method_medians.items():
            if method in weights_all:
                weighted_sum += median * weights_all[method]
                total_weight += weights_all[method]
        
        if total_weight > 0:
            weighted_avg = weighted_sum / total_weight
            premium = (weighted_avg - self.latest_price) / self.latest_price * 100
            
            if premium > 30:
                recommendation = "强烈买入"
            elif premium > 15:
                recommendation = "买入"
            elif premium > -10:
                recommendation = "持有"
            elif premium > -30:
                recommendation = "减持"
            else:
                recommendation = "强烈卖出"
            
            md += f"| 组合1 (综合) | {weighted_avg:.2f} 元/股 | {premium:+.2f}% | {recommendation} |\n"
        
        # 2. 完整版DCF + 传统方法
        weights_full_dcf = {
            'DCF(FCFF完整)': 0.2, 'DCF(FCFE完整)': 0.2,
            'DDM': 0.2, 'PE': 0.15, 'PB': 0.1, 'EV/EBITDA': 0.15
        }
        weighted_sum = 0
        total_weight = 0
        for method, median in method_medians.items():
            if method in weights_full_dcf:
                weighted_sum += median * weights_full_dcf[method]
                total_weight += weights_full_dcf[method]
        
        if total_weight > 0:
            weighted_avg = weighted_sum / total_weight
            premium = (weighted_avg - self.latest_price) / self.latest_price * 100
            
            if premium > 30:
                recommendation = "强烈买入"
            elif premium > 15:
                recommendation = "买入"
            elif premium > -30:
                recommendation = "持有"
            elif premium > -30:
                recommendation = "减持"
            else:
                recommendation = "强烈卖出"
            
            md += f"| 组合2 (绝对（完整） + 相对) | {weighted_avg:.2f} 元/股 | {premium:+.2f}% | {recommendation} |\n"
        
        # 3. 基本版DCF + 传统方法
        weights_basic_dcf = {
            'DCF(FCFF基本)': 0.2, 'DCF(FCFE基本)': 0.2,
            'DDM': 0.2, 'PE': 0.15, 'PB': 0.1, 'EV/EBITDA': 0.15
        }
        weighted_sum = 0
        total_weight = 0
        for method, median in method_medians.items():
            if method in weights_basic_dcf:
                weighted_sum += median * weights_basic_dcf[method]
                total_weight += weights_basic_dcf[method]
        
        if total_weight > 0:
            weighted_avg = weighted_sum / total_weight
            premium = (weighted_avg - self.latest_price) / self.latest_price * 100
            
            if premium > 30:
                recommendation = "强烈买入"
            elif premium > 15:
                recommendation = "买入"
            elif premium > -30:
                recommendation = "持有"
            elif premium > -30:
                recommendation = "减持"
            else:
                recommendation = "强烈卖出"
            
            md += f"| 组合3 (绝对（基本） + 相对) | {weighted_avg:.2f} 元/股 | {premium:+.2f}% | {recommendation} |\n"
        
        # 4. 仅完整版DCF + DDM
        weights_full_dcf_ddm = {
            'DCF(FCFF完整)': 0.4, 'DCF(FCFE完整)': 0.4, 'DDM': 0.2
        }
        weighted_sum = 0
        total_weight = 0
        for method, median in method_medians.items():
            if method in weights_full_dcf_ddm:
                weighted_sum += median * weights_full_dcf_ddm[method]
                total_weight += weights_full_dcf_ddm[method]
        
        if total_weight > 0:
            weighted_avg = weighted_sum / total_weight
            premium = (weighted_avg - self.latest_price) / self.latest_price * 100
            
            if premium > 30:
                recommendation = "强烈买入"
            elif premium > 15:
                recommendation = "买入"
            elif premium > -30:
                recommendation = "持有"
            elif premium > -30:
                recommendation = "减持"
            else:
                recommendation = "强烈卖出"
            
            md += f"| 组合4 (绝对（完整） + 股息) | {weighted_avg:.2f} 元/股 | {premium:+.2f}% | {recommendation} |\n"
        
        # 5. 仅基本版DCF + DDM
        weights_basic_dcf_ddm = {
            'DCF(FCFF基本)': 0.4, 'DCF(FCFE基本)': 0.4, 'DDM': 0.2
        }
        weighted_sum = 0
        total_weight = 0
        for method, median in method_medians.items():
            if method in weights_basic_dcf_ddm:
                weighted_sum += median * weights_basic_dcf_ddm[method]
                total_weight += weights_basic_dcf_ddm[method]
        
        if total_weight > 0:
            weighted_avg = weighted_sum / total_weight
            premium = (weighted_avg - self.latest_price) / self.latest_price * 100
            
            if premium > 30:
                recommendation = "强烈买入"
            elif premium > 15:
                recommendation = "买入"
            elif premium > -30:
                recommendation = "持有"
            elif premium > -30:
                recommendation = "减持"
            else:
                recommendation = "强烈卖出"
            
            md += f"| 组合5 (绝对（基本） + 股息) | {weighted_avg:.2f} 元/股 | {premium:+.2f}% | {recommendation} |\n"
        
        # 6. 仅传统估值方法
        weights_traditional = {
            'PE': 0.4, 'PB': 0.3, 'EV/EBITDA': 0.3
        }
        weighted_sum = 0
        total_weight = 0
        for method, median in method_medians.items():
            if method in weights_traditional:
                weighted_sum += median * weights_traditional[method]
                total_weight += weights_traditional[method]
        
        if total_weight > 0:
            weighted_avg = weighted_sum / total_weight
            premium = (weighted_avg - self.latest_price) / self.latest_price * 100
            
            if premium > 30:
                recommendation = "强烈买入"
            elif premium > 15:
                recommendation = "买入"
            elif premium > -30:
                recommendation = "持有"
            elif premium > -30:
                recommendation = "减持"
            else:
                recommendation = "强烈卖出"
            
            md += f"| 组合6 (相对) | {weighted_avg:.2f} 元/股 | {premium:+.2f}% | {recommendation} |\n"
        
        return md
