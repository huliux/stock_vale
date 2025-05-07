import numpy as np
import pandas as pd
import os # 用于读取环境变量
import inspect # 用于 DCF 辅助函数判断调用者
import traceback # For detailed error logging in combo calc
from typing import Dict, Any, Optional, List # Added Optional and List

class ValuationCalculator:
    # Remove dcf_growth_cap from constructor signature
    def __init__(self, stock_info, latest_price, total_shares, financials, dividends, market_cap):
        self.stock_info = stock_info
        self.latest_price = latest_price
        # total_shares is passed as actual share count from api/main.py
        self.total_shares = total_shares if total_shares is not None else 0
        # financials should be the processed data dictionary
        self.financials_dict = financials if isinstance(financials, dict) else {}
        # Keep a reference to the balance sheet for net debt calculation if needed elsewhere
        # Use .get with default to handle cases where 'balance_sheet' might be missing
        self.financials = self.financials_dict.get('balance_sheet', pd.DataFrame()) 
        self.dividends = dividends   # DataFrame containing yearly dividend data, expected sorted descending by year
        self.market_cap = market_cap # 单位：亿元
        
        # 配置项
        self.tax_rate = 0.25 # 有效税率，TODO: 未来可考虑从财报计算

        # 从环境变量加载 WACC 和 DCF Cap 参数
        try:
            self.beta = float(os.getenv('DEFAULT_BETA', '1.0'))
            self.risk_free_rate = float(os.getenv('RISK_FREE_RATE', '0.03'))
            self.market_risk_premium = float(os.getenv('MARKET_RISK_PREMIUM', '0.05'))
            self.cost_of_debt_pretax = float(os.getenv('DEFAULT_COST_OF_DEBT', '0.05'))
            self.dcf_growth_cap = float(os.getenv('DCF_GROWTH_CAP', '0.25'))
            if not (0 < self.dcf_growth_cap <= 1): # Basic validation
                 print(f"警告：环境变量 DCF_GROWTH_CAP ({self.dcf_growth_cap}) 无效，将使用默认值 0.25。")
                 self.dcf_growth_cap = 0.25
        except ValueError:
            print("警告：无法从环境变量加载数值参数 (WACC 或 DCF_GROWTH_CAP)，将使用默认值。")
            self.beta = 1.0
            self.risk_free_rate = 0.03
            self.market_risk_premium = 0.05
            self.cost_of_debt_pretax = 0.05
            self.dcf_growth_cap = 0.25 # Ensure default is set on error

        # Store defaults read from environment or hardcoded
        self.default_beta = self.beta
        self.default_risk_free_rate = self.risk_free_rate
        self.default_market_risk_premium = self.market_risk_premium
        self.default_cost_of_debt_pretax = self.cost_of_debt_pretax
        self.default_tax_rate = self.tax_rate
        self.default_size_premium = float(os.getenv('DEFAULT_SIZE_PREMIUM', '0.0'))
        self.default_target_debt_ratio = float(os.getenv('TARGET_DEBT_RATIO', '0.45')) # Default target ratio

        self.last_calculated_wacc: Optional[float] = None
        self.last_calculated_ke: Optional[float] = None


    def _get_wacc_and_ke(self, params: dict):
        """
        Internal helper to calculate WACC and Ke based on provided parameters or defaults.
        Args:
            params (dict): A dictionary potentially containing request overrides for WACC calculation.
                           Keys like 'target_debt_ratio', 'cost_of_debt', 'tax_rate',
                           'risk_free_rate', 'beta', 'market_risk_premium', 'size_premium'.
        Returns:
            tuple: (wacc, cost_of_equity) or (None, None) if calculation fails.
        """
        try:
            debt_ratio = params.get('target_debt_ratio', self.default_target_debt_ratio)
            cost_of_debt = params.get('cost_of_debt', self.default_cost_of_debt_pretax)
            tax_rate = params.get('tax_rate', self.default_tax_rate)
            rf_rate = params.get('risk_free_rate', self.default_risk_free_rate)
            beta = params.get('beta', self.default_beta)
            mrp = params.get('market_risk_premium', self.default_market_risk_premium)
            size_premium = params.get('size_premium', self.default_size_premium)

            if not (0 <= debt_ratio <= 1):
                print(f"警告: 无效的目标债务比率 ({debt_ratio})，将使用默认值 {self.default_target_debt_ratio}")
                debt_ratio = self.default_target_debt_ratio
            equity_ratio = 1.0 - debt_ratio

            if not (0 <= tax_rate <= 1):
                 print(f"警告: 无效的税率 ({tax_rate})，将使用默认值 {self.default_tax_rate}")
                 tax_rate = self.default_tax_rate

            cost_of_equity = rf_rate + beta * mrp + size_premium
            if np.isnan(cost_of_equity) or np.isinf(cost_of_equity) or cost_of_equity <= 0:
                 print(f"警告: 计算出的权益成本(Ke)无效或非正 ({cost_of_equity:.4f})，无法计算 WACC。参数: Rf={rf_rate}, Beta={beta}, MRP={mrp}, SP={size_premium}")
                 return None, None

            cost_of_debt_after_tax = cost_of_debt * (1 - tax_rate)
            if np.isnan(cost_of_debt_after_tax) or np.isinf(cost_of_debt_after_tax):
                 print(f"警告: 计算出的税后债务成本无效 ({cost_of_debt_after_tax:.4f})，无法计算 WACC。参数: Kd={cost_of_debt}, Tax={tax_rate}")
                 return None, cost_of_equity

            wacc = (equity_ratio * cost_of_equity) + (debt_ratio * cost_of_debt_after_tax)

            if np.isnan(wacc) or np.isinf(wacc) or not (0 < wacc < 1):
                 print(f"警告: 计算出的 WACC ({wacc:.4f}) 无效或超出合理范围 (0-100%)。Ke={cost_of_equity:.4f}, Kd(AT)={cost_of_debt_after_tax:.4f}, DebtRatio={debt_ratio:.2f}")
                 return None, cost_of_equity

            return wacc, cost_of_equity

        except Exception as e:
            print(f"计算 WACC 和 Ke 时出错: {e}")
            return None, None


    def calculate_wacc_based_on_market_values(self):
        """
        计算基于当前市场价值的 WACC (保留原始逻辑，可能用于参考或回退)。
        """
        try:
            cost_of_equity_default = self.default_risk_free_rate + self.default_beta * self.default_market_risk_premium + self.default_size_premium

            # Use the balance sheet from the processed data dictionary
            bs_df = self.financials_dict.get('balance_sheet')
            if bs_df is None or bs_df.empty:
                print("财务数据(资产负债表)为空，无法计算 WACC")
                return None

            latest_finance = bs_df.iloc[-1] # Assuming sorted ascending by date

            market_cap_value = self.market_cap * 100000000
            if market_cap_value <= 0:
                print("市值非正，无法计算 WACC")
                return None

            lt_borr = float(latest_finance.get('lt_borr', 0) or 0)
            st_borr = float(latest_finance.get('st_borr', 0) or 0)
            bond_payable = float(latest_finance.get('bond_payable', 0) or 0)
            debt_market_value = lt_borr + st_borr + bond_payable

            if debt_market_value <= 0:
                 total_liab = float(latest_finance.get('total_liab', 0) or 0)
                 if total_liab <= 0:
                      print("警告: 无法获取有效债务数据（有息或总负债），假设债务为零计算 WACC")
                      debt_market_value = 0
                 else:
                      debt_market_value = total_liab
                      print("警告: 未找到明确的有息负债数据，使用总负债近似债务市值计算 WACC，结果可能不准确")

            total_capital = market_cap_value + debt_market_value
            if total_capital <= 0:
                 print("总资本非正，无法计算 WACC")
                 return None

            cost_of_equity = cost_of_equity_default

            cost_of_debt_after_tax = self.cost_of_debt_pretax * (1 - self.tax_rate)

            if total_capital == 0:
                 print("错误：总资本为零，无法计算权重。")
                 return None
            equity_weight = market_cap_value / total_capital
            debt_weight = debt_market_value / total_capital
            wacc = (equity_weight * cost_of_equity) + (debt_weight * cost_of_debt_after_tax)

            if not (0 < wacc < 1):
                 print(f"警告：计算出的 WACC ({wacc:.2%}) 超出合理范围 (0% - 100%)，请检查输入参数。")

            return wacc

        except Exception as e:
            print(f"计算 WACC 时出错: {e}")
            return None

    def calculate_pe_ratio(self):
        is_df = self.financials_dict.get('income_statement')
        if is_df is None or is_df.empty: return None
        try:
            latest_income = float(is_df.iloc[-1].get('n_income', 0) or 0)
            if latest_income <= 0 or self.market_cap is None or self.market_cap <= 0: return None
            current_pe = (self.market_cap * 100000000) / latest_income
            return current_pe if not np.isnan(current_pe) and not np.isinf(current_pe) else None
        except Exception as e:
            print(f"计算 PE 时出错: {e}")
            return None

    def calculate_pb_ratio(self):
        bs_df = self.financials_dict.get('balance_sheet')
        if bs_df is None or bs_df.empty: return None
        try:
            # BPS = Total Equity / Total Shares
            latest_equity = float(bs_df.iloc[-1].get('total_hldr_eqy_inc_min_int', 0) or 0) # 优先使用包含少数股东权益的
            if latest_equity == 0:
                latest_equity = float(bs_df.iloc[-1].get('total_hldr_eqy_exc_min_int', 0) or 0) # 备选不含少数股东权益
            
            if latest_equity <= 0 or self.total_shares is None or self.total_shares <= 0 or self.latest_price is None: return None
            
            latest_bps = latest_equity / self.total_shares
            if latest_bps <= 0: return None
            
            current_pb = self.latest_price / latest_bps
            return current_pb if not np.isnan(current_pb) and not np.isinf(current_pb) else None
        except Exception as e:
            print(f"计算 PB 时出错: {e}")
            return None

    def calculate_growth_rate(self):
        # This method might become less relevant as growth is handled by the forecaster
        # Keep for historical analysis display if needed
        income_growth = []
        revenue_growth = []
        cagr = {}
        is_df = self.financials_dict.get('income_statement')
        if is_df is None or len(is_df) < 2: return income_growth, revenue_growth, cagr
        try:
            # Assuming is_df is sorted ascending by date
            sorted_financials = is_df.sort_values(by='end_date', ascending=False)
            for i in range(len(sorted_financials) - 1):
                current_row = sorted_financials.iloc[i]
                prev_row = sorted_financials.iloc[i+1]
                # Check for yearly interval (approx 300-400 days)
                date_diff = (current_row['end_date'] - prev_row['end_date']).days
                if not (300 < date_diff < 400): continue 

                current_income = float(current_row.get('n_income', 0) or 0)
                prev_income = float(prev_row.get('n_income', 0) or 0)
                current_revenue = float(current_row.get('total_revenue', 0) or 0)
                prev_revenue = float(prev_row.get('total_revenue', 0) or 0)

                if prev_income != 0:
                    income_growth_rate = (current_income / prev_income - 1) * 100
                    if not np.isnan(income_growth_rate) and not np.isinf(income_growth_rate):
                        income_growth.append({'year': current_row['end_date'].year, 'rate': income_growth_rate})
                if prev_revenue > 0:
                    revenue_growth_rate = (current_revenue / prev_revenue - 1) * 100
                    if not np.isnan(revenue_growth_rate) and not np.isinf(revenue_growth_rate):
                        revenue_growth.append({'year': current_row['end_date'].year, 'rate': revenue_growth_rate})

            if len(sorted_financials) >= 4: # Need 4 points for 3-year CAGR
                latest_income = float(sorted_financials.iloc[0].get('n_income', 0) or 0)
                three_years_ago_income = float(sorted_financials.iloc[3].get('n_income', 0) or 0)
                if three_years_ago_income > 0 and latest_income > 0:
                    income_cagr = ((latest_income / three_years_ago_income) ** (1/3) - 1) * 100
                    if not np.isnan(income_cagr) and not np.isinf(income_cagr):
                         cagr['income_3y'] = income_cagr

                latest_revenue = float(sorted_financials.iloc[0].get('total_revenue', 0) or 0)
                three_years_ago_revenue = float(sorted_financials.iloc[3].get('total_revenue', 0) or 0)
                if three_years_ago_revenue > 0 and latest_revenue > 0:
                    revenue_cagr = ((latest_revenue / three_years_ago_revenue) ** (1/3) - 1) * 100
                    if not np.isnan(revenue_cagr) and not np.isinf(revenue_cagr):
                        cagr['revenue_3y'] = revenue_cagr
        except Exception as e:
            print(f"计算增长率时出错: {e}")
        return income_growth, revenue_growth, cagr

    def calculate_fcff_fcfe(self, capex_type: str = 'basic'):
        # This method calculates historical FCFF/FCFE, might still be useful for display
        # It needs access to multiple tables from self.financials_dict
        fcff_history = []
        fcfe_history = []
        is_df = self.financials_dict.get('income_statement')
        bs_df = self.financials_dict.get('balance_sheet')
        cf_df = self.financials_dict.get('cash_flow')

        if is_df is None or bs_df is None or cf_df is None or len(is_df) < 2 or len(bs_df) < 2 or len(cf_df) < 1:
             print("财务数据不足，无法计算历史 FCFF/FCFE")
             return None, None, [], [], capex_type

        # Merge dataframes on end_date for easier calculation
        try:
            merged_df = pd.merge(is_df, bs_df, on='end_date', how='inner', suffixes=('', '_bs'))
            merged_df = pd.merge(merged_df, cf_df, on='end_date', how='inner', suffixes=('', '_cf'))
            merged_df = merged_df.sort_values(by='end_date', ascending=False)
        except Exception as e:
            print(f"合并财务报表时出错: {e}")
            return None, None, [], [], capex_type

        for idx, row in merged_df.iterrows():
            year = row['end_date'].year
            try:
                # EBIAT
                ebit_indicator = float(row.get('ebit', 0) or 0)
                interest_expense = float(row.get('finan_exp', 0) or 0) 
                if ebit_indicator != 0: ebit = ebit_indicator
                else:
                    operating_profit = float(row.get('operate_profit', 0) or 0)
                    ebit = operating_profit - interest_expense 
                ebiat = ebit * (1 - self.tax_rate)
                if np.isnan(ebiat) or np.isinf(ebiat): ebiat = 0

                # D&A
                depreciation = float(row.get('depr_fa_coga_dpba', 0) or 0)
                amortization = float(row.get('amort_intang_assets', 0) or 0)
                da = depreciation + amortization
                if np.isnan(da) or np.isinf(da): da = 0

                # Capex
                capex_field = 'stot_out_inv_act' if capex_type == 'full' else 'c_pay_acq_const_fiolta'
                capital_expenditure = abs(float(row.get(capex_field, 0) or 0))
                if np.isnan(capital_expenditure) or np.isinf(capital_expenditure): capital_expenditure = 0

                # Change in NWC
                working_capital_change = 0
                current_assets = float(row.get('total_cur_assets', 0) or 0)
                current_liab = float(row.get('total_cur_liab', 0) or 0)
                cash = float(row.get('money_cap', 0) or 0)
                st_debt = float(row.get('st_borr', 0) or 0)
                current_nwc = (current_assets - cash) - (current_liab - st_debt)

                prev_year_index = idx + 1
                if prev_year_index < len(merged_df):
                    prev_row = merged_df.iloc[prev_year_index]
                    # Check year difference
                    if (row['end_date'] - prev_row['end_date']).days < 400: 
                        prev_assets = float(prev_row.get('total_cur_assets', 0) or 0)
                        prev_liab = float(prev_row.get('total_cur_liab', 0) or 0)
                        prev_cash = float(prev_row.get('money_cap', 0) or 0)
                        prev_st_debt = float(prev_row.get('st_borr', 0) or 0)
                        prev_nwc = (prev_assets - prev_cash) - (prev_liab - prev_st_debt)
                        if not (np.isnan(current_nwc) or np.isinf(current_nwc) or np.isnan(prev_nwc) or np.isinf(prev_nwc)):
                            working_capital_change = current_nwc - prev_nwc
                        else: working_capital_change = 0
                if np.isnan(working_capital_change) or np.isinf(working_capital_change): working_capital_change = 0

                # FCFF
                fcff = ebiat + da - capital_expenditure - working_capital_change
                fcff_value_to_store = fcff if not (np.isnan(fcff) or np.isinf(fcff)) else None

                # FCFE
                cash_recp_borrow = float(row.get('c_recp_borrow', 0) or 0)
                cash_prepay_amt_borr = float(row.get('c_prepay_amt_borr', 0) or 0)
                net_debt_increase = cash_recp_borrow - cash_prepay_amt_borr
                if np.isnan(net_debt_increase) or np.isinf(net_debt_increase): net_debt_increase = 0
                interest_paid_after_tax = abs(interest_expense) * (1 - self.tax_rate)
                if np.isnan(interest_paid_after_tax) or np.isinf(interest_paid_after_tax): interest_paid_after_tax = 0
                fcfe = None
                if fcff_value_to_store is not None:
                    fcfe = fcff_value_to_store - interest_paid_after_tax + net_debt_increase
                    fcfe_value_to_store = fcfe if not (np.isnan(fcfe) or np.isinf(fcfe)) else None
                else: fcfe_value_to_store = None

                fcff_history.append({'year': year, 'value': fcff_value_to_store})
                fcfe_history.append({'year': year, 'value': fcfe_value_to_store})

            except Exception as e:
                 print(f"计算 {year} 年历史 FCFF/FCFE ({capex_type} capex) 时出错: {e}")
                 fcff_history.append({'year': year, 'value': None})
                 fcfe_history.append({'year': year, 'value': None})

        latest_fcff = next((item['value'] for item in fcff_history if item['value'] is not None), None)
        latest_fcfe = next((item['value'] for item in fcfe_history if item['value'] is not None), None)
        return latest_fcff, latest_fcfe, fcff_history, fcfe_history, capex_type

    def calculate_ev(self):
        # Calculates historical EV/EBITDA
        try:
            bs_df = self.financials_dict.get('balance_sheet')
            is_df = self.financials_dict.get('income_statement')
            cf_df = self.financials_dict.get('cash_flow')
            if bs_df is None or is_df is None or cf_df is None or bs_df.empty or is_df.empty or cf_df.empty: 
                return None, None, None
            
            # Use latest available data
            latest_bs = bs_df.iloc[-1]
            latest_is = is_df[is_df['end_date'] == latest_bs['end_date']]
            latest_cf = cf_df[cf_df['end_date'] == latest_bs['end_date']]
            if latest_is.empty or latest_cf.empty:
                 print("警告：最新资产负债表日期无法匹配利润表或现金流量表，无法计算最新EV/EBITDA")
                 return None, None, None
            latest_is = latest_is.iloc[0]
            latest_cf = latest_cf.iloc[0]

            market_cap_value = self.market_cap * 100000000
            lt_borr = float(latest_bs.get('lt_borr', 0) or 0)
            st_borr = float(latest_bs.get('st_borr', 0) or 0)
            bond_payable = float(latest_bs.get('bond_payable', 0) or 0)
            total_debt = lt_borr + st_borr + bond_payable
            money_cap = float(latest_bs.get('money_cap', 0) or 0)
            cash_equivalents = money_cap if money_cap > 0 else 0
            if cash_equivalents == 0: print("警告: 未能获取有效的货币资金(money_cap)，计算EV时假设现金等价物为0。")
            
            enterprise_value = market_cap_value + total_debt - cash_equivalents

            ebitda_indicator = float(latest_is.get('ebitda', 0) or 0) # Check IS first
            if ebitda_indicator == 0: ebitda_indicator = float(latest_cf.get('ebitda', 0) or 0) # Then CF

            if ebitda_indicator != 0: ebitda = ebitda_indicator
            else:
                ebit_indicator = float(latest_is.get('ebit', 0) or 0)
                interest_expense = float(latest_is.get('finan_exp', 0) or 0)
                if ebit_indicator != 0: ebit = ebit_indicator
                else:
                    operating_profit = float(latest_is.get('operate_profit', 0) or 0)
                    ebit = operating_profit - interest_expense
                depreciation = float(latest_cf.get('depr_fa_coga_dpba', 0) or 0)
                amortization = float(latest_cf.get('amort_intang_assets', 0) or 0)
                da = depreciation + amortization
                ebitda = ebit + da
                print("警告: 未找到直接的 EBITDA 数据，使用 EBIT + D&A 估算。")
            
            ev_to_ebitda = None
            if ebitda is not None and ebitda != 0 and enterprise_value is not None:
                ev_to_ebitda = enterprise_value / ebitda
                if np.isnan(ev_to_ebitda) or np.isinf(ev_to_ebitda): ev_to_ebitda = None
            elif ebitda is not None and ebitda == 0: print("EBITDA为零，无法计算 EV/EBITDA")
            
            return enterprise_value, ebitda, ev_to_ebitda
        except Exception as e:
            print(f"计算 EV/EBITDA 时出错: {e}")
            return None, None, None

    def calculate_dividend_yield(self):
        current_yield, dividend_history, avg_div, payout_ratio = 0, [], 0, 0
        if self.dividends is None or self.dividends.empty: return current_yield, dividend_history, avg_div, payout_ratio
        try:
            sorted_dividends = self.dividends.sort_values(by='end_date', ascending=False) # Assuming 'end_date' exists
            latest_div_row = sorted_dividends.iloc[0]
            # Use 'dividend' column if 'cash_div_tax' not present
            div_col = 'cash_div_tax' if 'cash_div_tax' in latest_div_row else 'dividend'
            latest_div_per_share = float(latest_div_row.get(div_col, 0) or 0)

            if self.latest_price is not None and self.latest_price > 0 and latest_div_per_share > 0:
                current_yield = (latest_div_per_share / self.latest_price) * 100

            for _, row in sorted_dividends.iterrows():
                year = row['end_date'].year # Assuming 'end_date' is datetime
                div_per_share = float(row.get(div_col, 0) or 0)
                if year > 0 and div_per_share > 0:
                    dividend_history.append({'year': year, 'dividend_per_share': div_per_share})

            if len(dividend_history) >= 3:
                recent_dividends = [d['dividend_per_share'] for d in dividend_history[:3]]
                if recent_dividends: avg_div = sum(recent_dividends) / len(recent_dividends)

            is_df = self.financials_dict.get('income_statement')
            if is_df is not None and not is_df.empty:
                latest_income = float(is_df.iloc[-1].get('n_income', 0) or 0)
                if latest_income > 0 and latest_div_per_share > 0 and self.total_shares is not None and self.total_shares > 0:
                    total_dividend = latest_div_per_share * self.total_shares
                    payout_ratio = (total_dividend / latest_income) * 100
        except Exception as e:
            print(f"计算股息率时出错: {e}")
        return current_yield, dividend_history, avg_div, payout_ratio

    def _get_growth_rates_for_dcf(self, history_values):
        # This helper might be deprecated if growth rates are determined differently
        avg_growth = 0
        if len(history_values) >= 4:
            growths = []
            sorted_history = sorted([h for h in history_values if h['value'] is not None], key=lambda x: x['year'], reverse=True)
            if len(sorted_history) >= 4:
                for i in range(3):
                     if sorted_history[i]['year'] == sorted_history[i+1]['year'] + 1:
                         curr = sorted_history[i]['value']
                         prev = sorted_history[i+1]['value']
                         if prev is not None and curr is not None and prev != 0:
                             growth = (curr - prev) / abs(prev)
                             if -1 <= growth <= 2: growths.append(growth)
                if growths: avg_growth = sum(growths) / len(growths)
        if avg_growth > self.dcf_growth_cap:
            print(f"警告: 计算出的平均增长率 ({avg_growth:.2%}) 过高，已限制为 {self.dcf_growth_cap:.0%}")
            avg_growth = self.dcf_growth_cap
        if avg_growth > 0.01:
            low_g = max(0, avg_growth * 0.8)
            mid_g = avg_growth
            high_g = max(mid_g, min(0.3, avg_growth * 1.2))
            growth_rates = sorted(list(set([round(low_g, 4), round(mid_g, 4), round(high_g, 4)])))
            if len(growth_rates) < 3:
                 if len(growth_rates) == 2: growth_rates.append(min(0.3, round(growth_rates[1] + 0.01, 4)))
                 elif len(growth_rates) == 1:
                      rate = growth_rates[0]
                      growth_rates = [max(0, round(rate - 0.01, 4)), rate, min(0.3, round(rate + 0.01, 4))]
                 growth_rates = sorted(list(set(growth_rates)))[:3]
        else: growth_rates = [0.01, 0.03, 0.05]
        return growth_rates

    def _perform_dcf_valuation(self, latest_fcf, fcf_history, growth_rates, discount_rates_override, wacc_params: dict, is_fcff=False):
        # This method is likely deprecated in favor of calculate_dcf_valuation_from_forecast
        # Keep for potential backward compatibility or specific use cases if needed
        # ... (implementation remains the same for now) ...
        if latest_fcf is None or latest_fcf <= 0:
            return None, "自由现金流为负、零或计算失败"
        if growth_rates is None:
            growth_rates = self._get_growth_rates_for_dcf(fcf_history)
        else: growth_rates = [float(g) for g in growth_rates]
        calculated_wacc, calculated_ke = self._get_wacc_and_ke(wacc_params)
        if discount_rates_override is None:
            base_rate = calculated_wacc if is_fcff else calculated_ke
            if base_rate is None:
                 error_msg = "WACC 计算失败" if is_fcff else "股权成本(Ke) 计算失败"
                 self.last_calculated_wacc = calculated_wacc
                 self.last_calculated_ke = calculated_ke
                 return None, error_msg + "，无法进行 DCF 估值"
            discount_rates = [max(0.01, base_rate - 0.01), base_rate, base_rate + 0.01]
        else: discount_rates = [float(r) for r in discount_rates_override]
        self.last_calculated_wacc = calculated_wacc
        self.last_calculated_ke = calculated_ke
        valuations = []
        for g in growth_rates:
            for r in discount_rates:
                terminal_growth = min(g * 0.5, r * 0.8, self.risk_free_rate)
                if terminal_growth >= r:
                    print(f"警告: DCF 永续增长率({terminal_growth:.2%}) >= 折现率({r:.2%})，跳过组合 g={g:.2%}, r={r:.2%}")
                    continue
                try:
                    present_value_fcf = 0
                    for year in range(1, 6):
                        fcf = latest_fcf * (1 + g) ** year
                        present_value_fcf += fcf / ((1 + r) ** year)
                    terminal_fcf_year6 = latest_fcf * (1 + g) ** 5 * (1 + terminal_growth)
                    terminal_value_at_year5 = terminal_fcf_year6 / (r - terminal_growth)
                    terminal_value_present = terminal_value_at_year5 / (1 + r) ** 5
                    total_value_enterprise_or_equity = present_value_fcf + terminal_value_present
                    value_per_share = None
                    if is_fcff:
                        bs_df = self.financials_dict.get('balance_sheet')
                        if bs_df is not None and not bs_df.empty:
                            latest_finance = bs_df.iloc[-1]
                            lt_borr = float(latest_finance.get('lt_borr', 0) or 0)
                            st_borr = float(latest_finance.get('st_borr', 0) or 0)
                            bond_payable = float(latest_finance.get('bond_payable', 0) or 0)
                            total_debt = lt_borr + st_borr + bond_payable
                            money_cap = float(latest_finance.get('money_cap', 0) or 0)
                            net_debt = total_debt - money_cap
                            total_equity_value = total_value_enterprise_or_equity - net_debt
                            if self.total_shares > 0: value_per_share = total_equity_value / self.total_shares
                            else: print("总股本非正，无法计算FCFF的每股价值")
                        else: print("财务数据(资产负债表)为空，无法计算FCFF的净债务")
                    else:
                        if self.total_shares > 0: value_per_share = total_value_enterprise_or_equity / self.total_shares
                        else: print("总股本非正，无法计算FCFE的每股价值")
                    premium = None
                    if value_per_share is not None and self.latest_price is not None and self.latest_price > 0:
                        premium = (value_per_share / self.latest_price - 1) * 100
                    valuations.append({'growth_rate': g, 'discount_rate': r, 'value': value_per_share, 'premium': premium})
                except OverflowError: print(f"DCF 计算溢出错误，跳过组合 g={g:.2%}, r={r:.2%}")
                except ZeroDivisionError: print(f"DCF 除零错误 (r={r:.2%}, g_terminal={terminal_growth:.2%})，跳过组合 g={g:.2%}, r={r:.2%}")
        return valuations, None


    def calculate_ddm_valuation(self, growth_rates=None, discount_rates_override=None, wacc_params: dict = {}):
        current_yield, div_history, avg_div, _ = self.calculate_dividend_yield()
        if avg_div is None or avg_div <= 0: return None, "无有效平均分红数据，无法进行DDM估值"
        
        # Determine growth rates for DDM (can use a simpler logic or reuse _get_growth_rates_for_dcf with dividend history)
        if growth_rates is None:
             # Example: Use historical dividend growth if available, else default
             div_growth_rates = self._get_growth_rates_for_dcf([{'year': d['year'], 'value': d['dividend_per_share']} for d in div_history])
             growth_rates = div_growth_rates if div_growth_rates else [0.01, 0.02, 0.03] # Fallback if history insufficient
        else: 
             growth_rates = [float(g) for g in growth_rates]

        _, calculated_ke = self._get_wacc_and_ke(wacc_params)
        if discount_rates_override is None:
            if calculated_ke is None:
                 self.last_calculated_ke = calculated_ke
                 return None, "无法计算股权成本(Ke)，无法进行DDM估值"
            discount_rates = [max(0.01, calculated_ke - 0.01), calculated_ke, calculated_ke + 0.01]
        else: 
             discount_rates = [float(r) for r in discount_rates_override]
        self.last_calculated_ke = calculated_ke

        valuations = []
        for g in growth_rates:
            for r in discount_rates:
                terminal_growth = min(g * 0.5, r * 0.8, self.risk_free_rate)
                if terminal_growth >= r:
                    print(f"警告: DDM 永续增长率({terminal_growth:.2%}) >= 折现率({r:.2%})，跳过组合 g={g:.2%}, r={r:.2%}")
                    continue
                try:
                    present_value_dividends = 0
                    base_dividend = avg_div
                    for year in range(1, 6): # 5-year high growth stage
                        dividend = base_dividend * (1 + g) ** year
                        present_value_dividends += dividend / ((1 + r) ** year)
                    
                    terminal_dividend_year6 = base_dividend * (1 + g) ** 5 * (1 + terminal_growth)
                    if r - terminal_growth <= 1e-9:
                         print(f"警告: DDM 折现率({r:.2%}) 接近或小于等于永续增长率({terminal_growth:.2%})，跳过组合 g={g:.2%}, r={r:.2%}")
                         continue
                    terminal_value_at_year5 = terminal_dividend_year6 / (r - terminal_growth)
                    terminal_value_present = terminal_value_at_year5 / (1 + r) ** 5
                    
                    total_value_per_share = present_value_dividends + terminal_value_present
                    premium = None
                    if self.latest_price is not None and self.latest_price > 0: 
                        premium = (total_value_per_share / self.latest_price - 1) * 100
                    valuations.append({'growth_rate': g, 'discount_rate': r, 'value': total_value_per_share, 'premium': premium})
                except OverflowError: print(f"DDM 计算溢出错误，跳过组合 g={g:.2%}, r={r:.2%}")
                except ZeroDivisionError: print(f"DDM 除零错误 (r={r:.2%}, g_terminal={terminal_growth:.2%})，跳过组合 g={g:.2%}, r={r:.2%}")
        
        return valuations, None

    # --- DCF methods based on historical FCF (Restored) ---
    def perform_fcff_valuation_basic_capex(self, growth_rates=None, discount_rates_override=None, wacc_params: dict = {}):
        latest_fcff, _, fcff_history, _, _ = self.calculate_fcff_fcfe(capex_type='basic')
        return self._perform_dcf_valuation(latest_fcff, fcff_history, growth_rates, discount_rates_override, wacc_params, is_fcff=True)
    def perform_fcfe_valuation_basic_capex(self, growth_rates=None, discount_rates_override=None, wacc_params: dict = {}):
        _, latest_fcfe, _, fcfe_history, _ = self.calculate_fcff_fcfe(capex_type='basic')
        return self._perform_dcf_valuation(latest_fcfe, fcfe_history, growth_rates, discount_rates_override, wacc_params, is_fcff=False)
    def perform_fcfe_valuation_full_capex(self, growth_rates=None, discount_rates_override=None, wacc_params: dict = {}):
        _, latest_fcfe, _, fcfe_history, _ = self.calculate_fcff_fcfe(capex_type='full')
        return self._perform_dcf_valuation(latest_fcfe, fcfe_history, growth_rates, discount_rates_override, wacc_params, is_fcff=False)
    def perform_fcff_valuation_full_capex(self, growth_rates=None, discount_rates_override=None, wacc_params: dict = {}):
        latest_fcff, _, fcff_history, _, _ = self.calculate_fcff_fcfe(capex_type='full')
        return self._perform_dcf_valuation(latest_fcff, fcff_history, growth_rates, discount_rates_override, wacc_params, is_fcff=True)

    def get_other_analysis(self):
        analysis = {'dividend_analysis': None, 'growth_analysis': None}
        try:
            current_yield, _, avg_div, payout_ratio = self.calculate_dividend_yield()
            analysis['dividend_analysis'] = {'current_yield_pct': current_yield, 'avg_dividend_3y': avg_div, 'payout_ratio_pct': payout_ratio}
            _, _, cagr = self.calculate_growth_rate()
            analysis['growth_analysis'] = {'net_income_cagr_3y': cagr.get('income_3y'), 'revenue_cagr_3y': cagr.get('revenue_3y')}
        except Exception as e: print(f"计算其他分析时出错: {e}")
        return analysis

    def get_combo_valuations(self, 
                             main_dcf_result_dict: Optional[Dict[str, Any]], 
                             pe_multiples: List[str], 
                             pb_multiples: List[str], 
                             ev_ebitda_multiples: List[str], 
                             wacc_params: dict = {}):
        """
        计算新的绝对估值组合（包含安全边际）及投资建议。
        Args:
            main_dcf_result_dict (Optional[Dict[str, Any]]): calculate_dcf_valuation_from_forecast 的结果。
            pe_multiples, pb_multiples, ev_ebitda_multiples: 用于相对估值参考。
            wacc_params (dict): 包含 WACC/Ke 计算所需参数的字典。
        """
        combos_with_margin = {} # Store results as {'Alias': {'value': float, 'safety_margin_pct': float}} or None
        investment_advice = {}
        # Initialize attributes to store calculated WACC/Ke for the response
        # WACC/Ke calculation might be needed for DDM or if main_dcf_result is missing
        calculated_wacc, calculated_ke = self._get_wacc_and_ke(wacc_params)
        self.last_calculated_wacc = calculated_wacc
        self.last_calculated_ke = calculated_ke
        
        try:
            # --- 提取主 DCF 估值结果 ---
            val_dcf = None
            if main_dcf_result_dict and main_dcf_result_dict.get("error") is None:
                val_dcf = main_dcf_result_dict.get('value_per_share')

            # --- 计算 DDM 估值结果 ---
            # DDM calculation needs Ke, which is calculated above
            # Pass wacc_params to ensure consistency if user overrides are present
            # Use default growth rates for DDM sensitivity, or allow override via wacc_params if needed
            ddm_growth_rates = wacc_params.get('ddm_growth_rates') # Example: allow override
            ddm_discount_rates = wacc_params.get('ddm_discount_rates_override') # Example: allow override
            ddm_results, _ = self.calculate_ddm_valuation(
                growth_rates=ddm_growth_rates, 
                discount_rates_override=ddm_discount_rates, 
                wacc_params=wacc_params
            ) 
            
            def extract_central_value(results):
                # DDM still returns a list of valuations for sensitivity, extract central value
                if not results: return None
                valid_values = [r['value'] for r in results if r and r.get('value') is not None and not np.isnan(r['value'])]
                if not valid_values: return None
                # Use median for DDM sensitivity results
                return np.median(valid_values) if valid_values else None

            val_ddm = extract_central_value(ddm_results or [])

            # --- Helper to calculate safety margin ---
            def calculate_safety_margin_pct(value, price):
                if value is not None and not np.isnan(value) and price is not None and price > 0:
                    return (value / price - 1) * 100
                return None

            # --- 计算新的绝对估值组合及其安全边际 ---
            def safe_avg(*args):
                valid_args = [arg for arg in args if arg is not None and not np.isnan(arg)]
                return sum(valid_args) / len(valid_args) if valid_args else None

            # Calculate combo values based on the single DCF result and DDM
            combo_values = {
                'DCF_Forecast': val_dcf,
                'DDM': val_ddm,
                'Avg_DCF_DDM': safe_avg(val_dcf, val_ddm),
                # Add more relevant combos if needed, e.g., weighting
            }
            
            # Example weighted composite valuation (adjust weights as needed)
            composite_valuation_value = None
            if val_dcf is not None and val_ddm is not None:
                 composite_valuation_value = val_dcf * 0.7 + val_ddm * 0.3 # Example: 70% DCF, 30% DDM
            elif val_dcf is not None:
                 composite_valuation_value = val_dcf
            elif val_ddm is not None:
                 composite_valuation_value = val_ddm
                 
            combo_values['Composite_Valuation'] = composite_valuation_value

            # Now populate combos_with_margin including safety margin
            for key, value in combo_values.items():
                if value is not None and not np.isnan(value):
                    margin = calculate_safety_margin_pct(value, self.latest_price)
                    combos_with_margin[key] = {'value': value, 'safety_margin_pct': margin}
                else:
                    combos_with_margin[key] = None # Keep combo as None if value is None

            # --- 生成投资建议 (基于安全边际和关键组合) ---
            # Use DCF and DDM as the base for advice
            advice_base_values = [v for v in [val_dcf, val_ddm] if v is not None and not np.isnan(v)]
            min_intrinsic_value_for_advice = min(advice_base_values) if advice_base_values else None
            avg_intrinsic_value_for_advice = safe_avg(*advice_base_values)
            max_intrinsic_value_for_advice = max(advice_base_values) if advice_base_values else None

            # Use safety margin based on the minimum of the core absolute valuations
            safety_margin_advice = calculate_safety_margin_pct(min_intrinsic_value_for_advice, self.latest_price) 

            advice = "无法评估"
            reason = "缺乏足够的有效估值结果来生成建议。"
            if safety_margin_advice is not None and self.latest_price is not None:
                strong_buy_margin = 40 # Percentage
                buy_margin = 20        # Percentage
                sell_threshold_avg_factor = 1.2 # Sell if price > 1.2 * avg value
                strong_sell_threshold_max_factor = 1.5 # Strong sell if price > 1.5 * max value

                if safety_margin_advice > strong_buy_margin:
                    advice = "强烈买入"
                    reason = f"当前价格({self.latest_price:.2f})显著低于基于DCF和DDM估算的保守内在价值下限({min_intrinsic_value_for_advice:.2f})，提供了超过 {strong_buy_margin:.0f}% 的安全边际。"
                elif safety_margin_advice > buy_margin:
                    advice = "买入"
                    reason = f"当前价格({self.latest_price:.2f})低于基于DCF和DDM估算的保守内在价值下限({min_intrinsic_value_for_advice:.2f})，提供了约 {buy_margin:.0f}% 的安全边际。"
                elif max_intrinsic_value_for_advice is not None and self.latest_price > max_intrinsic_value_for_advice * strong_sell_threshold_max_factor:
                     advice = "强烈卖出"
                     reason = f"当前价格({self.latest_price:.2f})显著高于基于DCF和DDM估算的内在价值上限({max_intrinsic_value_for_advice:.2f})，估值过高风险极大。"
                elif avg_intrinsic_value_for_advice is not None and self.latest_price > avg_intrinsic_value_for_advice * sell_threshold_avg_factor:
                    advice = "卖出"
                    reason = f"当前价格({self.latest_price:.2f})高于基于DCF和DDM估算的内在价值平均值({avg_intrinsic_value_for_advice:.2f})超过 {int((sell_threshold_avg_factor-1)*100)}%，可能估值偏高。"
                else:
                    advice = "持有/观察"
                    reason = f"当前价格({self.latest_price:.2f})处于基于DCF和DDM估算的内在价值区间内({min_intrinsic_value_for_advice:.2f if min_intrinsic_value_for_advice is not None else 'N/A'}-{max_intrinsic_value_for_advice:.2f if max_intrinsic_value_for_advice is not None else 'N/A'})，安全边际 ({safety_margin_advice:.1f}%) 不显著。"

                # Safely access combo values for reason string
                dcf_val_str = f"{combos_with_margin.get('DCF_Forecast', {}).get('value', 'N/A'):.2f}" if combos_with_margin.get('DCF_Forecast') else 'N/A'
                ddm_val_str = f"{combos_with_margin.get('DDM', {}).get('value', 'N/A'):.2f}" if combos_with_margin.get('DDM') else 'N/A'
                composite_val_str = f"{combos_with_margin.get('Composite_Valuation', {}).get('value', 'N/A'):.2f}" if combos_with_margin.get('Composite_Valuation') else 'N/A'
                reason += f" 参考估值点：DCF={dcf_val_str}；DDM={ddm_val_str}；综合估值={composite_val_str}。"

            investment_advice = {
                'based_on': "安全边际 (基于 DCF & DDM), 综合估值, DCF_Forecast, DDM",
                'advice': advice,
                'reason': reason,
                'min_intrinsic_value': min_intrinsic_value_for_advice,
                'avg_intrinsic_value': avg_intrinsic_value_for_advice,
                'max_intrinsic_value': max_intrinsic_value_for_advice,
                'safety_margin_pct': safety_margin_advice 
            }

            # --- 添加参考信息 ---
            reference = []
            # Relative valuation multiples
            current_pe = self.calculate_pe_ratio()
            current_pb = self.calculate_pb_ratio()
            _, _, current_ev_ebitda = self.calculate_ev() # Recalculate EV/EBITDA based on latest data
            if current_pe is not None: reference.append(f"当前 PE: {current_pe:.2f}")
            if current_pb is not None: reference.append(f"当前 PB: {current_pb:.2f}")
            if current_ev_ebitda is not None: reference.append(f"当前 EV/EBITDA: {current_ev_ebitda:.2f}")

            # Absolute valuation references
            if val_dcf is not None: reference.append(f"DCF 估值: {val_dcf:.2f}")
            if val_ddm is not None: reference.append(f"DDM 估值: {val_ddm:.2f}")
            
            investment_advice['reference_info'] = "；".join(reference) + "。相对估值指标和绝对估值模型可结合市场情绪和公司基本面进行参考。"

            return combos_with_margin, investment_advice
        except Exception as e:
            print(f"计算综合估值和建议时发生严重错误: {e}\n{traceback.format_exc()}")
            return {}, {}

    def calculate_dcf_valuation_from_forecast(self,
                                              forecast_df: pd.DataFrame,
                                              wacc: float,
                                              terminal_value_method: str = 'exit_multiple',
                                              exit_multiple: Optional[float] = None,
                                              perpetual_growth_rate: Optional[float] = None) -> Dict[str, Any]:
        results = {
            "enterprise_value": None, "equity_value": None, "value_per_share": None,
            "pv_forecast_ufcf": None, "pv_terminal_value": None, "terminal_value": None,
            "wacc_used": wacc, "terminal_value_method_used": terminal_value_method,
            "perpetual_growth_rate_used": None, "exit_multiple_used": None,
            "forecast_period_years": None, "net_debt": None, "error": None
        }

        if forecast_df is None or forecast_df.empty:
            results["error"] = "预测数据为空，无法进行DCF计算。"
            return results
        if 'ufcf' not in forecast_df.columns:
            results["error"] = "预测数据中缺少 'ufcf' 列。"
            return results
        if not (0 < wacc < 1): # WACC should be a rate between 0 and 1
             results["error"] = f"无效的 WACC 值: {wacc:.4f} (应在 0 和 1 之间)。"
             return results

        try:
            forecast_years = len(forecast_df)
            results["forecast_period_years"] = forecast_years
            
            forecast_df_copy = forecast_df.copy() # Work on a copy
            forecast_df_copy['discount_factor'] = [(1 / (1 + wacc)) ** year for year in forecast_df_copy['year']]
            forecast_df_copy['pv_ufcf'] = forecast_df_copy['ufcf'] * forecast_df_copy['discount_factor']
            pv_forecast_ufcf = forecast_df_copy['pv_ufcf'].sum()
            results["pv_forecast_ufcf"] = pv_forecast_ufcf

            terminal_value = None
            last_forecast_year_data = forecast_df_copy.iloc[-1]

            if terminal_value_method == 'exit_multiple':
                results["exit_multiple_used"] = exit_multiple
                if exit_multiple is None or exit_multiple <= 0:
                    results["error"] = "使用退出乘数法需要提供有效的正退出乘数。"
                    return results
                if 'ebitda' not in forecast_df_copy.columns:
                     results["error"] = "预测数据中缺少 'ebitda' 列，无法使用退出乘数法。"
                     return results
                last_ebitda = last_forecast_year_data['ebitda']
                if last_ebitda is None or np.isnan(last_ebitda):
                     results["error"] = f"预测期最后一年的 EBITDA ({last_ebitda}) 无效，无法计算终值。"
                     return results
                if last_ebitda <= 0:
                    print(f"警告: 预测期最后一年的 EBITDA ({last_ebitda:.2f}) 非正，退出乘数法计算的终值可能不切实际。")
                terminal_value = last_ebitda * exit_multiple
            
            elif terminal_value_method == 'perpetual_growth':
                pg_rate_to_use = perpetual_growth_rate
                if pg_rate_to_use is None:
                    results["error"] = "使用永续增长法需要提供永续增长率。"
                    return results
                
                # Cap perpetual growth rate by risk-free rate
                pg_rate_to_use = min(pg_rate_to_use, self.risk_free_rate)
                results["perpetual_growth_rate_used"] = pg_rate_to_use

                if pg_rate_to_use >= wacc:
                    results["error"] = f"永续增长率 ({pg_rate_to_use:.4f}) 必须小于 WACC ({wacc:.4f})。"
                    return results
                
                last_ufcf = last_forecast_year_data['ufcf']
                if last_ufcf is None or np.isnan(last_ufcf) or last_ufcf <= 0:
                     results["error"] = f"预测期最后一年的 UFCF ({last_ufcf}) 非正或无效，无法使用永续增长法计算终值。"
                     return results
                terminal_value = last_ufcf * (1 + pg_rate_to_use) / (wacc - pg_rate_to_use)
            else:
                results["error"] = f"无效的终值计算方法: {terminal_value_method}"
                return results

            if terminal_value is None or np.isnan(terminal_value):
                 results["error"] = "终值计算结果无效。"
                 return results
            results["terminal_value"] = terminal_value

            pv_terminal_value = terminal_value * forecast_df_copy['discount_factor'].iloc[-1]
            results["pv_terminal_value"] = pv_terminal_value

            enterprise_value = pv_forecast_ufcf + pv_terminal_value
            results["enterprise_value"] = enterprise_value

            # Use the balance sheet from the processed data dictionary
            bs_df = self.financials_dict.get('balance_sheet')
            if bs_df is None or bs_df.empty:
                 results["error"] = (results["error"] + "; " if results["error"] else "") + "无法获取最新财务数据(资产负债表)计算净债务。"
                 # Set equity value and per share value to None if net debt cannot be calculated
                 results["equity_value"] = None
                 results["value_per_share"] = None
                 return results # Return early as further calculation depends on net debt

            latest_finance = bs_df.iloc[-1] # Assuming sorted ascending
            lt_borr = float(latest_finance.get('lt_borr', 0) or 0)
            st_borr = float(latest_finance.get('st_borr', 0) or 0)
            bond_payable = float(latest_finance.get('bond_payable', 0) or 0)
            total_debt = lt_borr + st_borr + bond_payable
            money_cap = float(latest_finance.get('money_cap', 0) or 0)
            net_debt = total_debt - money_cap
            results["net_debt"] = net_debt

            equity_value = enterprise_value - net_debt
            results["equity_value"] = equity_value

            if self.total_shares is not None and self.total_shares > 0:
                value_per_share = equity_value / self.total_shares
                results["value_per_share"] = value_per_share
            else:
                error_msg = "总股本非正，无法计算每股价值。"
                results["error"] = (results["error"] + "; " if results["error"] else "") + error_msg
                results["value_per_share"] = None # Ensure value_per_share is None
        
        except Exception as e:
            print(f"DCF 估值计算时发生错误: {e}\n{traceback.format_exc()}")
            results["error"] = (results["error"] + "; " if results["error"] else "") + f"计算错误: {str(e)}"

        return results

# End of class ValuationCalculator
