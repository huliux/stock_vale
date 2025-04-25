import pandas as pd
from utils.report_utils import get_recommendation

class MarkdownReportGenerator:
    def __init__(self, stock_info, latest_price, total_shares, market_cap, pe_history, pb_history,
                 income_growth, revenue_growth, cagr, latest_fcff, latest_fcfe, fcff_history, fcfe_history,
                 enterprise_value, ebitda, ev_to_ebitda, current_yield, dividend_history, avg_div, payout_ratio,
                 ddm_vals, fcff_full_vals, fcfe_full_vals, fcfe_vals, fcff_vals):
        self.stock_info = stock_info
        self.latest_price = latest_price
        self.total_shares = total_shares
        self.market_cap = market_cap
        self.pe_history = pe_history
        self.pb_history = pb_history
        self.income_growth = income_growth
        self.revenue_growth = revenue_growth
        self.cagr = cagr
        self.latest_fcff = latest_fcff
        self.latest_fcfe = latest_fcfe
        self.fcff_history = fcff_history
        self.fcfe_history = fcfe_history
        self.enterprise_value = enterprise_value
        self.ebitda = ebitda
        self.ev_to_ebitda = ev_to_ebitda
        self.current_yield = current_yield
        self.dividend_history = dividend_history
        self.avg_div = avg_div
        self.payout_ratio = payout_ratio
        self.ddm_vals = ddm_vals
        self.fcff_full_vals = fcff_full_vals
        self.fcfe_full_vals = fcfe_full_vals
        self.fcfe_vals = fcfe_vals
        self.fcff_vals = fcff_vals

    def generate_markdown_report(self, pe_range, pb_range, growth_rates, discount_rates, ev_ebitda_range):
        """生成Markdown格式的估值报告"""
        md = f"""# 股票估值报告 - {self.stock_info['ts_code']} {self.stock_info['name']}

*生成日期: {pd.Timestamp.now().strftime('%Y年%m月%d日')}*

## 基本信息

| 项目 | 数值 |
|------|------|
| 股票代码 | {self.stock_info['ts_code']} |
| 股票名称 | {self.stock_info['name']} |
| 当前价格 | {self.latest_price:.2f} 元 |
| 总股本 | {self.total_shares/100000000:.2f} 亿股 |
| 市值 | {self.market_cap:.2f} 亿元 |

## 相对估值

### PE估值

| 指标 | 估值 | 相对当前价格 |
|------|------|------------|
| 当前PE | {self.pe_history:.2f} | - |
"""
        
        # PE估值
        for pe in pe_range:
            value = float(pe) * (self.latest_fcff / 100000000) / (self.total_shares / 100000000)
            premium = (value - self.latest_price) / self.latest_price * 100
            md += f"| PE={pe} | {value:.2f} 元/股 | {premium:+.2f}% |\n"
        
        md += f"""
### PB估值

| 指标 | 估值 | 相对当前价格 |
|------|------|------------|
| 当前PB | {self.pb_history:.2f} | - |
"""
        
        # PB估值
        for pb in pb_range:
            value = float(pb) * self.latest_price / self.pb_history
            premium = (value - self.latest_price) / self.latest_price * 100
            md += f"| PB={pb} | {value:.2f} 元/股 | {premium:+.2f}% |\n"
        
        md += f"""
### EV/EBITDA估值

| 指标 | 估值 | 相对当前价格 |
|------|------|------------|
| 当前EV/EBITDA | {self.ev_to_ebitda:.2f} | - |
"""
        
        # EV/EBITDA估值
        for multiple in ev_ebitda_range:
            value = (float(multiple) * self.ebitda - (self.enterprise_value - self.market_cap * 100000000)) / self.total_shares
            premium = (value - self.latest_price) / self.latest_price * 100
            md += f"| EV/EBITDA={multiple} | {value:.2f} 元/股 | {premium:+.2f}% |\n"
        
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
| 当前股息率 | {self.current_yield:.2f}% |
| 3年平均分红 | {self.avg_div:.2f} 元/股 |
| 分红支付率 | {self.payout_ratio:.2f}% |

### 增长分析

| 指标 | 数值 |
|------|------|
| 3年净利润CAGR | {self.cagr.get('income_3y', 0):.2f}% |
| 3年营收CAGR | {self.cagr.get('revenue_3y', 0):.2f}% |

## 估值方法说明

| 估值方法 | 说明 |
|---------|------|
| PE估值 | 市盈率估值，基于公司每股收益与市场给予的估值倍数 |
| PB估值 | 市净率估值，基于公司每股净资产与市场给予的估值倍数 |
| EV/EBITDA估值 | 企业价值倍数估值，考虑公司债务情况的综合估值方法 |
| DCF(FCFF基本) | 基本资本性支出的企业自由现金流贴现模型 |
| DCF(FCFF完整) | 完整资本性支出(含投资支出)的企业自由现金流贴现模型 |
| DCF(FCFE基本) | 基本资本性支出的股权自由现金流贴现模型 |
| DCF(FCFE完整) | 完整资本性支出(含投资支出)的股权自由现金流贴现模型 |
| DDM | 股利贴现模型，基于公司历史分红情况的估值方法 |

## 投资建议标准

| 建议 | 标准 |
|------|------|
| 强烈买入 | 估值溢价 > 30% |
| 买入 | 估值溢价 15% ~ 30% |
| 持有 | 估值溢价 -10% ~ 15% |
| 减持 | 估值溢价 -30% ~ -10% |
| 强烈卖出 | 估值溢价 < -30% |

---

*本报告仅供参考，不构成任何投资建议*
"""
        
        return md
