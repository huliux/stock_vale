from typing import Optional, Dict, Any, List

class StockData:
    def __init__(self, 
                 stock_info: Dict[str, Any], 
                 latest_price: Optional[float], 
                 total_shares: Optional[float], 
                 market_cap: Optional[float], 
                 pe_history: Optional[float], 
                 pb_history: Optional[float],
                 income_growth: List[Dict[str, Any]], # 可能仍用于历史展示
                 revenue_growth: List[Dict[str, Any]], # 可能仍用于历史展示
                 cagr: Dict[str, float], # 可能仍用于历史展示
                 latest_fcff: Optional[float], # 可能被 main_dcf_result 替代或用于历史展示
                 latest_fcfe: Optional[float], # 可能被 main_dcf_result 替代或用于历史展示
                 fcff_history: List[Dict[str, Any]], # 可能仍用于历史展示
                 fcfe_history: List[Dict[str, Any]], # 可能仍用于历史展示
                 enterprise_value: Optional[float], # 历史 EV
                 ebitda: Optional[float], # 历史 EBITDA
                 ev_to_ebitda: Optional[float], # 历史 EV/EBITDA
                 current_yield: Optional[float], 
                 dividend_history: List[Dict[str, Any]], 
                 avg_div: Optional[float], 
                 payout_ratio: Optional[float],
                 # 移除旧的估值结果列表参数
                 # ddm_vals, fcff_full_vals, fcfe_full_vals, fcfe_vals, fcff_vals,
                 pe_range: List[str] = ['5', '10', '15', '20', '25', '30'], 
                 pb_range: List[str] = ['0.5', '1.0', '1.5', '2.0', '2.5', '3.0'],
                 ev_ebitda_range: List[str] = ['5', '10', '15', '20', '25', '30'],
                 # 新增参数用于存储新的估值结果
                 main_dcf_result: Optional[Dict[str, Any]] = None,
                 combos_with_margin: Optional[Dict[str, Optional[Dict[str, Any]]]] = None, # 字典的值可能是 None
                 investment_advice: Optional[Dict[str, Any]] = None
                 ):
        # 确保必要字段存在
        required_fields = {
            'ts_code': 'N/A',
            'name': '未知名称',
            'industry': '未知'
        }
        stock_info = stock_info or {} # 确保 stock_info 不是 None
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
        self.cagr = cagr if isinstance(cagr, dict) else {} # 确保 cagr 是字典
        self.latest_fcff = latest_fcff
        self.latest_fcfe = latest_fcfe
        self.fcff_history = fcff_history
        self.fcfe_history = fcfe_history
        self.enterprise_value = enterprise_value # 历史 EV
        self.ebitda = ebitda # 历史 EBITDA
        self.ev_to_ebitda = ev_to_ebitda # 历史 EV/EBITDA
        self.current_yield = current_yield
        self.dividend_history = dividend_history
        self.avg_div = avg_div
        self.payout_ratio = payout_ratio
        
        # 移除旧的估值结果属性
        # self.ddm_vals = ddm_vals
        # self.fcff_full_vals = fcff_full_vals # 将被 main_dcf_result 替代
        # self.fcfe_full_vals = fcfe_full_vals
        # self.fcfe_vals = fcfe_vals
        # self.fcff_vals = fcff_vals
        
        self.pe_range = pe_range
        self.pb_range = pb_range
        self.ev_ebitda_range = ev_ebitda_range
        
        # 存储新的估值结果
        # 注意：main.py 中将 dcf_results 包装在列表中存入 fcff_full_vals，这里直接存储字典
        self.main_dcf_result = main_dcf_result if isinstance(main_dcf_result, dict) else None
        self.combos_with_margin = combos_with_margin if isinstance(combos_with_margin, dict) else {}
        self.investment_advice = investment_advice if isinstance(investment_advice, dict) else {}

        # 兼容旧报告生成器（如果它们直接访问这些属性）
        # 将 main_dcf_result 放入 fcff_full_vals 列表中
        self.fcff_full_vals = [self.main_dcf_result] if self.main_dcf_result else []
        # 其他旧列表置空
        self.ddm_vals = [] 
        self.fcfe_full_vals = []
        self.fcfe_vals = []
        self.fcff_vals = []

        # 移除旧的 combo_valuations 属性，因为它被 combos_with_margin 取代
        # self.combo_valuations = {} 
        # self.all_valuations = [] # 这个属性似乎未使用，也移除
