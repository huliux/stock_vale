import numpy as np
import pandas as pd
import configparser

class ValuationCalculator:
    def __init__(self, stock_info, latest_price, total_shares, financials, dividends, market_cap):
        self.stock_info = stock_info
        self.latest_price = latest_price
        self.total_shares = total_shares
        self.financials = financials
        self.dividends = dividends
        self.market_cap = market_cap
        
        # 读取配置文件
        config = configparser.ConfigParser()
        with open('config.ini', encoding='utf-8') as config_file:
            config.read_file(config_file)
        
        # 配置项
        self.tax_rate = float(config['VALUATION']['tax_rate'])
        self.default_growth_rates = [float(r) for r in config['VALUATION']['default_growth_rates'].split(',')]
        self.default_discount_rates = [float(r) for r in config['VALUATION']['default_discount_rates'].split(',')]
        self.cash_equivalents_percentage = float(config['VALUATION']['cash_equivalents_percentage'])
        self.depreciation_amortization_percentage = float(config['VALUATION']['depreciation_amortization_percentage'])

    def calculate_pe_ratio(self):
        """计算当前PE和历史PE"""
        # 计算当前PE
        latest_income = float(self.financials.iloc[0]['n_income'])
        current_pe = self.market_cap / (latest_income / 100000000)  # 将净利润也转为亿元
        
        return current_pe
    
    def calculate_pb_ratio(self):
        """计算当前PB"""
        # 计算当前PB
        latest_bps = float(self.financials.iloc[0]['bps'])
        current_pb = self.latest_price / latest_bps
        
        return current_pb
    
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
            
            # 计算EBIAT(税后息前利润) = (营业利润 + 财务费用) * (1 - 税率)
            operating_profit = float(row.get('operate_profit', 0))
            interest_expense = float(row.get('finan_exp', 0))
            tax_rate = self.tax_rate
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
            
            # FCFE = FCFF - 利息*(1-税率) + 净债务变动
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
        
        # 假设现金及现金等价物为总资产的指定百分比
        total_assets = float(latest_finance['total_assets'])
        cash_equivalents = total_assets * self.cash_equivalents_percentage
        
        enterprise_value = (self.market_cap * 100000000) + total_liabilities - cash_equivalents  # 转回为元
        
        # 计算EBITDA: 营业利润 + 折旧摊销
        operating_profit = float(latest_finance['operate_profit'])
        
        # 假设折旧摊销为营业收入的指定百分比
        total_revenue = float(latest_finance['total_revenue'])
        depreciation_amortization = total_revenue * self.depreciation_amortization_percentage
        
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
                growth_rates = self.default_growth_rates  # 默认增长率
        
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
        latest_fcff, _, fcff_history, _ = self.calculate_fcff_fcfe()
        
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
                growth_rates = self.default_growth_rates  # 默认增长率
        
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
        _, latest_fcfe, _, fcfe_history = self.calculate_fcff_fcfe()
        
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
                growth_rates = self.default_growth_rates  # 默认增长率
        
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
        _, latest_fcfe, _, fcfe_history = self.calculate_fcff_fcfe()
        
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
                growth_rates = self.default_growth_rates  # 默认增长率
        
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

    def perform_fcff_valuation_adjusted(self, growth_rates, discount_rates):
        """基于调整后FCFF的DCF估值"""
        latest_fcff, _, fcff_history, _ = self.calculate_fcff_fcfe()
        
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
                growth_rates = self.default_growth_rates  # 默认增长率
        
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
