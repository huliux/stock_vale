from models.stock_data import StockData
import numpy as np

class BaseReportGenerator:
    """报告生成器的基类，包含所有估值计算方法"""
    def __init__(self, stock_data):
        if not isinstance(stock_data, StockData):
            raise ValueError("stock_data must be an instance of StockData")
        self.stock_data = stock_data
        self.stock_info = stock_data.stock_info
        self.stock_code = stock_data.stock_info.get('ts_code', 'N/A')
        self.stock_name = stock_data.stock_info.get('name', '未知名称')

        # Initialize all required attributes from stock_data
        self.fcff_vals = getattr(stock_data, 'fcff_vals', None)
        self.fcff_full_vals = getattr(stock_data, 'fcff_full_vals', None)
        self.fcfe_vals = getattr(stock_data, 'fcfe_vals', None)
        self.fcfe_full_vals = getattr(stock_data, 'fcfe_full_vals', None)
        self.ddm_vals = getattr(stock_data, 'ddm_vals', None)
        self.latest_fcff = getattr(stock_data, 'latest_fcff', None)
        self.total_shares = getattr(stock_data, 'total_shares', None)
        self.pb_history = getattr(stock_data, 'pb_history', None)
        self.ebitda = getattr(stock_data, 'ebitda', None)

        # Add initialization for enterprise_value and market_cap
        self.enterprise_value = getattr(stock_data, 'enterprise_value', None)
        self.market_cap = getattr(stock_data, 'market_cap', None)

    def _calculate_pe_valuations(self, pe_range=[5, 8, 12, 15, 20, 25]):
        """计算PE估值"""
        valuations = []
        for pe in pe_range:
            value = float(pe) * (self.stock_data.latest_fcff / 100000000) / (self.stock_data.total_shares / 100000000)
            premium = (value - self.stock_data.latest_price) / self.stock_data.latest_price * 100
            valuations.append({
                'pe': pe,
                'value': value,
                'premium': premium
            })
        return valuations

    def _calculate_pb_valuations(self, pb_range=[0.8, 1.2, 1.5, 2.0, 2.5, 3.0]):
        """计算PB估值"""
        valuations = []
        for pb in pb_range:
            value = float(pb) * self.stock_data.latest_price / self.pb_history
            premium = (value - self.stock_data.latest_price) / self.stock_data.latest_price * 100
            valuations.append({
                'pb': pb,
                'value': value,
                'premium': premium
            })
        return valuations

    def _calculate_ev_valuations(self, ev_ebitda_range=[6, 8, 10, 12, 15, 18]):
        """计算EV/EBITDA估值"""
        valuations = []
        for multiple in ev_ebitda_range:
            value = (float(multiple) * self.ebitda - (self.stock_data.enterprise_value - self.stock_data.market_cap * 100000000)) / self.stock_data.total_shares
            premium = (value - self.stock_data.latest_price) / self.stock_data.latest_price * 100
            valuations.append({
                'ev_ebitda': multiple,
                'value': value,
                'premium': premium
            })
        return valuations

    def _calculate_fcff_valuations(self, growth_rates=[0.05, 0.08, 0.10], discount_rates=[0.10, 0.12, 0.15]):
        """计算FCFF估值"""
        if not self.stock_data.latest_fcff or self.stock_data.latest_fcff <= 0:
            return []
            
        valuations = []
        for g in growth_rates:
            for r in discount_rates:
                try:
                    value = self.stock_data.latest_fcff * (1 + g) / (r - g) / self.stock_data.total_shares
                    premium = (value - self.stock_data.latest_price) / self.stock_data.latest_price * 100
                    valuations.append({
                        'growth_rate': g,
                        'discount_rate': r,
                        'value': value,
                        'premium': premium
                    })
                except ZeroDivisionError:
                    continue
        return valuations

    def _calculate_fcfe_valuations(self, growth_rates=[0.05, 0.08, 0.10], discount_rates=[0.10, 0.12, 0.15]):
        """计算FCFE估值"""
        if not self.stock_data.latest_fcfe or self.stock_data.latest_fcfe <= 0:
            return []
            
        valuations = []
        for g in growth_rates:
            for r in discount_rates:
                try:
                    value = self.stock_data.latest_fcfe * (1 + g) / (r - g) / self.stock_data.total_shares
                    premium = (value - self.stock_data.latest_price) / self.stock_data.latest_price * 100
                    valuations.append({
                        'growth_rate': g,
                        'discount_rate': r,
                        'value': value,
                        'premium': premium
                    })
                except ZeroDivisionError:
                    continue
        return valuations

    def _calculate_ddm_valuations(self, growth_rates=[0.05, 0.08, 0.10], discount_rates=[0.10, 0.12, 0.15]):
        """计算DDM估值"""
        if not self.stock_data.avg_div or self.stock_data.avg_div <= 0:
            return []
            
        valuations = []
        for g in growth_rates:
            for r in discount_rates:
                try:
                    value = self.stock_data.avg_div * (1 + g) / (r - g)
                    premium = (value - self.stock_data.latest_price) / self.stock_data.latest_price * 100
                    valuations.append({
                        'growth_rate': g,
                        'discount_rate': r,
                        'value': value,
                        'premium': premium
                    })
                except ZeroDivisionError:
                    continue
        return valuations
