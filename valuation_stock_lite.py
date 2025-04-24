import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sqlalchemy import create_engine, text
import matplotlib
import argparse
import sys
from decimal import Decimal

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
    parser.add_argument('--stock', type=str, help='股票代码，例如：000001.SH', default='000001.SH')
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
                    i.n_income, i.revenue, i.total_revenue, c.finan_exp,
                    i.oper_cost, i.operate_profit, i.non_oper_income, i.non_oper_exp,
                    f.eps, f.bps, f.roe, f.netprofit_margin, f.debt_to_assets,
                    c.n_cashflow_act, c.stot_out_inv_act, c.stot_cash_in_fnc_act, c.stot_cashout_fnc_act,
                    c.c_pay_acq_const_fiolta, c.c_paid_invest, c.decr_inventories,
                    c.incr_oper_payable, c.decr_oper_payable, c.c_recp_borrow, c.c_prepay_amt_borr,
                    c.depr_fa_coga_dpba, c.amort_intang_assets,
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
                    # 将所有数值字段转换为float
                    for key, value in row_dict.items():
                        if isinstance(value, (int, float, Decimal)):
                            row_dict[key] = float(value)
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
    
    def calculate_fcff_fcfe_full_capex(self):
        """计算企业自由现金流(FCFF)和股权自由现金流(FCFE) - 完整资本性支出版本"""
        fcff_history = []
        fcfe_history = []
        
        for idx, row in self.financials.iterrows():
            year = int(row['year'])
            
            # 计算EBIAT(税后息前利润) = (营业利润 + 财务费用) * (1 - 税率)
            operating_profit = float(row.get('operate_profit', 0))
            interest_expense = float(row.get('finan_exp', 0))
            tax_rate = 0.25  # 假设税率25%
            ebit = operating_profit + interest_expense
            ebiate = ebit * (1 - tax_rate)
            
            # 折旧与摊销
            depreciation = float(row.get('depr_fa_coga_dpba', 0))
            amortization = float(row.get('amort_intang_assets', 0))
            
            # 完整资本性支出 = 购建固定资产、无形资产和其他长期资产支付的现金 + 投资支付的现金
            capex = float(row.get('c_pay_acq_const_fiolta', 0)) + float(row.get('c_paid_invest', 0))
            
            # 计算营运资本 = 流动资产合计 - 流动负债合计
            current_assets = float(row.get('total_cur_assets', 0))
            current_liab = float(row.get('total_cur_liab', 0))
            current_wc = current_assets - current_liab
            
            # 计算营运资本变动
            if idx < len(self.financials) - 1:
                prev_row = self.financials.iloc[idx + 1]
                prev_assets = float(prev_row.get('total_cur_assets', 0))
                prev_liab = float(prev_row.get('total_cur_liab', 0))
                prev_wc = prev_assets - prev_liab
                working_capital_change = current_wc - prev_wc
            else:
                working_capital_change = 0  # 没有上期数据时设为0
            
            # FCFF = EBIAT + 折旧与摊销 - 资本支出 - 营运资本增加
            fcff = ebiate + depreciation + amortization - capex - working_capital_change
            
            # FCFE = FCFF - 利息*(1-税率) + 净债务变动
            net_debt_increase = float(row.get('c_recp_borrow', 0)) - float(row.get('c_prepay_amt_borr', 0))
            fcfe = fcff - interest_expense * (1 - tax_rate) + net_debt_increase
            
            fcff_history.append((year, fcff))
            fcfe_history.append((year, fcfe))
        
        # 计算最新的FCFF和FCFE
        latest_fcff = fcff_history[0][1] if fcff_history else 0
        latest_fcfe = fcfe_history[0][1] if fcfe_history else 0
        
        return latest_fcff, latest_fcfe, fcff_history, fcfe_history

    def calculate_fcff_fcfe(self):
        """计算企业自由现金流(FCFF)和股权自由现金流(FCFE)"""
        fcff_history = []
        fcfe_history = []
        
        for idx, row in self.financials.iterrows():
            year = int(row['year'])
            
            # 计算EBIAT(税后息前利润) = (营业利润 + 财务费用) * (1 - 税率)
            operating_profit = float(row.get('operate_profit', 0))
            interest_expense = float(row.get('finan_exp', 0))
            tax_rate = 0.25  # 假设税率25%
            ebit = operating_profit + interest_expense
            ebiate = ebit * (1 - tax_rate)
            
            # 折旧与摊销
            depreciation = float(row.get('depr_fa_coga_dpba', 0))
            amortization = float(row.get('amort_intang_assets', 0))
            
            # 资本支出 = 购建固定资产、无形资产和其他长期资产支付的现金
            capital_expenditure = float(row.get('c_pay_acq_const_fiolta', 0))
            
            # 计算营运资本 = 流动资产合计 - 流动负债合计
            current_assets = float(row.get('total_cur_assets', 0))
            current_liab = float(row.get('total_cur_liab', 0))
            current_wc = current_assets - current_liab
            
            # 计算营运资本变动
            if idx < len(self.financials) - 1:
                prev_row = self.financials.iloc[idx + 1]
                prev_assets = float(prev_row.get('total_cur_assets', 0))
                prev_liab = float(prev_row.get('total_cur_liab', 0))
                prev_wc = prev_assets - prev_liab
                working_capital_change = current_wc - prev_wc
            else:
                working_capital_change = 0  # 没有上期数据时设为0
            
            # FCFF = EBIAT + 折旧与摊销 - 资本支出 - 营运资本增加
            fcff = ebiate + depreciation + amortization - capital_expenditure - working_capital_change
            
            # 验证计算
            if current_wc < 0:
                print(f"警告: {year}年营运资本为负值: {current_wc}")
            
            # FCFE = FCFF - 利息*(1-税率) + 净债务变动
            net_debt_increase = float(row.get('c_recp_borrow', 0)) - float(row.get('c_prepay_amt_borr', 0))
            fcfe = fcff - interest_expense * (1 - tax_rate) + net_debt_increase
            fcff_history.append((year, fcff))
            fcfe_history.append((year, fcfe))
        
        # 计算最新的FCFF和FCFE
        latest_fcff = fcff_history[0][1] if fcff_history else 0
        latest_fcfe = fcfe_history[0][1] if fcfe_history else 0
        
        return latest_fcff, latest_fcfe, fcff_history, fcfe_history
    
    def calculate_fcff_fcfe_adjusted(self):
        """计算调整后的企业自由现金流(FCFF)和股权自由现金流(FCFE)，去除投资活动现金流"""
        fcff_history = []
        fcfe_history = []
        
        for idx, row in self.financials.iterrows():
            year = int(row['year'])
            
            # 直接使用经营活动现金流
            operating_cash_flow = float(row.get('n_cashflow_act', 0))
            
            # 营运资本变动 = (流动资产合计 - 流动负债合计)的变动
            current_assets = float(row.get('total_cur_assets', 0))
            current_liab = float(row.get('total_cur_liab', 0))
            current_wc = current_assets - current_liab
            
            # 获取上一期数据计算变动
            if idx < len(self.financials) - 1:
                prev_row = self.financials.iloc[idx + 1]
                prev_wc = float(prev_row.get('total_cur_assets', 0)) - float(prev_row.get('total_cur_liab', 0))
                working_capital_change = current_wc - prev_wc
            else:
                working_capital_change = 0  # 没有上期数据时设为0
            
            # 调整后的FCFF = 经营活动现金流 - 营运资本增加
            fcff = operating_cash_flow - working_capital_change
            
            # 调整后的FCFE = FCFF - 利息*(1-税率) + 净债务变动
            interest_expense = float(row.get('finan_exp', 0))
            tax_rate = 0.25  # 假设税率25%
            net_debt_increase = float(row.get('c_recp_borrow', 0)) - float(row.get('c_prepay_amt_borr', 0))
            fcfe = fcff - interest_expense * (1 - tax_rate) + net_debt_increase
            
            fcff_history.append((year, fcff))
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
        
        # 计算3年平均分红
        avg_div = 0
        if len(dividend_history) >= 3:
            avg_div = sum([d[1] for d in dividend_history[:3]]) / 3
        
        # 计算分红支付率
        payout_ratio = 0
        if not self.financials.empty:
            latest_income = float(self.financials.iloc[0]['n_income'])
            if latest_income > 0:
                payout_ratio = (latest_div_per_share * self.total_shares) / latest_income * 100
        
        return current_yield, dividend_history, avg_div, payout_ratio

    def calculate_ddm_valuation(self, growth_rates, discount_rates):
        """股利贴现模型(DDM)估值"""
        current_yield, div_history, avg_div, _ = self.calculate_dividend_yield()
        
        if avg_div <= 0:
            return None, "无有效分红数据，无法进行DDM估值"
        
        # 计算历史分红增长率
        growth_rates = [float(r) for r in growth_rates]
        discount_rates = [float(r) for r in discount_rates]
        
        # 计算3年平均分红增长率
        avg_growth = 0
        if len(div_history) >= 3:
            growths = []
            for i in range(len(div_history)-1):
                prev = div_history[i+1][1]
                curr = div_history[i][1]
                if prev > 0:
                    growths.append((curr - prev) / prev)
            if growths:
                avg_growth = sum(growths) / len(growths)
        
        # 使用用户提供的增长率或历史平均增长率
        if not growth_rates:
            if avg_growth > 0:
                growth_rates = [avg_growth * 0.8, avg_growth, avg_growth * 1.2]
            else:
                growth_rates = [0.03, 0.05, 0.08]  # 默认增长率
        
        valuations = []
        for g in growth_rates:
            for r in discount_rates:
                # 两阶段DDM模型
                # 第一阶段: 5年高增长期
                terminal_value = 0
                present_value = 0
                for year in range(1, 6):
                    dividend = avg_div * (1 + g) ** year
                    present_value += dividend / ((1 + r) ** year)
                
                # 第二阶段: 永续增长率为g/2
                terminal_growth = g / 2
                terminal_dividend = avg_div * (1 + g) ** 5 * (1 + terminal_growth)
                terminal_value = terminal_dividend / (r - terminal_growth) / (1 + r) ** 5
                
                total_value = present_value + terminal_value
                valuations.append({
                    'growth_rate': g,
                    'discount_rate': r,
                    'value': total_value,
                    'premium': (total_value - self.latest_price) / self.latest_price * 100
                })
        
        return valuations, None
    
    def perform_fcff_valuation_full_capex(self, growth_rates, discount_rates):
        """基于完整资本性支出FCFF的DCF估值"""
        latest_fcff, _, fcff_history, _ = self.calculate_fcff_fcfe_full_capex()
        
        if latest_fcff <= 0:
            return None, "FCFF为负或零，无法进行DCF估值"
        
        # 计算历史FCFF增长率
        growth_rates = [float(r) for r in growth_rates]
        discount_rates = [float(r) for r in discount_rates]
        
        # 计算3年FCFF平均增长率
        avg_growth = 0
        if len(fcff_history) >= 3:
            growths = []
            for i in range(len(fcff_history)-1):
                prev = fcff_history[i+1][1]
                curr = fcff_history[i][1]
                if prev > 0:
                    growths.append((curr - prev) / prev)
            if growths:
                avg_growth = sum(growths) / len(growths)
        
        # 使用用户提供的增长率或历史平均增长率
        if not growth_rates:
            if avg_growth > 0:
                growth_rates = [avg_growth * 0.8, avg_growth, avg_growth * 1.2]
            else:
                growth_rates = [0.05, 0.08, 0.1]  # 默认增长率
        
        valuations = []
        for g in growth_rates:
            for r in discount_rates:
                # 两阶段DCF模型
                # 第一阶段: 5年高增长期
                terminal_value = 0
                present_value = 0
                for year in range(1, 6):
                    fcff = latest_fcff * (1 + g) ** year
                    present_value += fcff / ((1 + r) ** year)
                
                # 第二阶段: 永续增长率为g/2
                terminal_growth = g / 2
                terminal_fcff = latest_fcff * (1 + g) ** 5 * (1 + terminal_growth)
                terminal_value = terminal_fcff / (r - terminal_growth) / (1 + r) ** 5
                
                total_value = (present_value + terminal_value) / self.total_shares  # 每股价值
                valuations.append({
                    'growth_rate': g,
                    'discount_rate': r,
                    'value': total_value,
                    'premium': (total_value - self.latest_price) / self.latest_price * 100
                })
        
        return valuations, None
    
    def perform_fcff_valuation_adjusted(self, growth_rates, discount_rates):
        """基于调整后FCFF的DCF估值"""
        latest_fcff, _, fcff_history, _ = self.calculate_fcff_fcfe_adjusted()
        
        if latest_fcff <= 0:
            return None, "FCFF为负或零，无法进行DCF估值"
        
        # 计算历史FCFF增长率
        growth_rates = [float(r) for r in growth_rates]
        discount_rates = [float(r) for r in discount_rates]
        
        # 计算3年FCFF平均增长率
        avg_growth = 0
        if len(fcff_history) >= 3:
            growths = []
            for i in range(len(fcff_history)-1):
                prev = fcff_history[i+1][1]
                curr = fcff_history[i][1]
                if prev > 0:
                    growths.append((curr - prev) / prev)
            if growths:
                avg_growth = sum(growths) / len(growths)
        
        # 使用用户提供的增长率或历史平均增长率
        if not growth_rates:
            if avg_growth > 0:
                growth_rates = [avg_growth * 0.8, avg_growth, avg_growth * 1.2]
            else:
                growth_rates = [0.05, 0.08, 0.1]  # 默认增长率
        
        valuations = []
        for g in growth_rates:
            for r in discount_rates:
                # 两阶段DCF模型
                # 第一阶段: 5年高增长期
                terminal_value = 0
                present_value = 0
                for year in range(1, 6):
                    fcff = latest_fcff * (1 + g) ** year
                    present_value += fcff / ((1 + r) ** year)
                
                # 第二阶段: 永续增长率为g/2
                terminal_growth = g / 2
                terminal_fcff = latest_fcff * (1 + g) ** 5 * (1 + terminal_growth)
                terminal_value = terminal_fcff / (r - terminal_growth) / (1 + r) ** 5
                
                total_value = (present_value + terminal_value) / self.total_shares  # 每股价值
                valuations.append({
                    'growth_rate': g,
                    'discount_rate': r,
                    'value': total_value,
                    'premium': (total_value - self.latest_price) / self.latest_price * 100
                })
        
        return valuations, None

    def perform_fcfe_valuation_full_capex(self, growth_rates, discount_rates):
        """基于完整资本性支出FCFE的DCF估值"""
        _, latest_fcfe, _, fcfe_history = self.calculate_fcff_fcfe_full_capex()
        
        if latest_fcfe <= 0:
            return None, "FCFE为负或零，无法进行DCF估值"
        
        # 计算历史FCFE增长率
        growth_rates = [float(r) for r in growth_rates]
        discount_rates = [float(r) for r in discount_rates]
        
        # 计算3年FCFE平均增长率
        avg_growth = 0
        if len(fcfe_history) >= 3:
            growths = []
            for i in range(len(fcfe_history)-1):
                prev = fcfe_history[i+1][1]
                curr = fcfe_history[i][1]
                if prev > 0:
                    growths.append((curr - prev) / prev)
            if growths:
                avg_growth = sum(growths) / len(growths)
        
        # 使用用户提供的增长率或历史平均增长率
        if not growth_rates:
            if avg_growth > 0:
                growth_rates = [avg_growth * 0.8, avg_growth, avg_growth * 1.2]
            else:
                growth_rates = [0.05, 0.08, 0.1]  # 默认增长率
        
        valuations = []
        for g in growth_rates:
            for r in discount_rates:
                # 两阶段DCF模型
                # 第一阶段: 5年高增长期
                terminal_value = 0
                present_value = 0
                for year in range(1, 6):
                    fcfe = latest_fcfe * (1 + g) ** year
                    present_value += fcfe / ((1 + r) ** year)
                
                # 第二阶段: 永续增长率为g/2
                terminal_growth = g / 2
                terminal_fcfe = latest_fcfe * (1 + g) ** 5 * (1 + terminal_growth)
                terminal_value = terminal_fcfe / (r - terminal_growth) / (1 + r) ** 5
                
                total_value = (present_value + terminal_value) / self.total_shares  # 每股价值
                valuations.append({
                    'growth_rate': g,
                    'discount_rate': r,
                    'value': total_value,
                    'premium': (total_value - self.latest_price) / self.latest_price * 100
                })
        
        return valuations, None

    def perform_fcfe_valuation_adjusted(self, growth_rates, discount_rates):
        """基于调整后FCFE的DCF估值"""
        _, latest_fcfe, _, fcfe_history = self.calculate_fcff_fcfe_adjusted()
        
        if latest_fcfe <= 0:
            return None, "FCFE为负或零，无法进行DCF估值"
        
        # 计算历史FCFE增长率
        growth_rates = [float(r) for r in growth_rates]
        discount_rates = [float(r) for r in discount_rates]
        
        # 计算3年FCFE平均增长率
        avg_growth = 0
        if len(fcfe_history) >= 3:
            growths = []
            for i in range(len(fcfe_history)-1):
                prev = fcfe_history[i+1][1]
                curr = fcfe_history[i][1]
                if prev > 0:
                    growths.append((curr - prev) / prev)
            if growths:
                avg_growth = sum(growths) / len(growths)
        
        # 使用用户提供的增长率或历史平均增长率
        if not growth_rates:
            if avg_growth > 0:
                growth_rates = [avg_growth * 0.8, avg_growth, avg_growth * 1.2]
            else:
                growth_rates = [0.05, 0.08, 0.1]  # 默认增长率
        
        valuations = []
        for g in growth_rates:
            for r in discount_rates:
                # 两阶段DCF模型
                # 第一阶段: 5年高增长期
                terminal_value = 0
                present_value = 0
                for year in range(1, 6):
                    fcfe = latest_fcfe * (1 + g) ** year
                    present_value += fcfe / ((1 + r) ** year)
                
                # 第二阶段: 永续增长率为g/2
                terminal_growth = g / 2
                terminal_fcfe = latest_fcfe * (1 + g) ** 5 * (1 + terminal_growth)
                terminal_value = terminal_fcfe / (r - terminal_growth) / (1 + r) ** 5
                
                total_value = (present_value + terminal_value) / self.total_shares  # 每股价值
                valuations.append({
                    'growth_rate': g,
                    'discount_rate': r,
                    'value': total_value,
                    'premium': (total_value - self.latest_price) / self.latest_price * 100
                })
        
        return valuations, None
    
    def generate_valuation_report(self, pe_range, pb_range, growth_rates, discount_rates, ev_ebitda_range):
        """生成估值报告"""
        report = []
        
        # 基本信息
        report.append(f"股票代码: {self.ts_code}")
        report.append(f"股票名称: {self.stock_info['name']}")
        report.append(f"当前价格: {self.latest_price:.2f} 元")
        report.append(f"总股本: {self.total_shares/100000000:.2f} 亿股")
        report.append(f"市值: {self.market_cap:.2f} 亿元")
        
        # PE估值
        current_pe, pe_history = self.calculate_pe_ratio()
        report.append("\nPE估值:")
        report.append(f"当前PE: {current_pe:.2f}")
        for pe in pe_range:
            value = float(pe) * (self.financials.iloc[0]['n_income'] / 100000000) / (self.total_shares / 100000000)
            premium = (value - self.latest_price) / self.latest_price * 100
            report.append(f"PE={pe}: {value:.2f} 元/股 ({premium:+.2f}%)")
        
        # PB估值
        current_pb, pb_history = self.calculate_pb_ratio()
        report.append("\nPB估值:")
        report.append(f"当前PB: {current_pb:.2f}")
        for pb in pb_range:
            value = float(pb) * self.financials.iloc[0]['bps']
            premium = (value - self.latest_price) / self.latest_price * 100
            report.append(f"PB={pb}: {value:.2f} 元/股 ({premium:+.2f}%)")
        

        
        # DCF估值 (FCFF完整资本性支出)
        fcff_full_vals, fcff_full_err = self.perform_fcff_valuation_full_capex(growth_rates, discount_rates)
        report.append("\nDCF估值(FCFF完整资本性支出):")
        if fcff_full_err:
            report.append(fcff_full_err)
        else:
            for val in fcff_full_vals:
                report.append(f"增长率={val['growth_rate']:.1%}, 折现率={val['discount_rate']:.1%}: {val['value']:.2f} 元/股 ({val['premium']:+.2f}%)")
        
        # DCF估值 (FCFE完整资本性支出)
        fcfe_full_vals, fcfe_full_err = self.perform_fcfe_valuation_full_capex(growth_rates, discount_rates)
        report.append("\nDCF估值(FCFE完整资本性支出):")
        if fcfe_full_err:
            report.append(fcfe_full_err)
        else:
            for val in fcfe_full_vals:
                report.append(f"增长率={val['growth_rate']:.1%}, 折现率={val['discount_rate']:.1%}: {val['value']:.2f} 元/股 ({val['premium']:+.2f}%)")
        
        # DCF估值 (FCFE调整后)
        fcfe_vals, fcfe_err = self.perform_fcfe_valuation_adjusted(growth_rates, discount_rates)
        report.append("\nDCF估值(FCFE基本资本性支出):")
        if fcfe_err:
            report.append(fcfe_err)
        else:
            for val in fcfe_vals:
                report.append(f"增长率={val['growth_rate']:.1%}, 折现率={val['discount_rate']:.1%}: {val['value']:.2f} 元/股 ({val['premium']:+.2f}%)")
        
        # DCF估值 (FCFF调整后)
        fcff_vals, fcff_err = self.perform_fcff_valuation_adjusted(growth_rates, discount_rates)
        report.append("\nDCF估值(FCFF基本资本性支出):")
        if fcff_err:
            report.append(fcff_err)
        else:
            for val in fcff_vals:
                report.append(f"增长率={val['growth_rate']:.1%}, 折现率={val['discount_rate']:.1%}: {val['value']:.2f} 元/股 ({val['premium']:+.2f}%)")
        # EV/EBITDA估值
        enterprise_value, ebitda, ev_to_ebitda = self.calculate_ev()
        report.append("\nEV/EBITDA估值:")
        report.append(f"当前EV/EBITDA: {ev_to_ebitda:.2f}")
        for multiple in ev_ebitda_range:
            value = (float(multiple) * ebitda - (enterprise_value - self.market_cap * 100000000)) / self.total_shares
            premium = (value - self.latest_price) / self.latest_price * 100
            report.append(f"EV/EBITDA={multiple}: {value:.2f} 元/股 ({premium:+.2f}%)")
        
        # 股息率
        current_yield, div_history, avg_div, payout_ratio = self.calculate_dividend_yield()
        report.append("\n股息分析:")
        report.append(f"当前股息率: {current_yield:.2f}%")
        report.append(f"3年平均分红: {avg_div:.2f} 元/股")
        report.append(f"分红支付率: {payout_ratio:.2f}%")
        
        # 增长分析
        income_growth, revenue_growth, cagr = self.calculate_growth_rate()
        report.append("\n增长分析:")
        report.append(f"3年净利润CAGR: {cagr.get('income_3y', 0):.2f}%")
        report.append(f"3年营收CAGR: {cagr.get('revenue_3y', 0):.2f}%")

        # DDM估值
        ddm_vals, ddm_err = self.calculate_ddm_valuation(growth_rates, discount_rates)
        report.append("\nDDM估值(股利贴现模型):")
        if ddm_err:
            report.append(ddm_err)
        else:
            for val in ddm_vals:
                report.append(f"增长率={val['growth_rate']:.1%}, 折现率={val['discount_rate']:.1%}: {val['value']:.2f} 元/股 ({val['premium']:+.2f}%)")
        
        # 综合分析
        report.append("\n\n=== 综合分析 ===")
        
        # 收集所有估值结果
        all_valuations = []
        
        # PE估值
        for pe in pe_range:
            value = float(pe) * (self.financials.iloc[0]['n_income'] / 100000000) / (self.total_shares / 100000000)
            all_valuations.append(('PE', value))
        
        # PB估值
        for pb in pb_range:
            value = float(pb) * self.financials.iloc[0]['bps']
            all_valuations.append(('PB', value))
        
        # DCF估值
        if fcff_vals:
            for val in fcff_vals:
                all_valuations.append(('DCF(FCFF)', val['value']))
        if fcfe_vals:
            for val in fcfe_vals:
                all_valuations.append(('DCF(FCFE)', val['value']))
        
        # DDM估值
        if ddm_vals:
            for val in ddm_vals:
                all_valuations.append(('DDM', val['value']))
        
        # EV/EBITDA估值
        for multiple in ev_ebitda_range:
            value = (float(multiple) * ebitda - (enterprise_value - self.market_cap * 100000000)) / self.total_shares
            all_valuations.append(('EV/EBITDA', value))
        
        # 计算综合估值
        if all_valuations:
            # 按方法分类
            method_values = {}
            for method, value in all_valuations:
                if method not in method_values:
                    method_values[method] = []
                method_values[method].append(value)
            
            # 计算各方法中位数
            method_medians = {}
            for method, values in method_values.items():
                method_medians[method] = np.median(values)
            
            # 设置权重
            weights = {
                'DCF(FCFF)': 0.2,
                'DCF(FCFE)': 0.2,
                'DDM': 0.2,
                'PE': 0.15,
                'PB': 0.1,
                'EV/EBITDA': 0.1,
            }
            
            # 计算加权平均估值
            weighted_sum = 0
            total_weight = 0
            for method, median in method_medians.items():
                if method in weights:
                    weighted_sum += median * weights[method]
                    total_weight += weights[method]
            
            if total_weight > 0:
                weighted_avg = weighted_sum / total_weight
                report.append(f"\n综合估值(加权平均): {weighted_avg:.2f} 元/股")
                
                # 计算估值区间
                all_values = [v for _, v in all_valuations]
                min_val = min(all_values)
                max_val = max(all_values)
                report.append(f"估值区间: {min_val:.2f} - {max_val:.2f} 元/股")
                
                # 投资建议
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
                
                report.append(f"当前价格: {self.latest_price:.2f} 元/股 (相对综合估值: {premium:+.2f}%)")
                report.append(f"投资建议: {recommendation}")
        
        return "\n".join(report)

def main():
    """主程序入口"""
    args = parse_arguments()
    
    # 解析参数
    pe_range = args.pe.split(',')
    pb_range = args.pb.split(',')
    growth_rates = args.growth.split(',')
    discount_rates = args.discount.split(',')
    ev_ebitda_range = args.ev_ebitda.split(',')
    
    # 创建估值对象
    valuation = StockValuation(args.stock)
    
    # 生成并打印估值报告
    report = valuation.generate_valuation_report(
        pe_range=pe_range,
        pb_range=pb_range,
        growth_rates=growth_rates,
        discount_rates=discount_rates,
        ev_ebitda_range=ev_ebitda_range
    )
    
    print("\n" + "="*50 + " 股票估值报告 " + "="*50)
    print(report)
    print("="*112)

if __name__ == "__main__":
    main()
