class StockData:
    def __init__(self, stock_info, latest_price, total_shares, market_cap, pe_history, pb_history,
                 income_growth, revenue_growth, cagr, latest_fcff, latest_fcfe, fcff_history, fcfe_history,
                 enterprise_value, ebitda, ev_to_ebitda, current_yield, dividend_history, avg_div, payout_ratio,
                 ddm_vals, fcff_full_vals, fcfe_full_vals, fcfe_vals, fcff_vals,
                 pe_range=[5, 10, 15, 20, 25, 30], 
                 pb_range=[0.5, 1.0, 1.5, 2.0, 2.5, 3.0],
                 ev_ebitda_range=[5, 10, 15, 20, 25, 30]):
        # 确保必要字段存在
        required_fields = {
            'ts_code': self.ts_code if hasattr(self, 'ts_code') else 'N/A',
            'name': '未知名称',
            'industry': '未知'
        }
        for field, default in required_fields.items():
            if field not in stock_info or stock_info[field] is None:
                stock_info[field] = default
                
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
        self.pe_range = pe_range
        self.pb_range = pb_range
        self.ev_ebitda_range = ev_ebitda_range
        self.all_valuations = []
        self.combo_valuations = {}
