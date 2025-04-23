import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sqlalchemy import create_engine, text
import matplotlib
import argparse
import sys

matplotlib.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
matplotlib.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

# 数据库连接
user = 'matt'
password = 'wq3395469'
host = 'dasen.fun'
port = '15432'
database = 'postgres'
engine = create_engine(f'postgresql://{user}:{password}@{host}:{port}/{database}')

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='股票绝对估值计算工具')
    parser.add_argument('--stock', type=str, help='股票代码，例如：601717.SH', default='601717.SH')
    parser.add_argument('--pe', type=str, help='PE估值倍数，用逗号分隔，例如：5,8,12', default='5,8,12')
    parser.add_argument('--pb', type=str, help='PB估值倍数，用逗号分隔，例如：0.8,1.2,1.5', default='0.8,1.2,1.5')
    parser.add_argument('--growth', type=str, help='增长率，用逗号分隔，例如：0.05,0.08,0.1', default='0.05,0.08,0.1')
    parser.add_argument('--discount', type=str, help='折现率，用逗号分隔，例如：0.1,0.12,0.15', default='0.1,0.12,0.15')
    parser.add_argument('--ev-ebitda', type=str, help='EV/EBITDA倍数，用逗号分隔，例如：6,8,10', default='6,8,10')
    
    return parser.parse_args()

