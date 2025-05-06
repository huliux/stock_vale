import numpy as np
import pandas as pd
import os # 用于读取环境变量
import inspect # 用于 DCF 辅助函数判断调用者
import traceback # For detailed error logging in combo calc

class ValuationCalculator:
    # Remove dcf_growth_cap from constructor signature
    def __init__(self, stock_info, latest_price, total_shares, financials, dividends, market_cap):
        self.stock_info = stock_info
        self.latest_price = latest_price
        # total_shares is passed as actual share count from api/main.py
        self.total_shares = total_shares if total_shares is not None else 0
        self.financials = financials # DataFrame containing yearly financial data, expected sorted descending by year
        self.dividends = dividends   # DataFrame containing yearly dividend data, expected sorted descending by year
        self.market_cap = market_cap # 单位：亿元
        # self.dcf_growth_cap = dcf_growth_cap # Removed storage from constructor arg

        # 配置项
        self.tax_rate = 0.25 # 有效税率，TODO: 未来可考虑从财报计算

        # 从环境变量加载 WACC 和 DCF Cap 参数
        try:
            self.beta = float(os.getenv('DEFAULT_BETA', '1.0'))
            self.risk_free_rate = float(os.getenv('RISK_FREE_RATE', '0.03'))
            self.market_risk_premium = float(os.getenv('MARKET_RISK_PREMIUM', '0.05'))
            self.cost_of_debt_pretax = float(os.getenv('DEFAULT_COST_OF_DEBT', '0.05'))
            # Read DCF_GROWTH_CAP from environment, default to 0.25 (25%)
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

        # 预先计算 Ke 和 WACC
        # Calculate Ke first as it's needed by WACC
        self.cost_of_equity = self.risk_free_rate + self.beta * self.market_risk_premium
        self.wacc = self.calculate_wacc() # Now self.cost_of_equity exists when this is called
        if self.wacc is None: # Corrected indentation
            print("警告：WACC 计算失败，DCF 估值可能受影响或无法进行。") # Corrected indentation
        # Ke is always calculated, useful for DDM


    def calculate_wacc(self):
        """计算加权平均资本成本 (WACC)"""
        try:
            if self.financials.empty:
                print("财务数据为空，无法计算 WACC")
                return None

            latest_finance = self.financials.iloc[0]

            # E: 股权的市场价值 (市值，从亿元转为元)
            market_cap_value = self.market_cap * 100000000
            if market_cap_value <= 0:
                print("市值非正，无法计算 WACC")
                return None

            # D: 债务的市场价值 (有息负债，单位：元)
            lt_borr = float(latest_finance.get('lt_borr', 0) or 0)
            st_borr = float(latest_finance.get('st_borr', 0) or 0)
            bond_payable = float(latest_finance.get('bond_payable', 0) or 0)
            debt_market_value = lt_borr + st_borr + bond_payable

            if debt_market_value <= 0:
                 # 如果有息负债为0或无法获取，尝试使用总负债，但给出警告
                 total_liab = float(latest_finance.get('total_liab', 0) or 0)
                 if total_liab <= 0:
                      print("警告: 无法获取有效债务数据（有息或总负债），假设债务为零计算 WACC")
                      debt_market_value = 0
                 else:
                      debt_market_value = total_liab
                      print("警告: 未找到明确的有息负债数据，使用总负债近似债务市值计算 WACC，结果可能不准确")

            # V = E + D
            total_capital = market_cap_value + debt_market_value
            if total_capital <= 0:
                 print("总资本非正，无法计算 WACC")
                 return None

            # Ke: 股权成本 (already calculated in __init__)
            cost_of_equity = self.cost_of_equity # Accesses self.cost_of_equity

            # Kd: 税后债务成本
            cost_of_debt_after_tax = self.cost_of_debt_pretax * (1 - self.tax_rate)

            # 计算 WACC
            # Handle division by zero if total_capital is somehow zero despite checks
            if total_capital == 0:
                 print("错误：总资本为零，无法计算权重。")
                 return None
            equity_weight = market_cap_value / total_capital
            debt_weight = debt_market_value / total_capital
            wacc = (equity_weight * cost_of_equity) + (debt_weight * cost_of_debt_after_tax)

            # 添加合理性检查
            if not (0 < wacc < 1):
                 print(f"警告：计算出的 WACC ({wacc:.2%}) 超出合理范围 (0% - 100%)，请检查输入参数。")
                 # 可以选择返回 None 或继续使用计算值
                 # return None

            return wacc

        except Exception as e:
            print(f"计算 WACC 时出错: {e}")
            return None

    def calculate_pe_ratio(self):
        """计算当前PE"""
        if self.financials.empty: return None
        try:
            latest_income = float(self.financials.iloc[0].get('n_income', 0) or 0)
            if latest_income <= 0: return None
            # 市值单位亿元，净利润单位元
            current_pe = (self.market_cap * 100000000) / latest_income
            return current_pe if not np.isnan(current_pe) and not np.isinf(current_pe) else None
        except Exception as e:
            print(f"计算 PE 时出错: {e}")
            return None

    def calculate_pb_ratio(self):
        """计算当前PB"""
        if self.financials.empty: return None
        try:
            latest_bps = float(self.financials.iloc[0].get('bps', 0) or 0)
            if latest_bps <= 0: return None
            current_pb = self.latest_price / latest_bps
            return current_pb if not np.isnan(current_pb) and not np.isinf(current_pb) else None
        except Exception as e:
            print(f"计算 PB 时出错: {e}")
            return None

    def calculate_growth_rate(self):
        """计算历史增长率 (YoY 和 3年CAGR)"""
        income_growth = []
        revenue_growth = []
        cagr = {}

        if len(self.financials) < 2: return income_growth, revenue_growth, cagr

        try:
            sorted_financials = self.financials.sort_values(by='year', ascending=False)
            # 计算 YoY 增长
            for i in range(len(sorted_financials) - 1):
                current_row = sorted_financials.iloc[i]
                prev_row = sorted_financials.iloc[i+1]
                # 确保年份连续
                current_year = int(current_row.get('year', 0))
                prev_year = int(prev_row.get('year', 0))
                if current_year != prev_year + 1: continue

                current_income = float(current_row.get('n_income', 0) or 0)
                prev_income = float(prev_row.get('n_income', 0) or 0)
                current_revenue = float(current_row.get('total_revenue', 0) or 0)
                prev_revenue = float(prev_row.get('total_revenue', 0) or 0)

                if prev_income != 0: # Allow calculation even if prev_income is negative
                    income_growth_rate = (current_income / prev_income - 1) * 100 if prev_income != 0 else np.inf
                    if not np.isnan(income_growth_rate) and not np.isinf(income_growth_rate):
                        income_growth.append({'year': current_year, 'rate': income_growth_rate})
                if prev_revenue > 0:
                    revenue_growth_rate = (current_revenue / prev_revenue - 1) * 100
                    if not np.isnan(revenue_growth_rate) and not np.isinf(revenue_growth_rate):
                        revenue_growth.append({'year': current_year, 'rate': revenue_growth_rate})

            # 计算3年CAGR (需要 T, T-1, T-2, T-3 四年数据)
            if len(sorted_financials) >= 4:
                latest_income = float(sorted_financials.iloc[0].get('n_income', 0) or 0)
                three_years_ago_income = float(sorted_financials.iloc[3].get('n_income', 0) or 0)
                # CAGR requires positive start and end values usually, or handle sign changes carefully
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
        """计算企业自由现金流(FCFF)和股权自由现金流(FCFE)"""
        fcff_history = []
        fcfe_history = []

        if self.financials.empty or len(self.financials) < 2:
             print("财务数据不足，无法计算 FCFF/FCFE")
             return None, None, [], [], capex_type

        sorted_financials = self.financials.sort_values(by='year', ascending=False)

        for idx, row in sorted_financials.iterrows():
            year = int(row.get('year', 0))
            if year == 0: continue

            try:
                # EBIAT (Earnings Before Interest After Taxes)
                # Use EBIT if available, otherwise estimate from Operating Profit
                ebit_indicator = float(row.get('ebit', 0) or 0)
                interest_expense = float(row.get('finan_exp', 0) or 0) # Usually negative, take absolute later if needed
                if ebit_indicator != 0:
                    ebit = ebit_indicator
                else:
                    operating_profit = float(row.get('operate_profit', 0) or 0)
                    # Estimate EBIT = Operating Profit + Interest Expense (if finan_exp is negative interest)
                    # This might not be perfectly accurate depending on finan_exp content
                    ebit = operating_profit - interest_expense # Subtracting negative interest expense adds it back
                ebiat = ebit * (1 - self.tax_rate)

                # D&A (Depreciation & Amortization)
                depreciation = float(row.get('depr_fa_coga_dpba', 0) or 0)
                amortization = float(row.get('amort_intang_assets', 0) or 0)
                da = depreciation + amortization

                # Capex (Capital Expenditures)
                capex_field = 'stot_out_inv_act' if capex_type == 'full' else 'c_pay_acq_const_fiolta'
                capital_expenditure = float(row.get(capex_field, 0) or 0)
                # Capex from cash flow statement is often negative, use absolute value
                capital_expenditure = abs(capital_expenditure)


                # Change in NWC (Net Working Capital)
                working_capital_change = 0
                current_assets = float(row.get('total_cur_assets', 0) or 0)
                current_liab = float(row.get('total_cur_liab', 0) or 0)
                # Exclude cash from current assets and short-term debt from current liabilities for NWC calc
                cash = float(row.get('money_cap', 0) or 0)
                st_debt = float(row.get('st_borr', 0) or 0)
                current_nwc = (current_assets - cash) - (current_liab - st_debt)

                prev_year_index = idx + 1
                if prev_year_index < len(sorted_financials):
                    prev_row = sorted_financials.iloc[prev_year_index]
                    if int(prev_row.get('year', 0)) == year - 1:
                        prev_assets = float(prev_row.get('total_cur_assets', 0) or 0)
                        prev_liab = float(prev_row.get('total_cur_liab', 0) or 0)
                        prev_cash = float(prev_row.get('money_cap', 0) or 0)
                        prev_st_debt = float(prev_row.get('st_borr', 0) or 0)
                        prev_nwc = (prev_assets - prev_cash) - (prev_liab - prev_st_debt)
                        working_capital_change = current_nwc - prev_nwc

                # FCFF = EBIAT + D&A - Capex - Change in NWC
                fcff = ebiat + da - capital_expenditure - working_capital_change

                # FCFE = FCFF - Interest Expense * (1 - Tax Rate) + Net Debt Issued
                # Net Debt Issued = Cash from borrowing - Cash paid for debt
                cash_recp_borrow = float(row.get('c_recp_borrow', 0) or 0)
                cash_prepay_amt_borr = float(row.get('c_prepay_amt_borr', 0) or 0)
                net_debt_increase = cash_recp_borrow - cash_prepay_amt_borr
                # Interest expense should be positive for this formula
                interest_paid_after_tax = abs(interest_expense) * (1 - self.tax_rate)

                fcfe = fcff - interest_paid_after_tax + net_debt_increase

                fcff_history.append({'year': year, 'value': fcff})
                fcfe_history.append({'year': year, 'value': fcfe})

            except Exception as e:
                 print(f"计算 {year} 年 FCFF/FCFE ({capex_type} capex) 时出错: {e}")
                 fcff_history.append({'year': year, 'value': None})
                 fcfe_history.append({'year': year, 'value': None})

        latest_fcff = next((item['value'] for item in fcff_history if item['value'] is not None), None)
        latest_fcfe = next((item['value'] for item in fcfe_history if item['value'] is not None), None)

        # DEBUG: Print latest FCFE for basic capex (Removed)
        if capex_type == 'basic':
            # Also print components for the latest year if available
            if fcff_history and fcfe_history:
                 latest_year_data = sorted_financials.iloc[0]
                 latest_year = int(latest_year_data.get('year', 0))
                 latest_fcff_calc = next((item['value'] for item in fcff_history if item['year'] == latest_year), None)
                 latest_fcfe_calc = next((item['value'] for item in fcfe_history if item['year'] == latest_year), None)
                 # Find components used for this year's calculation (requires re-calculation or storing them)
                 # Simplified: just print the final values for now


        # Return the history specific to the capex type requested
        if capex_type == 'basic':
             return latest_fcff, latest_fcfe, fcff_history, fcfe_history, capex_type
        else: # full
             # Need to recalculate or store separately if needed, for now returning same history
             # This assumes the loop correctly calculated based on capex_type
             return latest_fcff, latest_fcfe, fcff_history, fcfe_history, capex_type


    def calculate_ev(self):
        """计算企业价值(EV)和EV/EBITDA倍数"""
        try:
            if self.financials.empty: return None, None, None
            latest_finance = self.financials.iloc[0]

            # EV = Market Cap + Total Debt - Cash & Cash Equivalents
            market_cap_value = self.market_cap * 100000000 # Convert billions to Yuan

            # Total Debt = Long Term Borrowings + Short Term Borrowings + Bonds Payable
            lt_borr = float(latest_finance.get('lt_borr', 0) or 0)
            st_borr = float(latest_finance.get('st_borr', 0) or 0)
            bond_payable = float(latest_finance.get('bond_payable', 0) or 0)
            total_debt = lt_borr + st_borr + bond_payable

            # Cash & Cash Equivalents
            money_cap = float(latest_finance.get('money_cap', 0) or 0)
            cash_equivalents = money_cap if money_cap > 0 else 0
            if cash_equivalents == 0: print("警告: 未能获取有效的货币资金(money_cap)，计算EV时假设现金等价物为0。")

            enterprise_value = market_cap_value + total_debt - cash_equivalents

            # EBITDA
            ebitda_indicator = float(latest_finance.get('ebitda', 0) or 0)
            if ebitda_indicator != 0:
                ebitda = ebitda_indicator
            else:
                # Estimate EBITDA = EBIT + D&A
                ebit_indicator = float(latest_finance.get('ebit', 0) or 0)
                interest_expense = float(latest_finance.get('finan_exp', 0) or 0)
                if ebit_indicator != 0:
                    ebit = ebit_indicator
                else:
                    operating_profit = float(latest_finance.get('operate_profit', 0) or 0)
                    ebit = operating_profit - interest_expense # Estimate EBIT

                depreciation = float(latest_finance.get('depr_fa_coga_dpba', 0) or 0)
                amortization = float(latest_finance.get('amort_intang_assets', 0) or 0)
                da = depreciation + amortization
                ebitda = ebit + da
                print("警告: 未找到直接的 EBITDA 数据，使用 EBIT + D&A 估算。")


            # EV/EBITDA
            ev_to_ebitda = None
            if ebitda is not None and ebitda != 0 and enterprise_value is not None: # Allow negative EBITDA? Check convention. Usually positive.
                ev_to_ebitda = enterprise_value / ebitda
                if np.isnan(ev_to_ebitda) or np.isinf(ev_to_ebitda): ev_to_ebitda = None
            elif ebitda is not None and ebitda == 0: print("EBITDA为零，无法计算 EV/EBITDA")

            return enterprise_value, ebitda, ev_to_ebitda
        except Exception as e:
            print(f"计算 EV/EBITDA 时出错: {e}")
            return None, None, None

    def calculate_dividend_yield(self):
        """计算股息率和历史分红"""
        current_yield, dividend_history, avg_div, payout_ratio = 0, [], 0, 0
        if self.dividends.empty: return current_yield, dividend_history, avg_div, payout_ratio

        try:
            sorted_dividends = self.dividends.sort_values(by='year', ascending=False)
            latest_div_row = sorted_dividends.iloc[0]
            latest_div_per_share = float(latest_div_row.get('cash_div_tax', 0) or 0)

            if self.latest_price > 0 and latest_div_per_share > 0:
                current_yield = (latest_div_per_share / self.latest_price) * 100

            for _, row in sorted_dividends.iterrows():
                year = int(row.get('year', 0))
                div_per_share = float(row.get('cash_div_tax', 0) or 0)
                if year > 0 and div_per_share > 0:
                    dividend_history.append({'year': year, 'dividend_per_share': div_per_share})

            if len(dividend_history) >= 3:
                recent_dividends = [d['dividend_per_share'] for d in dividend_history[:3]]
                if recent_dividends: avg_div = sum(recent_dividends) / len(recent_dividends)

            if not self.financials.empty:
                latest_income = float(self.financials.iloc[0].get('n_income', 0) or 0)
                # Ensure total_shares is actual number of shares
                if latest_income > 0 and latest_div_per_share > 0 and self.total_shares > 0:
                    total_dividend = latest_div_per_share * self.total_shares # total_shares is already actual count
                    payout_ratio = (total_dividend / latest_income) * 100
        except Exception as e:
            print(f"计算股息率时出错: {e}")

        return current_yield, dividend_history, avg_div, payout_ratio

    def _get_growth_rates_for_dcf(self, history_values):
        """辅助函数：根据历史数据计算DCF增长率列表"""
        avg_growth = 0
        if len(history_values) >= 4: # Need at least 4 points for 3 growth periods
            growths = []
            # Ensure history is sorted correctly (newest first)
            sorted_history = sorted([h for h in history_values if h['value'] is not None], key=lambda x: x['year'], reverse=True)
            if len(sorted_history) >= 4:
                for i in range(3): # Calculate growth for last 3 periods
                     # Check for consecutive years
                     if sorted_history[i]['year'] == sorted_history[i+1]['year'] + 1:
                         curr = sorted_history[i]['value']
                         prev = sorted_history[i+1]['value']
                         if prev is not None and curr is not None and prev != 0:
                             growth = (curr - prev) / abs(prev)
                             # 限制单年增长率在合理范围，如 -100% 到 +200%
                             if -1 <= growth <= 2:
                                 growths.append(growth)
                if growths: # This 'if' should align with the 'for i in range(3)' loop
                    avg_growth = sum(growths) / len(growths)
                # These prints should align with the 'if len(sorted_history) >= 4:' block
                # DEBUG print removed
                # DEBUG print removed
                # DEBUG print removed # Corrected indentation

        # --- 应用增长率上限限制 (从环境变量读取) ---
        # reasonable_growth_cap is now self.dcf_growth_cap read from env in __init__
        if avg_growth > self.dcf_growth_cap:
            print(f"警告: 计算出的平均增长率 ({avg_growth:.2%}) 过高，已限制为 {self.dcf_growth_cap:.0%}")
            avg_growth = self.dcf_growth_cap
        # --- 结束应用 ---

        # Define growth rate sensitivity based on the potentially capped average historical growth
        if avg_growth > 0.01:
            low_g = max(0, avg_growth * 0.8)  # Base low on (capped) avg
            mid_g = avg_growth               # Base mid on (capped) avg
            # Still cap the high end derived from the (capped) avg, but ensure it's at least the mid_g
            high_g = max(mid_g, min(0.3, avg_growth * 1.2)) # Ensure high >= mid, cap at 30%
            # Ensure rates are distinct and ordered reasonably, handle potential float issues
            growth_rates = sorted(list(set([round(low_g, 4), round(mid_g, 4), round(high_g, 4)])))
            # If capping resulted in fewer than 3 distinct rates, adjust slightly
            if len(growth_rates) < 3:
                 if len(growth_rates) == 2:
                      # Add a point slightly above the higher rate, capped at 0.3
                      growth_rates.append(min(0.3, round(growth_rates[1] + 0.01, 4)))
                 elif len(growth_rates) == 1:
                      # Add points slightly below and above, capped
                      rate = growth_rates[0]
                      growth_rates = [max(0, round(rate - 0.01, 4)), rate, min(0.3, round(rate + 0.01, 4))]
                 growth_rates = sorted(list(set(growth_rates)))[:3] # Ensure 3 rates max

        else: # Use default rates if history is flat, negative, or insufficient
            growth_rates = [0.01, 0.03, 0.05]

        # DEBUG print removed
        return growth_rates

    def _perform_dcf_valuation(self, latest_fcf, fcf_history, growth_rates, discount_rates, is_fcff=False):
        """通用的两阶段DCF估值逻辑"""
        if latest_fcf is None or latest_fcf <= 0:
            return None, "自由现金流为负、零或计算失败"

        # 确定增长率
        if growth_rates is None:
            growth_rates = self._get_growth_rates_for_dcf(fcf_history)
            # DEBUG print removed
        else:
            # Ensure provided rates are floats
            growth_rates = [float(g) for g in growth_rates]

        # 确定折现率
        if discount_rates is None:
            # Use WACC for FCFF, Ke for FCFE by default
            base_rate = self.wacc if is_fcff else self.cost_of_equity
            if base_rate is None:
                 error_msg = "WACC 计算失败，无法进行 FCFF 估值" if is_fcff else "股权成本(Ke) 计算失败，无法进行 FCFE 估值"
                 return None, error_msg
            # Sensitivity analysis around the base rate
            discount_rates = [max(0.01, base_rate - 0.01), base_rate, base_rate + 0.01]
        else:
             discount_rates = [float(r) for r in discount_rates]

        # DEBUG print removed
        # DEBUG print removed

        valuations = []
        for g in growth_rates:
            for r in discount_rates:
                # 确定永续增长率 (Terminal Growth Rate) - capped by risk-free rate and discount rate
                terminal_growth = min(g * 0.5, r * 0.8, self.risk_free_rate)
                # Ensure terminal growth is strictly less than discount rate
                if terminal_growth >= r:
                    print(f"警告: DCF 永续增长率({terminal_growth:.2%}) >= 折现率({r:.2%})，跳过组合 g={g:.2%}, r={r:.2%}")
                    continue

                try:
                    present_value_fcf = 0
                    # 第一阶段: 5年高增长期 (Year 1 to 5)
                    for year in range(1, 6):
                        fcf = latest_fcf * (1 + g) ** year
                        present_value_fcf += fcf / ((1 + r) ** year)

                    # 第二阶段: 永续增长 (Terminal Value)
                    terminal_fcf_year6 = latest_fcf * (1 + g) ** 5 * (1 + terminal_growth)
                    # Terminal value at the end of Year 5
                    terminal_value_at_year5 = terminal_fcf_year6 / (r - terminal_growth)
                    # Present value of terminal value
                    terminal_value_present = terminal_value_at_year5 / (1 + r) ** 5

                    total_value_enterprise_or_equity = present_value_fcf + terminal_value_present

                    value_per_share = None
                    if is_fcff:
                        # FCFF -> Enterprise Value -> Equity Value -> Value Per Share
                        if not self.financials.empty:
                            latest_finance = self.financials.iloc[0]
                            # Net Debt = Total Debt - Cash
                            lt_borr = float(latest_finance.get('lt_borr', 0) or 0)
                            st_borr = float(latest_finance.get('st_borr', 0) or 0)
                            bond_payable = float(latest_finance.get('bond_payable', 0) or 0)
                            total_debt = lt_borr + st_borr + bond_payable
                            money_cap = float(latest_finance.get('money_cap', 0) or 0)
                            net_debt = total_debt - money_cap

                            total_equity_value = total_value_enterprise_or_equity - net_debt
                            if self.total_shares > 0:
                                value_per_share = total_equity_value / self.total_shares
                            else: print("总股本非正，无法计算FCFF的每股价值")
                        else: print("财务数据为空，无法计算FCFF的净债务")
                    else: # FCFE -> Equity Value -> Value Per Share
                        if self.total_shares > 0:
                            value_per_share = total_value_enterprise_or_equity / self.total_shares
                        else: print("总股本非正，无法计算FCFE的每股价值")

                    premium = None
                    if value_per_share is not None and self.latest_price > 0:
                        premium = (value_per_share / self.latest_price - 1) * 100 # Correct premium calc

                    # 存储结果，即使 value_per_share 为 None
                    valuations.append({
                        'growth_rate': g,
                        'discount_rate': r,
                        'value': value_per_share,
                        'premium': premium
                    })
                except OverflowError:
                     print(f"DCF 计算溢出错误，跳过组合 g={g:.2%}, r={r:.2%}")
                except ZeroDivisionError:
                     # This happens if r equals terminal_growth
                     print(f"DCF 除零错误 (r={r:.2%}, g_terminal={terminal_growth:.2%})，跳过组合 g={g:.2%}, r={r:.2%}")

        return valuations, None

    def calculate_ddm_valuation(self, growth_rates=None, discount_rates=None):
        """股利贴现模型(DDM)估值"""
        current_yield, div_history, avg_div, _ = self.calculate_dividend_yield()

        if avg_div <= 0:
            return None, "无有效平均分红数据，无法进行DDM估值"

        # 确定增长率
        if growth_rates is None:
             avg_growth = 0
             if len(div_history) >= 4: # Need 4 points for 3 growth periods
                 growths = []
                 sorted_history = sorted([h for h in div_history if h['dividend_per_share'] is not None], key=lambda x: x['year'], reverse=True)
                 if len(sorted_history) >= 4:
                     for i in range(3): # Last 3 growth periods
                         if sorted_history[i]['year'] == sorted_history[i+1]['year'] + 1:
                             prev = sorted_history[i+1]['dividend_per_share']
                             curr = sorted_history[i]['dividend_per_share']
                             if prev is not None and curr is not None and prev != 0:
                                 growth = (curr - prev) / abs(prev)
                                 if -1 <= growth <= 2: # 限制增长率范围
                                     growths.append(growth)
                 if growths: avg_growth = sum(growths) / len(growths)

             # Define growth rate sensitivity based on average historical growth
             if avg_growth > 0.01:
                 low_g = max(0, avg_growth * 0.8)
                 mid_g = avg_growth
                 high_g = min(0.3, avg_growth * 1.2) # Cap high growth
                 growth_rates = [low_g, mid_g, high_g]
             else: # Use default rates if history is flat, negative, or insufficient
                 growth_rates = [0.01, 0.03, 0.05]
        else:
             growth_rates = [float(g) for g in growth_rates]

        # 确定折现率 (DDM 通常用 Ke)
        if discount_rates is None:
            if self.cost_of_equity is None:
                 return None, "无法计算股权成本(Ke)，无法进行DDM估值"
            # Sensitivity analysis around Ke
            discount_rates = [max(0.01, self.cost_of_equity - 0.01), self.cost_of_equity, self.cost_of_equity + 0.01]
        else:
             discount_rates = [float(r) for r in discount_rates]

        valuations = []
        for g in growth_rates:
            for r in discount_rates:
                # 确定永续增长率
                terminal_growth = min(g * 0.5, r * 0.8, self.risk_free_rate)
                if terminal_growth >= r:
                    print(f"警告: DDM 永续增长率({terminal_growth:.2%}) >= 折现率({r:.2%})，跳过组合 g={g:.2%}, r={r:.2%}")
                    continue

                try:
                    present_value_dividends = 0
                    # 第一阶段: 5年高增长期
                    # Use latest dividend as base if avg_div is problematic? Or stick to avg? Stick to avg for now.
                    base_dividend = avg_div
                    for year in range(1, 6):
                        dividend = base_dividend * (1 + g) ** year
                        present_value_dividends += dividend / ((1 + r) ** year)

                    # 第二阶段: 永续增长
                    terminal_dividend_year6 = base_dividend * (1 + g) ** 5 * (1 + terminal_growth)
                    if r - terminal_growth <= 1e-9: # Avoid division by zero or near-zero
                         print(f"警告: DDM 折现率({r:.2%}) 接近或小于等于永续增长率({terminal_growth:.2%})，无法计算终值，跳过组合 g={g:.2%}, r={r:.2%}")
                         continue
                    terminal_value_at_year5 = terminal_dividend_year6 / (r - terminal_growth)
                    terminal_value_present = terminal_value_at_year5 / (1 + r) ** 5

                    total_value_per_share = present_value_dividends + terminal_value_present # DDM直接得到每股价值

                    premium = None
                    if self.latest_price > 0:
                         premium = (total_value_per_share / self.latest_price - 1) * 100 # Correct premium calc

                    valuations.append({
                        'growth_rate': g,
                        'discount_rate': r,
                        'value': total_value_per_share,
                        'premium': premium
                    })
                except OverflowError:
                     print(f"DDM 计算溢出错误，跳过组合 g={g:.2%}, r={r:.2%}")
                except ZeroDivisionError:
                     print(f"DDM 除零错误 (r={r:.2%}, g_terminal={terminal_growth:.2%})，跳过组合 g={g:.2%}, r={r:.2%}")

        return valuations, None

    # --- DCF 方法重构 ---

    def perform_fcff_valuation_basic_capex(self, growth_rates=None, discount_rates=None):
        """基于基本资本性支出FCFF的DCF估值"""
        latest_fcff, _, fcff_history, _, _ = self.calculate_fcff_fcfe(capex_type='basic')
        # Pass the correct history
        return self._perform_dcf_valuation(latest_fcff, fcff_history, growth_rates, discount_rates, is_fcff=True)

    def perform_fcfe_valuation_basic_capex(self, growth_rates=None, discount_rates=None):
        """基于基本资本性支出FCFE的DCF估值"""
        _, latest_fcfe, _, fcfe_history, _ = self.calculate_fcff_fcfe(capex_type='basic')
        # Pass the correct history
        return self._perform_dcf_valuation(latest_fcfe, fcfe_history, growth_rates, discount_rates, is_fcff=False)

    def perform_fcfe_valuation_full_capex(self, growth_rates=None, discount_rates=None):
        """基于完整资本性支出FCFE的DCF估值"""
        _, latest_fcfe, _, fcfe_history, _ = self.calculate_fcff_fcfe(capex_type='full')
         # Need to ensure calculate_fcff_fcfe returns the correct history based on type
        # Assuming it does for now, or recalculate if necessary
        return self._perform_dcf_valuation(latest_fcfe, fcfe_history, growth_rates, discount_rates, is_fcff=False)

    def perform_fcff_valuation_full_capex(self, growth_rates=None, discount_rates=None):
        """基于完整资本性支出FCFF的DCF估值"""
        latest_fcff, _, fcff_history, _, _ = self.calculate_fcff_fcfe(capex_type='full')
        # Need to ensure calculate_fcff_fcfe returns the correct history based on type
        # Assuming it does for now, or recalculate if necessary
        return self._perform_dcf_valuation(latest_fcff, fcff_history, growth_rates, discount_rates, is_fcff=True)

    # --- 其他分析和综合分析 ---

    def get_other_analysis(self):
        """计算其他分析指标：股息和增长"""
        analysis = {
            'dividend_analysis': None,
            'growth_analysis': None
        }
        try:
            # 股息分析
            current_yield, _, avg_div, payout_ratio = self.calculate_dividend_yield()
            analysis['dividend_analysis'] = {
                'current_yield_pct': current_yield,
                'avg_dividend_3y': avg_div,
                'payout_ratio_pct': payout_ratio
            }

            # 增长分析
            _, _, cagr = self.calculate_growth_rate()
            analysis['growth_analysis'] = {
                'net_income_cagr_3y': cagr.get('income_3y'),
                'revenue_cagr_3y': cagr.get('revenue_3y')
            }
        except Exception as e:
            print(f"计算其他分析时出错: {e}")

        return analysis

    def get_combo_valuations(self, pe_multiples, pb_multiples, ev_ebitda_multiples, growth_rates=None, discount_rates=None):
        """计算新的绝对估值组合（包含安全边际）及投资建议"""
        combos_with_margin = {} # Store results as {'Alias': {'value': float, 'safety_margin_pct': float}} or None
        investment_advice = {}
        try:
            # --- 计算核心绝对/DDM估值模型结果 ---
            dcf_fcff_basic_results, _ = self.perform_fcff_valuation_basic_capex(growth_rates, None)
            dcf_fcfe_basic_results, _ = self.perform_fcfe_valuation_basic_capex(growth_rates, None)
            dcf_fcff_full_results, _ = self.perform_fcff_valuation_full_capex(growth_rates, None)
            dcf_fcfe_full_results, _ = self.perform_fcfe_valuation_full_capex(growth_rates, None)
            ddm_results, _ = self.calculate_ddm_valuation(growth_rates, None)

            # --- 提取各模型中心值 ---
            def extract_central_value(results):
                if not results: return None
                valid_values = [r['value'] for r in results if r and r.get('value') is not None and not np.isnan(r['value'])]
                if not valid_values: return None
                return sum(valid_values) / len(valid_values)

            val_dcf_ff_b = extract_central_value(dcf_fcff_basic_results or [])
            val_dcf_fe_b = extract_central_value(dcf_fcfe_basic_results or [])
            val_dcf_ff_f = extract_central_value(dcf_fcff_full_results or [])
            val_dcf_fe_f = extract_central_value(dcf_fcfe_full_results or [])
            val_ddm = extract_central_value(ddm_results or [])

            # --- Helper to calculate safety margin ---
            def calculate_safety_margin_pct(value, price):
                if value is not None and not np.isnan(value) and price > 0:
                    return (value / price - 1) * 100
                return None

            # --- 计算新的绝对估值组合及其安全边际 ---
            def safe_avg(*args):
                valid_args = [arg for arg in args if arg is not None and not np.isnan(arg)]
                return sum(valid_args) / len(valid_args) if valid_args else None

            # Calculate combo values first
            combo_values = {
                'FCFE_Basic': val_dcf_fe_b,
                'DDM': val_ddm,
                'FCFE_Full': val_dcf_fe_f,
                'Avg_FCF_Basic': safe_avg(val_dcf_ff_b, val_dcf_fe_b),
                'Avg_FCFE_Basic_DDM': safe_avg(val_dcf_fe_b, val_ddm),
                'Avg_FCFF_Basic_DDM': safe_avg(val_dcf_ff_b, val_ddm),
                'Avg_FCF_Full': safe_avg(val_dcf_ff_f, val_dcf_fe_f),
                'Avg_FCFE_Full_DDM': safe_avg(val_dcf_fe_f, val_ddm),
                'Avg_FCFF_Full_DDM': safe_avg(val_dcf_ff_f, val_ddm),
                'Avg_All_Absolute_DDM': safe_avg(val_dcf_ff_b, val_dcf_fe_b, val_dcf_ff_f, val_dcf_fe_f, val_ddm)
            }

            # Calculate composite valuation based on combo_values
            val_x = combo_values.get('FCFE_Basic')
            other_combo_keys = [k for k in combo_values if k != 'FCFE_Basic'] # Exclude X itself
            valid_other_combo_values = [v for k, v in combo_values.items() if k in other_combo_keys and v is not None and not np.isnan(v)]
            num_valid_others = len(valid_other_combo_values)
            sum_valid_others = sum(valid_other_combo_values)

            composite_valuation_value = None
            if val_x is not None and not np.isnan(val_x):
                if num_valid_others > 0:
                    other_avg = sum_valid_others / num_valid_others
                    composite_valuation_value = val_x * 0.4 + other_avg * 0.6
                else:
                    composite_valuation_value = val_x
            elif num_valid_others > 0:
                composite_valuation_value = sum_valid_others / num_valid_others

            combo_values['Composite_Valuation'] = composite_valuation_value

            # Now populate combos_with_margin including safety margin
            for key, value in combo_values.items():
                if value is not None and not np.isnan(value):
                    margin = calculate_safety_margin_pct(value, self.latest_price)
                    combos_with_margin[key] = {'value': value, 'safety_margin_pct': margin}
                else:
                    combos_with_margin[key] = None # Keep combo as None if value is None

            # --- 生成投资建议 (基于安全边际和关键组合) ---
            advice_base_results = (dcf_fcfe_basic_results or []) + (ddm_results or [])
            valid_advice_base_values = [r['value'] for r in advice_base_results if r and r.get('value') is not None and not np.isnan(r['value'])]
            min_intrinsic_value_for_advice = min(valid_advice_base_values) if valid_advice_base_values else None
            avg_intrinsic_value_for_advice = safe_avg(*valid_advice_base_values)
            max_intrinsic_value_for_advice = max(valid_advice_base_values) if valid_advice_base_values else None

            safety_margin_advice = calculate_safety_margin_pct(min_intrinsic_value_for_advice, self.latest_price) # Use the specific margin for advice

            advice = "无法评估"
            reason = "缺乏足够的有效估值结果来生成建议。"
            if safety_margin_advice is not None:
                strong_buy_margin = 40 # Percentage
                buy_margin = 20        # Percentage
                sell_threshold_avg_factor = 1.2
                strong_sell_threshold_max_factor = 1.5

                if safety_margin_advice > strong_buy_margin:
                    advice = "强烈买入"
                    reason = f"当前价格({self.latest_price:.2f})显著低于基于FCFE(基本)和DDM估算的保守内在价值下限({min_intrinsic_value_for_advice:.2f})，提供了超过 {strong_buy_margin:.0f}% 的安全边际。"
                elif safety_margin_advice > buy_margin:
                    advice = "买入"
                    reason = f"当前价格({self.latest_price:.2f})低于基于FCFE(基本)和DDM估算的保守内在价值下限({min_intrinsic_value_for_advice:.2f})，提供了约 {buy_margin:.0f}% 的安全边际。"
                elif max_intrinsic_value_for_advice is not None and self.latest_price > max_intrinsic_value_for_advice * strong_sell_threshold_max_factor:
                     advice = "强烈卖出"
                     reason = f"当前价格({self.latest_price:.2f})显著高于基于FCFE(基本)和DDM估算的内在价值上限({max_intrinsic_value_for_advice:.2f})，估值过高风险极大。"
                elif avg_intrinsic_value_for_advice is not None and self.latest_price > avg_intrinsic_value_for_advice * sell_threshold_avg_factor:
                    advice = "卖出"
                    reason = f"当前价格({self.latest_price:.2f})高于基于FCFE(基本)和DDM估算的内在价值平均值({avg_intrinsic_value_for_advice:.2f})超过 {int((sell_threshold_avg_factor-1)*100)}%，可能估值偏高。"
                else:
                    advice = "持有/观察"
                    reason = f"当前价格({self.latest_price:.2f})处于基于FCFE(基本)和DDM估算的内在价值区间内({min_intrinsic_value_for_advice:.2f}-{max_intrinsic_value_for_advice:.2f})，安全边际 ({safety_margin_advice:.1f}%) 不显著。"

                # Safely access combo values for reason string
                fcfe_basic_val_str = f"{combos_with_margin.get('FCFE_Basic', {}).get('value', 'N/A'):.2f}" if combos_with_margin.get('FCFE_Basic') else 'N/A'
                avg_fe_b_ddm_val_str = f"{combos_with_margin.get('Avg_FCFE_Basic_DDM', {}).get('value', 'N/A'):.2f}" if combos_with_margin.get('Avg_FCFE_Basic_DDM') else 'N/A'
                composite_val_str = f"{combos_with_margin.get('Composite_Valuation', {}).get('value', 'N/A'):.2f}" if combos_with_margin.get('Composite_Valuation') else 'N/A'
                reason += f" 参考估值点：FCFE(基本)={fcfe_basic_val_str}；FCFE(基本)+DDM={avg_fe_b_ddm_val_str}；综合估值={composite_val_str}。"

            investment_advice = {
                'based_on': "安全边际 (基于 FCFE Basic & DDM), 综合估值, FCFE_Basic, Avg_FCFE_Basic_DDM",
                'advice': advice,
                'reason': reason,
                'min_intrinsic_value': min_intrinsic_value_for_advice,
                'avg_intrinsic_value': avg_intrinsic_value_for_advice,
                'max_intrinsic_value': max_intrinsic_value_for_advice,
                'safety_margin_pct': safety_margin_advice # Use the specific margin calculated for advice
            }

            # --- 添加参考信息 ---
            reference = []
            def get_range_str(results, name):
                 vals = [r['value'] for r in results if r and r.get('value') is not None and not np.isnan(r['value'])]
                 if vals: return f"{name} 估值范围: {min(vals):.2f}-{max(vals):.2f}"
                 return None

            ddm_ref = get_range_str(ddm_results or [], "DDM")
            dcf_basic_ref = get_range_str((dcf_fcff_basic_results or []) + (dcf_fcfe_basic_results or []), "DCF(Basic Capex)")
            dcf_full_ref = get_range_str((dcf_fcff_full_results or []) + (dcf_fcfe_full_results or []), "DCF(Full Capex)")

            current_pe = self.calculate_pe_ratio()
            current_pb = self.calculate_pb_ratio()
            if current_pe is not None: reference.append(f"当前 PE: {current_pe:.2f}")
            if current_pb is not None: reference.append(f"当前 PB: {current_pb:.2f}")

            if ddm_ref: reference.append(ddm_ref)
            if dcf_basic_ref: reference.append(dcf_basic_ref)
            if dcf_full_ref: reference.append(dcf_full_ref)

            investment_advice['reference_info'] = "；".join(reference) + "。相对估值指标和绝对估值模型可结合市场情绪和公司基本面进行参考。"

            return combos_with_margin, investment_advice

        except Exception as e:
            print(f"计算综合估值和建议时发生严重错误: {e}\n{traceback.format_exc()}")
            return {}, {} # Return empty dicts on error

# End of class ValuationCalculator
