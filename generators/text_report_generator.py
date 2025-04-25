import numpy as np
from utils.report_utils import get_recommendation

class TextReportGenerator:
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

    def generate_valuation_report(self, pe_range, pb_range, growth_rates, discount_rates, ev_ebitda_range):
        """生成估值报告"""
        report = []
        
        # 基本信息
        report.append(f"股票代码: {self.stock_info['ts_code']}")
        report.append(f"股票名称: {self.stock_info['name']}")
        report.append(f"当前价格: {self.latest_price:.2f} 元")
        report.append(f"总股本: {self.total_shares/100000000:.2f} 亿股")
        report.append(f"市值: {self.market_cap:.2f} 亿元")
        
        # PE估值
        report.append("\nPE估值:")
        report.append(f"当前PE: {self.pe_history:.2f} 倍")
        for pe in pe_range:
            value = float(pe) * (self.latest_fcff / 100000000) / (self.total_shares / 100000000)
            premium = (value - self.latest_price) / self.latest_price * 100
            report.append(f"PE={pe}: {value:.2f} 元/股 ({premium:+.2f}%)")
        
        # PB估值
        report.append("\nPB估值:")
        report.append(f"当前PB: {self.pb_history:.2f} 倍")
        for pb in pb_range:
            value = float(pb) * self.latest_price / self.pb_history
            premium = (value - self.latest_price) / self.latest_price * 100
            report.append(f"PB={pb}: {value:.2f} 元/股 ({premium:+.2f}%)")
        
        # DCF估值 (FCFF完整资本性支出)
        report.append("\nDCF估值(FCFF完整资本性支出):")
        if self.fcff_full_vals is None:
            report.append("FCFF为负或零，无法进行DCF估值")
        else:
            for val in self.fcff_full_vals:
                report.append(f"增长率={val['growth_rate']:.1%}, 折现率={val['discount_rate']:.1%}: {val['value']:.2f} 元/股 ({val['premium']:+.2f}%)")
        
        # DCF估值 (FCFE完整资本性支出)
        report.append("\nDCF估值(FCFE完整资本性支出):")
        if self.fcfe_full_vals is None:
            report.append("FCFE为负或零，无法进行DCF估值")
        else:
            for val in self.fcfe_full_vals:
                report.append(f"增长率={val['growth_rate']:.1%}, 折现率={val['discount_rate']:.1%}: {val['value']:.2f} 元/股 ({val['premium']:+.2f}%)")
        
        # DCF估值 (FCFE基本资本性支出)
        report.append("\nDCF估值(FCFE基本资本性支出):")
        if self.fcfe_vals is None:
            report.append("FCFE为负或零，无法进行DCF估值")
        else:
            for val in self.fcfe_vals:
                report.append(f"增长率={val['growth_rate']:.1%}, 折现率={val['discount_rate']:.1%}: {val['value']:.2f} 元/股 ({val['premium']:+.2f}%)")
        
        # DCF估值 (FCFF基本资本性支出)
        report.append("\nDCF估值(FCFF基本资本性支出):")
        if self.fcff_vals is None:
            report.append("FCFF为负或零，无法进行DCF估值")
        else:
            for val in self.fcff_vals:
                report.append(f"增长率={val['growth_rate']:.1%}, 折现率={val['discount_rate']:.1%}: {val['value']:.2f} 元/股 ({val['premium']:+.2f}%)")
        
        # EV/EBITDA估值
        report.append("\nEV/EBITDA估值:")
        report.append(f"当前EV/EBITDA: {self.ev_to_ebitda:.2f}")
        for multiple in ev_ebitda_range:
            value = (float(multiple) * self.ebitda - (self.enterprise_value - self.market_cap * 100000000)) / self.total_shares
            premium = (value - self.latest_price) / self.latest_price * 100
            report.append(f"EV/EBITDA={multiple}: {value:.2f} 元/股 ({premium:+.2f}%)")
        
        # 股息分析
        report.append("\n股息分析:")
        report.append(f"当前股息率: {self.current_yield:.2f}%")
        report.append(f"3年平均分红: {self.avg_div:.2f} 元/股")
        report.append(f"分红支付率: {self.payout_ratio:.2f}%")
        
        # 增长分析
        report.append("\n增长分析:")
        report.append(f"3年净利润CAGR: {self.cagr.get('income_3y', 0):.2f}%")
        report.append(f"3年营收CAGR: {self.cagr.get('revenue_3y', 0):.2f}%")
        
        # DDM估值
        report.append("\nDDM估值(股利贴现模型):")
        if self.ddm_vals is None:
            report.append("无有效分红数据，无法进行DDM估值")
        else:
            for val in self.ddm_vals:
                report.append(f"增长率={val['growth_rate']:.1%}, 折现率={val['discount_rate']:.1%}: {val['value']:.2f} 元/股 ({val['premium']:+.2f}%)")
        
        # 综合分析
        report.append("\n\n=== 综合分析 ===")
        
        # 收集所有估值结果
        all_valuations = []
        
        # PE估值
        pe_valuations = []
        for pe in pe_range:
            value = float(pe) * (self.latest_fcff / 100000000) / (self.total_shares / 100000000)
            all_valuations.append(('PE', value))
            pe_valuations.append(value)
        
        # PB估值
        pb_valuations = []
        for pb in pb_range:
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
        for multiple in ev_ebitda_range:
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
        
        # 计算6种组合估值
        report.append("\n六种估值组合:")
        
        # 1. 全部方法
        report.append("\n组合1 (综合):")
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
            report.append(f"综合估值: {weighted_avg:.2f} 元/股")
            premium = (weighted_avg - self.latest_price) / self.latest_price * 100
            report.append(f"相对当前价格: {premium:+.2f}%")
            report.append(f"投资建议: {get_recommendation(premium)}")
        
        # 2. 完整版DCF + 传统方法
        report.append("\n组合2 (绝对（完整） + 相对):")
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
            report.append(f"综合估值: {weighted_avg:.2f} 元/股")
            premium = (weighted_avg - self.latest_price) / self.latest_price * 100
            report.append(f"相对当前价格: {premium:+.2f}%")
            report.append(f"投资建议: {get_recommendation(premium)}")
        
        # 3. 基本版DCF + 传统方法
        report.append("\n组合3 (绝对（基本） + 相对):")
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
            report.append(f"综合估值: {weighted_avg:.2f} 元/股")
            premium = (weighted_avg - self.latest_price) / self.latest_price * 100
            report.append(f"相对当前价格: {premium:+.2f}%")
            report.append(f"投资建议: {get_recommendation(premium)}")
        
        # 4. 仅完整版DCF + DDM
        report.append("\n组合4 (绝对（完整） + 股息):")
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
            report.append(f"综合估值: {weighted_avg:.2f} 元/股")
            premium = (weighted_avg - self.latest_price) / self.latest_price * 100
            report.append(f"相对当前价格: {premium:+.2f}%")
            report.append(f"投资建议: {get_recommendation(premium)}")
        
        # 5. 仅基本版DCF + DDM
        report.append("\n组合5 (绝对（基本） + 股息):")
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
            report.append(f"综合估值: {weighted_avg:.2f} 元/股")
            premium = (weighted_avg - self.latest_price) / self.latest_price * 100
            report.append(f"相对当前价格: {premium:+.2f}%")
            report.append(f"投资建议: {get_recommendation(premium)}")
        
        # 6. 仅传统估值方法
        report.append("\n组合6 (相对):")
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
            report.append(f"综合估值: {weighted_avg:.2f} 元/股")
            premium = (weighted_avg - self.latest_price) / self.latest_price * 100
            report.append(f"相对当前价格: {premium:+.2f}%")
            report.append(f"投资建议: {get_recommendation(premium)}")
        
        # 计算估值区间
        all_values = [v for _, v in all_valuations]
        min_val = min(all_values)
        max_val = max(all_values)
        report.append(f"\n估值区间: {min_val:.2f} - {max_val:.2f} 元/股")
        report.append(f"当前价格: {self.latest_price:.2f} 元/股")
        
        return "\n".join(report)