class StockValuation:
    def __init__(self, ts_code):
        self.ts_code = ts_code
        self.stock_info = self.get_stock_info()
        self.latest_price = self.get_latest_price()
        self.total_shares = self.get_total_shares()
        self.financials = self.get_financial_data()
        self.dividends = self.get_dividend_data()
        self.market_cap = self.latest_price * self.total_shares / 100000000  # 转为亿元
    
    def get_stock_info(self):
        """获取股票基本信息"""
        with engine.connect() as conn:
            query = text(f"SELECT * FROM stock_basic WHERE ts_code = '{self.ts_code}'")
            result = conn.execute(query)
            return result.fetchone()._asdict()
    
    def get_latest_price(self):
        """获取最新收盘价"""
        with engine.connect() as conn:
            query = text(f"SELECT close FROM daily_quotes WHERE ts_code = '{self.ts_code}' ORDER BY trade_date DESC LIMIT 1")
            result = conn.execute(query)
            return float(result.fetchone()[0])
    
    def get_total_shares(self):
        """获取总股本"""
        with engine.connect() as conn:
            query = text(f"SELECT total_share FROM balance_sheet WHERE ts_code = '{self.ts_code}' ORDER BY end_date DESC LIMIT 1")
            result = conn.execute(query)
            return float(result.fetchone()[0])
    
    def get_financial_data(self):
        """获取历年财务数据"""
        # 获取年报数据
        with engine.connect() as conn:
            query = text(f"""
                SELECT 
                    i.end_date, 
                    EXTRACT(YEAR FROM i.end_date::timestamp) as year,
                    i.n_income, i.revenue, i.total_revenue,
                    i.oper_cost, i.operate_profit, i.non_oper_income, i.non_oper_exp,
                    f.eps, f.bps, f.roe, f.netprofit_margin, f.debt_to_assets,
                    c.n_cashflow_act, c.stot_out_inv_act, c.stot_cash_in_fnc_act, c.stot_cashout_fnc_act,
                    b.total_assets, b.total_liab, b.total_hldr_eqy_exc_min_int
                FROM income_statement i
                JOIN financial_indicators f ON i.ts_code = f.ts_code AND i.end_date = f.end_date
                JOIN cash_flow c ON i.ts_code = c.ts_code AND i.end_date = c.end_date
                JOIN balance_sheet b ON i.ts_code = b.ts_code AND i.end_date = b.end_date
                WHERE i.ts_code = '{self.ts_code}' 
                AND EXTRACT(MONTH FROM i.end_date::timestamp) = 12
                ORDER BY i.end_date DESC
            """)
            result = conn.execute(query)
            # 去重，保证每年只有一条数据
            data = []
            years_seen = set()
            for row in result:
                row_dict = row._asdict()
                year = row_dict['year']
                if year not in years_seen:
                    years_seen.add(year)
                    data.append(row_dict)
            
            return pd.DataFrame(data)
    
    def get_dividend_data(self):
        """获取历年分红数据"""
        with engine.connect() as conn:
            query = text(f"""
                SELECT 
                    end_date,
                    EXTRACT(YEAR FROM end_date::timestamp) as year,
                    cash_div_tax,
                    ann_date,
                    div_proc
                FROM dividend
                WHERE ts_code = '{self.ts_code}'
                ORDER BY end_date DESC
            """)
            result = conn.execute(query)
            
            data = []
            for row in result:
                data.append(row._asdict())
            
            df = pd.DataFrame(data)
            if not df.empty:
                # 将现金分红转为浮点数
                df['cash_div_tax'] = df['cash_div_tax'].astype(float)
            return df
    
    def calculate_pe_ratio(self):
        """计算当前PE和历史PE"""
        # 当前PE
        latest_income = float(self.financials.iloc[0]['n_income'])
        current_pe = self.market_cap / (latest_income / 100000000)  # 将净利润也转为亿元
        
        # 历史PE
        pe_history = []
        for idx, row in self.financials.iterrows():
            year = int(row['year'])
            income = float(row['n_income']) / 100000000  # 转为亿元
            if income > 0:  # 避免除以零或负数
                pe = self.market_cap / income
                pe_history.append((year, pe))
        
        return current_pe, pe_history
    
    def calculate_pb_ratio(self):
        """计算当前PB和历史PB"""
        # 当前PB
        latest_bps = float(self.financials.iloc[0]['bps'])
        current_pb = self.latest_price / latest_bps
        
        # 历史PB
        pb_history = []
        for idx, row in self.financials.iterrows():
            year = int(row['year'])
            bps = float(row['bps'])
            if bps > 0:  # 避免除以零或负数
                pb = self.latest_price / bps
                pb_history.append((year, pb))
        
        return current_pb, pb_history
    
    def calculate_growth_rate(self):
        """计算历史增长率"""
        # 净利润增长率
        income_growth = []
        revenue_growth = []
        
        for i in range(len(self.financials) - 1):
            current_year = int(self.financials.iloc[i]['year'])
            current_income = float(self.financials.iloc[i]['n_income'])
            prev_income = float(self.financials.iloc[i+1]['n_income'])
            
            current_revenue = float(self.financials.iloc[i]['total_revenue'])
            prev_revenue = float(self.financials.iloc[i+1]['total_revenue'])
            
            if prev_income > 0 and prev_revenue > 0:  # 避免除以零或负数
                income_growth_rate = (current_income / prev_income - 1) * 100
                revenue_growth_rate = (current_revenue / prev_revenue - 1) * 100
                income_growth.append((current_year, income_growth_rate))
                revenue_growth.append((current_year, revenue_growth_rate))
        
        # 计算3年CAGR (如果有足够数据)
        cagr = {}
        if len(self.financials) >= 3:
            latest_income = float(self.financials.iloc[0]['n_income'])
            three_years_ago_income = float(self.financials.iloc[2]['n_income'])
            if three_years_ago_income > 0:
                income_cagr = ((latest_income / three_years_ago_income) ** (1/3) - 1) * 100
                cagr['income_3y'] = income_cagr
            
            latest_revenue = float(self.financials.iloc[0]['total_revenue'])
            three_years_ago_revenue = float(self.financials.iloc[2]['total_revenue'])
            if three_years_ago_revenue > 0:
                revenue_cagr = ((latest_revenue / three_years_ago_revenue) ** (1/3) - 1) * 100
                cagr['revenue_3y'] = revenue_cagr
        
        return income_growth, revenue_growth, cagr
    
    def calculate_fcff_fcfe(self):
        """计算企业自由现金流(FCFF)和股权自由现金流(FCFE)"""
        fcff_history = []
        fcfe_history = []
        
        for idx, row in self.financials.iterrows():
            year = int(row['year'])
            
            # 更准确的FCFF计算
            # FCFF = 净利润 + 利息*(1-税率) + 折旧摊销 - 资本支出 - 营运资本增加
            net_income = float(row['n_income'])
            
            # 假设利息支出为总负债的5%
            total_liabilities = float(row['total_liab'])
            interest_expense = total_liabilities * 0.05
            
            # 假设税率为25%
            tax_rate = 0.25
            
            # 假设折旧摊销为营业收入的5%
            total_revenue = float(row['total_revenue'])
            depreciation_amortization = total_revenue * 0.05
            
            # 假设资本支出为营业收入的10%
            capital_expenditure = total_revenue * 0.10
            
            # 假设营运资本增加为营业收入的2%
            working_capital_increase = total_revenue * 0.02
            
            # 计算FCFF
            fcff = net_income + interest_expense * (1 - tax_rate) + depreciation_amortization - capital_expenditure - working_capital_increase
            fcff_history.append((year, fcff))
            
            # 更准确的FCFE计算
            # FCFE = 净利润 + 折旧摊销 - 资本支出 - 营运资本增加 + 净债务增加
            
            # 假设净债务增加为总负债的2%
            net_debt_increase = total_liabilities * 0.02
            
            # 计算FCFE
            fcfe = net_income + depreciation_amortization - capital_expenditure - working_capital_increase + net_debt_increase
            fcfe_history.append((year, fcfe))
        
        # 计算最新的FCFF和FCFE
        latest_fcff = fcff_history[0][1] if fcff_history else 0
        latest_fcfe = fcfe_history[0][1] if fcfe_history else 0
        
        return latest_fcff, latest_fcfe, fcff_history, fcfe_history
    
    def calculate_ev(self):
        """计算企业价值(EV)和EV/EBITDA倍数"""
        # 企业价值 = 市值 + 总负债 - 现金及现金等价物
        latest_finance = self.financials.iloc[0]
        total_liabilities = float(latest_finance['total_liab'])
        total_equity = float(latest_finance['total_hldr_eqy_exc_min_int'])
        
        # 假设现金及现金等价物为总资产的5%
        total_assets = float(latest_finance['total_assets'])
        cash_equivalents = total_assets * 0.05
        
        enterprise_value = (self.market_cap * 100000000) + total_liabilities - cash_equivalents  # 转回为元
        
        # 计算EBITDA: 营业利润 + 折旧摊销
        operating_profit = float(latest_finance['operate_profit'])
        
        # 假设折旧摊销为营业收入的5%
        total_revenue = float(latest_finance['total_revenue'])
        depreciation_amortization = total_revenue * 0.05
        
        ebitda = operating_profit + depreciation_amortization
        
        # 计算EV/EBITDA
        ev_to_ebitda = enterprise_value / ebitda if ebitda > 0 else 0
        
        return enterprise_value, ebitda, ev_to_ebitda
    
    def calculate_dividend_yield(self):
        """计算股息率和历史分红"""
        if self.dividends.empty:
            return 0, [], 0, 0
        
        # 获取最新的年度分红
        latest_div = None
        for _, row in self.dividends.iterrows():
            if pd.notna(row['cash_div_tax']) and float(row['cash_div_tax']) > 0:
                latest_div = row
                break
                
        if latest_div is None:
            return 0, [], 0, 0
            
        latest_div_per_share = float(latest_div['cash_div_tax'])
        current_yield = (latest_div_per_share / self.latest_price) * 100
        
        # 获取历史股息率
        dividend_history = []
        for idx, row in self.dividends.iterrows():
            year = row['year']
            if pd.notna(year) and pd.notna(row['cash_div_tax']) and float(row['cash_div_tax']) > 0:
                div_per_share = float(row['cash_div_tax'])
                # 计算该年的股息率（使用当前价格，仅作参考）
                div_yield = (div_per_share / self.latest_price) * 100
                dividend_history.append((int(year), div_per_share, div_yield))
        
        # 计算平均派息率（分红占净利润的比例）
        if not self.financials.empty and not self.dividends.empty:
            payout_ratios = []
            for _, div_row in self.dividends.iterrows():
                if pd.notna(div_row['year']) and pd.notna(div_row['cash_div_tax']):
                    div_year = int(div_row['year'])
                    div_amount = float(div_row['cash_div_tax'])
                    
                    if div_amount <= 0:
                        continue
                        
                    # 找到对应年份的财务数据
                    for _, fin_row in self.financials.iterrows():
                        if int(fin_row['year']) == div_year:
                            eps = float(fin_row['eps'])
                            if eps > 0:
                                payout_ratio = (div_amount / eps) * 100
                                payout_ratios.append(payout_ratio)
                            break
            
            avg_payout_ratio = sum(payout_ratios) / len(payout_ratios) if payout_ratios else 0
        else:
            avg_payout_ratio = 0
        
        # 计算5年平均分红增长率
        if len(dividend_history) >= 2:
            growth_rates = []
            for i in range(len(dividend_history) - 1):
                current_div = dividend_history[i][1]
                prev_div = dividend_history[i+1][1]
                if prev_div > 0:
                    growth_rate = (current_div / prev_div - 1) * 100
                    growth_rates.append(growth_rate)
            
            avg_div_growth = sum(growth_rates) / len(growth_rates) if growth_rates else 0
        else:
            avg_div_growth = 0
            
        return current_yield, dividend_history, avg_payout_ratio, avg_div_growth
    
    def perform_pe_valuation(self, pe_range=(5, 8, 12)):
        """基于PE的估值"""
        latest_eps = float(self.financials.iloc[0]['eps'])
        
        valuations = []
        for pe in pe_range:
            estimated_price = latest_eps * pe
            discount_rate = (estimated_price / self.latest_price - 1) * 100
            valuations.append((pe, estimated_price, discount_rate))
        
        return valuations
    
    def perform_pb_valuation(self, pb_range=(0.8, 1.2, 1.5)):
        """基于PB的估值"""
        latest_bps = float(self.financials.iloc[0]['bps'])
        
        valuations = []
        for pb in pb_range:
            estimated_price = latest_bps * pb
            discount_rate = (estimated_price / self.latest_price - 1) * 100
            valuations.append((pb, estimated_price, discount_rate))
        
        return valuations
    
    def perform_gordon_growth_valuation(self, growth_rates=(0.05, 0.10, 0.15), discount_rates=(0.10, 0.12, 0.15)):
        """使用戈登增长模型进行估值"""
        latest_eps = float(self.financials.iloc[0]['eps'])
        
        valuations = []
        for g in growth_rates:
            for r in discount_rates:
                if r > g:  # 确保折现率大于增长率
                    gordon_price = latest_eps * (1 + g) / (r - g)
                    discount = (gordon_price / self.latest_price - 1) * 100
                    valuations.append((g, r, gordon_price, discount))
        
        return valuations
    
    def perform_ddm_valuation(self, growth_rates=(0.05, 0.08, 0.10), discount_rates=(0.10, 0.12, 0.15)):
        """使用股息贴现模型(DDM)进行估值"""
        # 如果没有分红数据，无法使用DDM
        if self.dividends.empty:
            return []
            
        # 获取最新的分红数据
        latest_div = None
        for _, row in self.dividends.iterrows():
            if pd.notna(row['cash_div_tax']) and float(row['cash_div_tax']) > 0:
                latest_div = row
                break
                
        if latest_div is None:
            return []
            
        # 最新的每股分红
        div_per_share = float(latest_div['cash_div_tax'])
        
        valuations = []
        for g in growth_rates:
            for r in discount_rates:
                if r > g:  # 确保折现率大于增长率
                    # 戈登增长模型: P = D1 / (r - g)
                    next_div = div_per_share * (1 + g)  # 预计下一期分红
                    ddm_price = next_div / (r - g)
                    discount = (ddm_price / self.latest_price - 1) * 100
                    valuations.append((g, r, ddm_price, discount))
        
        return valuations
    
    def perform_fcff_valuation(self, growth_rates=(0.05, 0.08, 0.10), discount_rates=(0.10, 0.12, 0.15)):
        """使用企业自由现金流(FCFF)进行DCF估值"""
        latest_fcff, _, _, _ = self.calculate_fcff_fcfe()
        
        if latest_fcff <= 0:
            return []
        
        valuations = []
        for g in growth_rates:
            for r in discount_rates:
                if r > g:  # 确保折现率大于增长率
                    # 使用永续增长模型: EV = FCFF * (1 + g) / (r - g)
                    enterprise_value = latest_fcff * (1 + g) / (r - g)
                    
                    # 计算每股价值: (企业价值 - 总负债) / 总股本
                    latest_finance = self.financials.iloc[0]
                    total_liabilities = float(latest_finance['total_liab'])
                    equity_value = enterprise_value - total_liabilities
                    price_per_share = equity_value / self.total_shares
                    
                    discount = (price_per_share / self.latest_price - 1) * 100
                    valuations.append((g, r, price_per_share, discount))
        
        return valuations
    
    def perform_fcfe_valuation(self, growth_rates=(0.05, 0.08, 0.10), discount_rates=(0.10, 0.12, 0.15)):
        """使用股权自由现金流(FCFE)进行DCF估值"""
        _, latest_fcfe, _, _ = self.calculate_fcff_fcfe()
        
        if latest_fcfe <= 0:
            return []
        
        valuations = []
        for g in growth_rates:
            for r in discount_rates:
                if r > g:  # 确保折现率大于增长率
                    # 使用永续增长模型: Equity Value = FCFE * (1 + g) / (r - g)
                    equity_value = latest_fcfe * (1 + g) / (r - g)
                    
                    # 计算每股价值
                    price_per_share = equity_value / self.total_shares
                    
                    discount = (price_per_share / self.latest_price - 1) * 100
                    valuations.append((g, r, price_per_share, discount))
        
        return valuations
    
    def perform_ev_ebitda_valuation(self, ev_ebitda_range=(6, 8, 10)):
        """使用EV/EBITDA倍数进行估值"""
        _, ebitda, _ = self.calculate_ev()
        
        if ebitda <= 0:
            return []
        
        valuations = []
        for multiple in ev_ebitda_range:
            # 计算企业价值
            enterprise_value = ebitda * multiple
            
            # 计算每股价值: (企业价值 - 总负债) / 总股本
            latest_finance = self.financials.iloc[0]
            total_liabilities = float(latest_finance['total_liab'])
            equity_value = enterprise_value - total_liabilities
            price_per_share = equity_value / self.total_shares
            
            discount = (price_per_share / self.latest_price - 1) * 100
            valuations.append((multiple, price_per_share, discount))
        
        return valuations
        
    def generate_valuation_report(self):
        """生成完整的估值报告"""
        # 基本信息
        print(f"=== {self.stock_info['name']} ({self.ts_code}) 绝对估值分析 ===")
        print(f"所属行业: {self.stock_info['industry']}")
        print(f"当前股价: {self.latest_price:.2f}元")
        print(f"总股本: {self.total_shares/100000000:.2f}亿股")
        print(f"总市值: {self.market_cap:.2f}亿元")
        print("\n")
        
        # 财务指标
        latest_finance = self.financials.iloc[0]
        print("=== 最新财务指标 ===")
        print(f"每股收益(EPS): {float(latest_finance['eps']):.2f}元")
        print(f"每股净资产(BPS): {float(latest_finance['bps']):.2f}元")
        print(f"净资产收益率(ROE): {float(latest_finance['roe']):.2f}%")
        print(f"净利润率: {float(latest_finance['netprofit_margin']):.2f}%")
        print(f"资产负债率: {float(latest_finance['debt_to_assets']):.2f}%")
        print(f"净利润: {float(latest_finance['n_income'])/100000000:.2f}亿元")
        print(f"营业收入: {float(latest_finance['total_revenue'])/100000000:.2f}亿元")
        print("\n")
        
        # 计算指标
        current_pe, pe_history = self.calculate_pe_ratio()
        current_pb, pb_history = self.calculate_pb_ratio()
        income_growth, revenue_growth, cagr = self.calculate_growth_rate()
        current_yield, dividend_history, avg_payout_ratio, avg_div_growth = self.calculate_dividend_yield()
        
        print("=== 估值指标 ===")
        print(f"当前市盈率(PE): {current_pe:.2f}倍")
        print(f"当前市净率(PB): {current_pb:.2f}倍")
        print(f"当前股息率: {current_yield:.2f}%")
        print(f"平均派息比例: {avg_payout_ratio:.2f}%")
        print(f"股息增长率: {avg_div_growth:.2f}%")
        
        if cagr:
            print("\n=== 增长指标 ===")
            for key, value in cagr.items():
                if key == 'income_3y':
                    print(f"净利润3年CAGR: {value:.2f}%")
                elif key == 'revenue_3y':
                    print(f"营收3年CAGR: {value:.2f}%")
        
        # 历史分红
        if dividend_history:
            print("\n=== 历史分红 ===")
            print(f"{'年份':<6}{'每股分红':<10}{'股息率':<10}")
            for year, div, yield_rate in dividend_history:
                print(f"{year:<6}{div:<10.4f}{yield_rate:<10.2f}%")
        
        # PE估值
        print("\n=== 基于PE的估值 ===")
        pe_valuations = self.perform_pe_valuation()
        print(f"{'PE倍数':<10}{'估值价格':<10}{'上涨空间':<10}")
        for pe, price, discount in pe_valuations:
            print(f"{pe:<10.2f}{price:<10.2f}{discount:<10.2f}%")
        
        # PB估值
        print("\n=== 基于PB的估值 ===")
        pb_valuations = self.perform_pb_valuation()
        print(f"{'PB倍数':<10}{'估值价格':<10}{'上涨空间':<10}")
        for pb, price, discount in pb_valuations:
            print(f"{pb:<10.2f}{price:<10.2f}{discount:<10.2f}%")
        
        # 戈登增长模型估值
        print("\n=== 基于戈登增长模型的估值(EPS) ===")
        gordon_valuations = self.perform_gordon_growth_valuation()
        print(f"{'增长率(g)':<10}{'折现率(r)':<10}{'估值价格':<10}{'上涨空间':<10}")
        for g, r, price, discount in gordon_valuations:
            print(f"{g*100:<10.2f}%{r*100:<10.2f}%{price:<10.2f}{discount:<10.2f}%")
        
        # 股息贴现模型估值
        ddm_valuations = self.perform_ddm_valuation()
        if ddm_valuations:
            print("\n=== 基于股息贴现模型(DDM)的估值 ===")
            print(f"{'增长率(g)':<10}{'折现率(r)':<10}{'估值价格':<10}{'上涨空间':<10}")
            for g, r, price, discount in ddm_valuations:
                print(f"{g*100:<10.2f}%{r*100:<10.2f}%{price:<10.2f}{discount:<10.2f}%")
        
        # 打印FCFF和FCFE的值
        latest_fcff, latest_fcfe, _, _ = self.calculate_fcff_fcfe()
        print("\n=== 自由现金流调试信息 ===")
        print(f"最新FCFF: {latest_fcff:.2f}")
        print(f"最新FCFE: {latest_fcfe:.2f}")
        
        # 打印现金流相关的原始数据
        latest_finance = self.financials.iloc[0]
        print("\n=== 现金流原始数据 ===")
        print(f"经营活动现金流(n_cashflow_act): {float(latest_finance['n_cashflow_act']):.2f}")
        print(f"投资活动现金流出(stot_out_inv_act): {float(latest_finance['stot_out_inv_act']):.2f}")
        print(f"筹资活动现金流入(stot_cash_in_fnc_act): {float(latest_finance['stot_cash_in_fnc_act']):.2f}")
        print(f"筹资活动现金流出(stot_cashout_fnc_act): {float(latest_finance['stot_cashout_fnc_act']):.2f}")
        
        # FCFF估值
        fcff_valuations = self.perform_fcff_valuation()
        if fcff_valuations:
            print("\n=== 基于企业自由现金流(FCFF)的DCF估值 ===")
            print(f"{'增长率(g)':<10}{'折现率(r)':<10}{'估值价格':<10}{'上涨空间':<10}")
            for g, r, price, discount in fcff_valuations:
                print(f"{g*100:<10.2f}%{r*100:<10.2f}%{price:<10.2f}{discount:<10.2f}%")
        else:
            print("\n=== 基于企业自由现金流(FCFF)的DCF估值 ===")
            print("无法计算FCFF估值，可能是因为FCFF为负数或零")
        
        # FCFE估值
        fcfe_valuations = self.perform_fcfe_valuation()
        if fcfe_valuations:
            print("\n=== 基于股权自由现金流(FCFE)的DCF估值 ===")
            print(f"{'增长率(g)':<10}{'折现率(r)':<10}{'估值价格':<10}{'上涨空间':<10}")
            for g, r, price, discount in fcfe_valuations:
                print(f"{g*100:<10.2f}%{r*100:<10.2f}%{price:<10.2f}{discount:<10.2f}%")
        else:
            print("\n=== 基于股权自由现金流(FCFE)的DCF估值 ===")
            print("无法计算FCFE估值，可能是因为FCFE为负数或零")
        
        # EV/EBITDA估值
        ev_ebitda_valuations = self.perform_ev_ebitda_valuation()
        if ev_ebitda_valuations:
            print("\n=== 基于EV/EBITDA倍数的估值 ===")
            print(f"{'EV/EBITDA':<10}{'估值价格':<10}{'上涨空间':<10}")
            for multiple, price, discount in ev_ebitda_valuations:
                print(f"{multiple:<10.2f}{price:<10.2f}{discount:<10.2f}%")
        
        # 估值结论
        print("\n=== 估值结论 ===")
        avg_pe_price = sum([v[1] for v in pe_valuations]) / len(pe_valuations)
        avg_pb_price = sum([v[1] for v in pb_valuations]) / len(pb_valuations)
        avg_gordon_price = sum([v[2] for v in gordon_valuations]) / len(gordon_valuations)
        
        valuation_components = [avg_pe_price, avg_pb_price, avg_gordon_price]
        valuation_weights = [0.2, 0.2, 0.2]  # 给不同模型分配权重
        
        # 如果有DDM估值结果，加入综合估值
        if ddm_valuations:
            avg_ddm_price = sum([v[2] for v in ddm_valuations]) / len(ddm_valuations)
            valuation_components.append(avg_ddm_price)
            valuation_weights.append(0.1)
        
        # 如果有FCFF估值结果，加入综合估值
        if fcff_valuations:
            avg_fcff_price = sum([v[2] for v in fcff_valuations]) / len(fcff_valuations)
            valuation_components.append(avg_fcff_price)
            valuation_weights.append(0.1)
        
        # 如果有FCFE估值结果，加入综合估值
        if fcfe_valuations:
            avg_fcfe_price = sum([v[2] for v in fcfe_valuations]) / len(fcfe_valuations)
            valuation_components.append(avg_fcfe_price)
            valuation_weights.append(0.1)
        
        # 如果有EV/EBITDA估值结果，加入综合估值
        if ev_ebitda_valuations:
            avg_ev_ebitda_price = sum([v[1] for v in ev_ebitda_valuations]) / len(ev_ebitda_valuations)
            valuation_components.append(avg_ev_ebitda_price)
            valuation_weights.append(0.1)
        
        # 确保权重总和为1
        total_weight = sum(valuation_weights)
        valuation_weights = [w / total_weight for w in valuation_weights]
        
        # 计算加权平均
        weighted_sum = sum(p * w for p, w in zip(valuation_components, valuation_weights))
        
        avg_discount = (weighted_sum / self.latest_price - 1) * 100
        
        print(f"PE估值均值: {avg_pe_price:.2f}元")
        print(f"PB估值均值: {avg_pb_price:.2f}元")
        print(f"戈登模型估值均值: {avg_gordon_price:.2f}元")
        
        if ddm_valuations:
            print(f"DDM模型估值均值: {avg_ddm_price:.2f}元")
            
        if fcff_valuations:
            print(f"FCFF模型估值均值: {avg_fcff_price:.2f}元")
            
        if fcfe_valuations:
            print(f"FCFE模型估值均值: {avg_fcfe_price:.2f}元")
            
        if ev_ebitda_valuations:
            print(f"EV/EBITDA模型估值均值: {avg_ev_ebitda_price:.2f}元")
        
        print(f"综合估值: {weighted_sum:.2f}元, 相对当前股价上涨空间: {avg_discount:.2f}%")
        
        if avg_discount > 20:
            print("结论: 严重低估，建议买入")
        elif avg_discount > 10:
            print("结论: 低估，可考虑买入")
        elif avg_discount > -10:
            print("结论: 合理估值，可持有观望")
        elif avg_discount > -20:
            print("结论: 高估，可考虑减持")
        else:
            print("结论: 严重高估，建议卖出")

    def plot_historical_data(self):
        """绘制历史数据图表"""
        # 转换财务数据的日期为年份
        self.financials['year'] = self.financials['year'].astype(int)
        
        # 确定图表数量（如果有分红数据，则增加一个图表）
        num_plots = 4 if not self.dividends.empty else 3
        
        fig, axes = plt.subplots(num_plots, 1, figsize=(12, 5 * num_plots))
        
        # 1. 绘制净利润和营收
        ax1 = axes[0]
        years = self.financials['year'].values
        income = [float(x)/100000000 for x in self.financials['n_income'].values]  # 转为亿元
        revenue = [float(x)/100000000 for x in self.financials['total_revenue'].values]  # 转为亿元
        
        ax1.bar(years - 0.2, income, width=0.4, label='净利润(亿元)')
        ax1.bar(years + 0.2, revenue, width=0.4, label='营业收入(亿元)')
        
        for i, v in enumerate(income):
            ax1.text(years[i] - 0.2, v + 1, f'{v:.1f}', ha='center')
        
        for i, v in enumerate(revenue):
            ax1.text(years[i] + 0.2, v + 1, f'{v:.1f}', ha='center')
        
        ax1.set_title('净利润与营业收入历史数据')
        ax1.set_xlabel('年份')
        ax1.set_ylabel('金额(亿元)')
        ax1.grid(axis='y', linestyle='--', alpha=0.7)
        ax1.legend()
        
        # 2. 绘制ROE和净利润率
        ax2 = axes[1]
        roe = [float(x) for x in self.financials['roe'].values]
        margin = [float(x) for x in self.financials['netprofit_margin'].values]
        
        ax2.plot(years, roe, 'o-', label='ROE(%)')
        ax2.plot(years, margin, 's-', label='净利润率(%)')
        
        for i, v in enumerate(roe):
            ax2.text(years[i], v + 0.5, f'{v:.1f}%', ha='center')
        
        for i, v in enumerate(margin):
            ax2.text(years[i], v - 0.5, f'{v:.1f}%', ha='center')
        
        ax2.set_title('ROE与净利润率历史数据')
        ax2.set_xlabel('年份')
        ax2.set_ylabel('百分比(%)')
        ax2.grid(axis='y', linestyle='--', alpha=0.7)
        ax2.legend()
        
        # 3. 绘制EPS和BPS
        ax3 = axes[2]
        eps = [float(x) for x in self.financials['eps'].values]
        bps = [float(x) for x in self.financials['bps'].values]
        
        ax3.plot(years, eps, 'o-', label='EPS(元)')
        ax3.plot(years, bps, 's-', label='BPS(元)')
        
        for i, v in enumerate(eps):
            ax3.text(years[i], v + 0.2, f'{v:.2f}', ha='center')
        
        for i, v in enumerate(bps):
            ax3.text(years[i], v - 0.2, f'{v:.2f}', ha='center')
        
        ax3.set_title('EPS与BPS历史数据')
        ax3.set_xlabel('年份')
        ax3.set_ylabel('金额(元)')
        ax3.grid(axis='y', linestyle='--', alpha=0.7)
        ax3.legend()
        
        # 4. 如果有分红数据，绘制历史分红
        if num_plots > 3:
            ax4 = axes[3]
            _, dividend_history, _, _ = self.calculate_dividend_yield()
            
            if dividend_history:
                div_years = [item[0] for item in dividend_history]
                div_values = [item[1] for item in dividend_history]
                div_yields = [item[2] for item in dividend_history]
                
                ax4.bar(div_years, div_values, color='green', alpha=0.7, label='每股分红(元)')
                ax4.set_title('历史分红数据')
                ax4.set_xlabel('年份')
                ax4.set_ylabel('每股分红(元)', color='green')
                ax4.tick_params(axis='y', labelcolor='green')
                
                # 添加第二个Y轴显示股息率
                ax4_2 = ax4.twinx()
                ax4_2.plot(div_years, div_yields, 'ro-', label='股息率(%)')
                ax4_2.set_ylabel('股息率(%)', color='red')
                ax4_2.tick_params(axis='y', labelcolor='red')
                
                # 标注值
                for i, v in enumerate(div_values):
                    ax4.text(div_years[i], v + 0.02, f'{v:.2f}', ha='center')
                
                for i, v in enumerate(div_yields):
                    ax4_2.text(div_years[i], v + 0.2, f'{v:.2f}%', ha='center', color='red')
                
                # 合并两个图例
                lines1, labels1 = ax4.get_legend_handles_labels()
                lines2, labels2 = ax4_2.get_legend_handles_labels()
                ax4.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
                
                ax4.grid(axis='y', linestyle='--', alpha=0.7)
        
        plt.tight_layout()
        plt.savefig(f"{self.ts_code.split('.')[0]}_valuation_charts.png")
        plt.close()
        
        print(f"图表已保存为 {self.ts_code.split('.')[0]}_valuation_charts.png")

def main():
    """主函数"""
    # 解析命令行参数
    args = parse_arguments()
    
    # 解析PE、PB、增长率、折现率和EV/EBITDA倍数
    pe_range = tuple(float(x) for x in args.pe.split(','))
    pb_range = tuple(float(x) for x in args.pb.split(','))
    growth_rates = tuple(float(x) for x in args.growth.split(','))
    discount_rates = tuple(float(x) for x in args.discount.split(','))
    ev_ebitda_range = tuple(float(x) for x in args.ev_ebitda.split(','))
    
    # 创建StockValuation对象
    valuation = StockValuation(args.stock)
    
    # 生成估值报告，传入参数
    pe_valuations = valuation.perform_pe_valuation(pe_range)
    pb_valuations = valuation.perform_pb_valuation(pb_range)
    gordon_valuations = valuation.perform_gordon_growth_valuation(growth_rates, discount_rates)
    ddm_valuations = valuation.perform_ddm_valuation(growth_rates, discount_rates)
    fcff_valuations = valuation.perform_fcff_valuation(growth_rates, discount_rates)
    fcfe_valuations = valuation.perform_fcfe_valuation(growth_rates, discount_rates)
    ev_ebitda_valuations = valuation.perform_ev_ebitda_valuation(ev_ebitda_range)
    
    # 生成估值报告
    valuation.generate_valuation_report()
    
    # 绘制历史数据图表
    valuation.plot_historical_data()
    
    # 打印使用说明
    print("\n=== 使用说明 ===")
    print("本工具可以通过命令行参数指定股票代码和估值参数，例如：")
    print("python valuation_stock.py --stock 601717.SH --pe \"5,8,12\" --pb \"0.8,1.2,1.5\" --growth \"0.05,0.08,0.1\" --discount \"0.1,0.12,0.15\" --ev-ebitda \"6,8,10\"")
    print("参数说明：")
    print("  --stock: 股票代码，例如：601717.SH")
    print("  --pe: PE估值倍数，用逗号分隔，例如：\"5,8,12\"")
    print("  --pb: PB估值倍数，用逗号分隔，例如：\"0.8,1.2,1.5\"")
    print("  --growth: 增长率，用逗号分隔，例如：\"0.05,0.08,0.1\"")
    print("  --discount: 折现率，用逗号分隔，例如：\"0.1,0.12,0.15\"")
    print("  --ev-ebitda: EV/EBITDA倍数，用逗号分隔，例如：\"6,8,10\"")

if __name__ == "__main__":
    main()
