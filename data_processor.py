import pandas as pd
import numpy as np # 新增导入
from typing import Dict, Tuple, Union

# 假设从 data_fetcher.py 获取的数据是 pandas DataFrame 的字典
# 例如: {'balance_sheet': df_balance_sheet, 'income_statement': df_income_statement, ...}

class DataProcessor:
    def __init__(self, historical_data: Dict[str, pd.DataFrame]):
        self.historical_data = historical_data
        self.processed_data = {}
        self.historical_ratios = {}

    def clean_data(self):
        """
        任务 1.1: 强化历史数据清洗逻辑
        - 处理异常值 (例如，基于统计方法识别并修正或标记)
        - 处理缺失值 (例如，填充、插值或标记)
        """
        print("Starting data cleaning...")
        key_financial_items = {
            'income_statement': ['total_revenue', 'revenue', 'oper_cost', 'sell_exp', 'admin_exp', 'rd_exp', 'income_tax', 'total_profit'],
            'balance_sheet': ['accounts_receiv_bill', 'inventories', 'accounts_pay', 'prepayment', 'oth_cur_assets', 'contract_liab', 'adv_receipts', 'payroll_payable', 'taxes_payable', 'oth_payable', 'total_cur_assets', 'total_cur_liab'],
            'cash_flow': ['depr_fa_coga_dpba', 'amort_intang_assets', 'lt_amort_deferred_exp', 'c_pay_acq_const_fiolta', 'c_paid_goods_s']
        }

        for table_name, df_original in self.historical_data.items():
            df = df_original.copy()
            print(f"Cleaning table: {table_name}")

            # 确保日期列是 datetime 类型并排序
            if 'end_date' in df.columns:
                try:
                    df['end_date'] = pd.to_datetime(df['end_date'])
                    df = df.sort_values(by='end_date')
                except Exception as e:
                    print(f"Warning: Could not convert 'end_date' to datetime or sort in {table_name}: {e}")
            
            numeric_cols = df.select_dtypes(include=['number']).columns
            
            for col in numeric_cols:
                print(f"  Processing column: {col}")
                # 1. 异常值检测与处理 (替换为 NaN)
                # 仅对有足够非空值的列进行异常值检测
                if df[col].notna().sum() >= 4: # 修改条件为 >= 4
                    q1 = df[col].quantile(0.25)
                    q3 = df[col].quantile(0.75)
                    iqr = q3 - q1
                    lower_bound = q1 - 1.5 * iqr
                    upper_bound = q3 + 1.5 * iqr
                    
                    outliers = df[(df[col] < lower_bound) | (df[col] > upper_bound)]
                    if not outliers.empty:
                        print(f"    Potential outliers detected in {col} at indices: {outliers.index.tolist()}. Values: {outliers[col].tolist()}")
                        df.loc[(df[col] < lower_bound) | (df[col] > upper_bound), col] = np.nan
                        print(f"    Replaced {len(outliers)} outliers in {col} with NaN.")
                
                # 2. 缺失值处理
                if df[col].isnull().any():
                    print(f"    Handling NaNs in column: {col}")
                    original_nan_count = df[col].isnull().sum()

                    # 策略1: 对关键财务项目尝试线性插值 (需要至少两个非NaN值)
                    if table_name in key_financial_items and col in key_financial_items[table_name] and df[col].notna().sum() >= 2:
                        try:
                            # 使用 limit_direction='both' 尝试填充两端
                            df[col] = df[col].interpolate(method='linear', limit_direction='both', limit_area='inside') # limit_area='inside' 避免填充首尾的NaN
                            interpolated_count = original_nan_count - df[col].isnull().sum()
                            if interpolated_count > 0:
                                print(f"      Applied linear interpolation to {col}, filled {interpolated_count} NaNs.")
                        except Exception as e:
                            print(f"      Error during interpolation for {col}: {e}")
                    
                    # 策略2: 对于首尾的NaN（如果插值未填充）或非关键列的NaN，或插值后仍存在的NaN，使用前向/后向填充
                    if df[col].isnull().any():
                        filled_ffill = df[col].ffill()
                        if not df[col].equals(filled_ffill):
                             df[col] = filled_ffill
                             print(f"      Applied ffill for {col}.")
                        
                        filled_bfill = df[col].bfill()
                        if not df[col].equals(filled_bfill):
                             df[col] = filled_bfill
                             print(f"      Applied bfill for {col}.")

                    # 策略3: 对剩余的NaN (插值和ffill/bfill无效)，使用0填充 (需要谨慎评估)
                    if df[col].isnull().any():
                        remaining_nan_count = df[col].isnull().sum()
                        print(f"      Filling {remaining_nan_count} remaining NaNs in {col} with 0 (Review Recommended).")
                        df[col] = df[col].fillna(0)
            
            self.processed_data[table_name] = df

        print("Data cleaning completed.")
        return self.processed_data

    def calculate_historical_ratios_and_turnovers(self) -> Dict[str, any]:
        """
        任务 1.2: 精确计算历史财务比率和周转天数
        根据 PRD 6.1 历史数据处理部分
        """
        if not self.processed_data:
            print("Error: Data not cleaned yet. Call clean_data() first.")
            return {}

        bs_df = self.processed_data.get('balance_sheet')
        is_df = self.processed_data.get('income_statement')
        cf_df = self.processed_data.get('cash_flow')

        if bs_df is None or is_df is None or cf_df is None:
            print("Error: Missing required dataframes (balance_sheet, income_statement, cash_flow).")
            return {}

        # 确保按报告期排序
        bs_df = bs_df.sort_values(by='end_date')
        is_df = is_df.sort_values(by='end_date')
        cf_df = cf_df.sort_values(by='end_date')

        # 销货成本占销售额比率 = oper_cost / total_revenue
        self.historical_ratios['cogs_to_revenue_ratio'] = \
            (is_df['oper_cost'] / is_df['total_revenue'].replace(0, np.nan)).mean() 

        # 销售/管理/研发费用占销售额比率 = (sell_exp + admin_exp + rd_exp) / total_revenue
        # 使用 .get(col, 0) 处理可能不存在的列
        sga_rd_exp = (is_df.get('sell_exp', 0) + 
                      is_df.get('admin_exp', 0) + 
                      is_df.get('rd_exp', 0))
        # 确保 sga_rd_exp 是 Series 或数值，如果列不存在，get 返回 0
        if isinstance(sga_rd_exp, (int, float)) and sga_rd_exp == 0 and not ('sell_exp' in is_df or 'admin_exp' in is_df or 'rd_exp' in is_df):
             self.historical_ratios['sga_rd_to_revenue_ratio'] = 0 # 如果所有列都不存在，比率为0
        else:
             self.historical_ratios['sga_rd_to_revenue_ratio'] = \
                 (sga_rd_exp / is_df['total_revenue'].replace(0, np.nan)).mean()

        if 'depreciation_and_amortization' in is_df.columns:
            total_da = is_df.get('depreciation_and_amortization', pd.Series([0] * len(is_df), index=is_df.index))
        elif all(c in cf_df.columns for c in ['depr_fa_coga_dpba', 'amort_intang_assets', 'lt_amort_deferred_exp']):
            # 使用 .get 获取列，如果不存在则返回 Series of zeros
            depr = cf_df.set_index('end_date').get('depr_fa_coga_dpba', pd.Series(0, index=cf_df.set_index('end_date').index))
            amort_intan = cf_df.set_index('end_date').get('amort_intang_assets', pd.Series(0, index=cf_df.set_index('end_date').index))
            amort_lt = cf_df.set_index('end_date').get('lt_amort_deferred_exp', pd.Series(0, index=cf_df.set_index('end_date').index))
            cf_da_sum = (depr + amort_intan + amort_lt).fillna(0) # Sum and fill NaNs resulting from potential missing columns
            temp_is_df = is_df.set_index('end_date').join(cf_da_sum.rename('total_da_cf'), how='left').reset_index()
            total_da = temp_is_df['total_da_cf'].fillna(0)
        else:
            print("Warning: Depreciation and Amortization data not clearly available for ratio calculation.")
            total_da = pd.Series([0] * len(is_df), index=is_df.index) # Ensure index alignment
        
        self.historical_ratios['da_to_revenue_ratio'] = \
            (total_da / is_df['total_revenue'].replace(0, np.nan)).mean()

        if 'c_pay_acq_const_fiolta' in cf_df.columns:
            # Use .get for safety, although checked above
            capex_series = cf_df.set_index('end_date').get('c_pay_acq_const_fiolta', pd.Series(0, index=cf_df.set_index('end_date').index))
            temp_is_df_capex = is_df.set_index('end_date').join(capex_series, how='left').reset_index()
            capex = temp_is_df_capex['c_pay_acq_const_fiolta'].fillna(0)
            # CapEx 应该是负数，但比率计算时通常用其绝对值或根据上下文调整
            self.historical_ratios['capex_to_revenue_ratio'] = \
                (capex.abs() / is_df['total_revenue'].replace(0, np.nan)).mean() 
        else:
            print("Warning: Capex data (c_pay_acq_const_fiolta) not found in cash_flow for ratio calculation.")
            self.historical_ratios['capex_to_revenue_ratio'] = 0

        ar_days_list = []
        if 'accounts_receiv_bill' in bs_df.columns and 'revenue' in is_df.columns and len(bs_df) > 0 and len(is_df) > 0:
            for i in range(len(is_df)):
                current_is_date = is_df['end_date'].iloc[i]
                current_revenue = is_df['revenue'].iloc[i]
                current_ar, prev_ar = self._get_avg_bs_item(bs_df, 'accounts_receiv_bill', current_is_date)
                
                if current_revenue > 0: # 只有当收入大于0时才有意义
                    if current_ar is not None and prev_ar is not None:
                        avg_ar_val = (current_ar + prev_ar) / 2
                        ar_days = avg_ar_val / (current_revenue / 360)
                        ar_days_list.append(ar_days)
                    elif current_ar is not None: # 只有当期数据
                        ar_days = current_ar / (current_revenue / 360)
                        ar_days_list.append(ar_days)
            self.historical_ratios['accounts_receivable_days'] = pd.Series(ar_days_list).mean() if ar_days_list else 0
        else:
            self.historical_ratios['accounts_receivable_days'] = 0

        inv_days_list = []
        if 'inventories' in bs_df.columns and 'oper_cost' in is_df.columns and len(bs_df) > 0 and len(is_df) > 0:
            for i in range(len(is_df)):
                current_is_date = is_df['end_date'].iloc[i]
                current_cogs = is_df['oper_cost'].iloc[i]
                current_inv, prev_inv = self._get_avg_bs_item(bs_df, 'inventories', current_is_date)

                if current_cogs > 0: # 只有当销货成本大于0时才有意义
                    if current_inv is not None and prev_inv is not None:
                        avg_inv_val = (current_inv + prev_inv) / 2
                        inv_days = avg_inv_val / (current_cogs / 360)
                        inv_days_list.append(inv_days)
                    elif current_inv is not None:
                        inv_days = current_inv / (current_cogs / 360)
                        inv_days_list.append(inv_days)
            self.historical_ratios['inventory_days'] = pd.Series(inv_days_list).mean() if inv_days_list else 0
        else:
            self.historical_ratios['inventory_days'] = 0

        ap_days_list = []
        if 'accounts_pay' in bs_df.columns and len(bs_df) > 0:
            if 'c_paid_goods_s' in cf_df.columns and len(cf_df) > 0:
                temp_cf_df = cf_df.set_index('end_date')
                for i in range(len(temp_cf_df)): # Iterate based on cash flow periods
                    current_cf_date = temp_cf_df.index[i]
                    # c_paid_goods_s is usually negative, use absolute for denominator
                    purchases_proxy = abs(temp_cf_df['c_paid_goods_s'].iloc[i]) 
                    current_ap, prev_ap = self._get_avg_bs_item(bs_df, 'accounts_pay', current_cf_date)

                    if purchases_proxy > 0:
                        if current_ap is not None and prev_ap is not None:
                            avg_ap_val = (current_ap + prev_ap) / 2
                            ap_days = avg_ap_val / (purchases_proxy / 360)
                            ap_days_list.append(ap_days)
                        elif current_ap is not None:
                             ap_days = current_ap / (purchases_proxy / 360)
                             ap_days_list.append(ap_days)
            elif 'oper_cost' in is_df.columns and 'inventories' in bs_df.columns and len(is_df) > 0:
                for i in range(len(is_df)): # Iterate based on income statement periods
                    current_is_date = is_df['end_date'].iloc[i]
                    cogs = is_df['oper_cost'].iloc[i]
                    current_inv, prev_inv = self._get_avg_bs_item(bs_df, 'inventories', current_is_date)
                    current_ap, prev_ap = self._get_avg_bs_item(bs_df, 'accounts_pay', current_is_date)

                    purchases_estimated = 0
                    if current_inv is not None and prev_inv is not None:
                        delta_inv = current_inv - prev_inv
                        purchases_estimated = cogs + delta_inv
                    elif cogs > 0 : # Fallback if inventory data is incomplete
                        purchases_estimated = cogs
                    
                    if purchases_estimated > 0:
                        if current_ap is not None and prev_ap is not None:
                            avg_ap_val = (current_ap + prev_ap) / 2
                            ap_days = avg_ap_val / (purchases_estimated / 360)
                            ap_days_list.append(ap_days)
                        elif current_ap is not None:
                             ap_days = current_ap / (purchases_estimated / 360)
                             ap_days_list.append(ap_days)
            self.historical_ratios['accounts_payable_days'] = pd.Series(ap_days_list).mean() if ap_days_list else 0
        else:
            self.historical_ratios['accounts_payable_days'] = 0

        if not bs_df.empty and not is_df.empty:
            last_bs_row = bs_df.iloc[-1]
            last_actual_nwc_val = 0
            
            last_ar, _ = self._get_avg_bs_item(bs_df, 'accounts_receiv_bill', last_bs_row['end_date'])
            last_inv, _ = self._get_avg_bs_item(bs_df, 'inventories', last_bs_row['end_date'])
            last_ap, _ = self._get_avg_bs_item(bs_df, 'accounts_pay', last_bs_row['end_date'])
            
            last_prepayment = last_bs_row.get('prepayment', 0)
            last_oth_cur_assets = last_bs_row.get('oth_cur_assets', 0)
            adv_receipts_col_last = 'contract_liab' if 'contract_liab' in last_bs_row else 'adv_receipts'
            last_adv_receipts = last_bs_row.get(adv_receipts_col_last, 0)
            last_payroll = last_bs_row.get('payroll_payable', 0)
            last_taxes = last_bs_row.get('taxes_payable', 0)
            last_oth_payable = last_bs_row.get('oth_payable', 0)

            last_other_ca = last_prepayment + last_oth_cur_assets
            last_other_cl = last_adv_receipts + last_payroll + last_taxes + last_oth_payable

            last_ar = last_ar if last_ar is not None else 0
            last_inv = last_inv if last_inv is not None else 0
            last_ap = last_ap if last_ap is not None else 0
            
            last_actual_nwc_val = (last_ar + last_inv + last_other_ca) - (last_ap + last_other_cl)
            self.historical_ratios['last_actual_nwc'] = last_actual_nwc_val
            
            if 'oper_cost' in is_df.columns:
                 self.historical_ratios['last_actual_cogs'] = is_df['oper_cost'].iloc[-1] if not is_df.empty else 0
            else:
                 self.historical_ratios['last_actual_cogs'] = 0

            nwc_list_ratio = []
            revenue_list_ratio = []
            for i in range(len(is_df)):
                 current_is_date = is_df['end_date'].iloc[i]
                 current_revenue = is_df['total_revenue'].iloc[i] # Use total_revenue for ratio consistency
                 
                 current_bs_row = bs_df[bs_df['end_date'] == current_is_date]
                 if current_bs_row.empty: continue

                 cur_ar, _ = self._get_avg_bs_item(bs_df, 'accounts_receiv_bill', current_is_date)
                 cur_inv, _ = self._get_avg_bs_item(bs_df, 'inventories', current_is_date)
                 cur_ap, _ = self._get_avg_bs_item(bs_df, 'accounts_pay', current_is_date)
                 
                 cur_prepayment = current_bs_row['prepayment'].iloc[0] if 'prepayment' in current_bs_row else 0
                 cur_oth_cur_assets = current_bs_row['oth_cur_assets'].iloc[0] if 'oth_cur_assets' in current_bs_row else 0
                 adv_receipts_col_cur = 'contract_liab' if 'contract_liab' in current_bs_row else 'adv_receipts'
                 cur_adv_receipts = current_bs_row[adv_receipts_col_cur].iloc[0] if adv_receipts_col_cur in current_bs_row else 0
                 cur_payroll = current_bs_row['payroll_payable'].iloc[0] if 'payroll_payable' in current_bs_row else 0
                 cur_taxes = current_bs_row['taxes_payable'].iloc[0] if 'taxes_payable' in current_bs_row else 0
                 cur_oth_payable = current_bs_row['oth_payable'].iloc[0] if 'oth_payable' in current_bs_row else 0

                 cur_other_ca = cur_prepayment + cur_oth_cur_assets
                 cur_other_cl = cur_adv_receipts + cur_payroll + cur_taxes + cur_oth_payable

                 cur_ar = cur_ar if cur_ar is not None else 0
                 cur_inv = cur_inv if cur_inv is not None else 0
                 cur_ap = cur_ap if cur_ap is not None else 0

                 nwc_val = (cur_ar + cur_inv + cur_other_ca) - (cur_ap + cur_other_cl)
                 if current_revenue > 0: # Only include if revenue is positive
                    nwc_list_ratio.append(nwc_val)
                    revenue_list_ratio.append(current_revenue)

            if revenue_list_ratio:
                 self.historical_ratios['nwc_to_revenue_ratio'] = \
                     (pd.Series(nwc_list_ratio) / pd.Series(revenue_list_ratio)).mean()
            else:
                 self.historical_ratios['nwc_to_revenue_ratio'] = 0.15 
        else:
            self.historical_ratios['last_actual_nwc'] = 0
            self.historical_ratios['last_actual_cogs'] = 0
            self.historical_ratios['nwc_to_revenue_ratio'] = 0.15

        if not bs_df.empty and not is_df.empty:
            bs_df_merged = pd.merge(bs_df, is_df[['end_date', 'total_revenue']], on='end_date', how='inner')
            if not bs_df_merged.empty and bs_df_merged['total_revenue'].abs().sum() > 0:
                other_ca_items = ['prepayment', 'oth_cur_assets']
                # Check if all items exist, otherwise sum available ones
                existing_oca_items = [item for item in other_ca_items if item in bs_df_merged.columns]
                if existing_oca_items:
                    bs_df_merged['calc_other_ca'] = bs_df_merged[existing_oca_items].sum(axis=1)
                    self.historical_ratios['other_current_assets_to_revenue_ratio'] = \
                        (bs_df_merged['calc_other_ca'] / bs_df_merged['total_revenue'].replace(0, np.nan)).mean()
                else:
                    self.historical_ratios['other_current_assets_to_revenue_ratio'] = 0.05 

                adv_receipts_col = 'contract_liab' if 'contract_liab' in bs_df_merged.columns else 'adv_receipts'
                other_cl_items_base = ['payroll_payable', 'taxes_payable', 'oth_payable']
                other_cl_items_to_sum = [adv_receipts_col] + other_cl_items_base
                existing_ocl_items = [item for item in other_cl_items_to_sum if item in bs_df_merged.columns]
                
                if existing_ocl_items:
                    bs_df_merged['calc_other_cl'] = bs_df_merged[existing_ocl_items].sum(axis=1)
                    self.historical_ratios['other_current_liabilities_to_revenue_ratio'] = \
                        (bs_df_merged['calc_other_cl'] / bs_df_merged['total_revenue'].replace(0, np.nan)).mean()
                else:
                    self.historical_ratios['other_current_liabilities_to_revenue_ratio'] = 0.03
            else: 
                self.historical_ratios['other_current_assets_to_revenue_ratio'] = 0.05 
                self.historical_ratios['other_current_liabilities_to_revenue_ratio'] = 0.03
        else: 
            self.historical_ratios['other_current_assets_to_revenue_ratio'] = 0.05 
            self.historical_ratios['other_current_liabilities_to_revenue_ratio'] = 0.03

        if 'income_tax' in is_df.columns and 'total_profit' in is_df.columns:
            valid_tax_calc = is_df[(is_df['total_profit'] > 0) & is_df['income_tax'].notna() & is_df['total_profit'].notna()]
            if not valid_tax_calc.empty:
                self.historical_ratios['effective_tax_rate'] = \
                    (valid_tax_calc['income_tax'] / valid_tax_calc['total_profit']).mean()
            else:
                self.historical_ratios['effective_tax_rate'] = 0.25 
        else:
            self.historical_ratios['effective_tax_rate'] = 0.25 

        print("Historical ratios calculated:", {k: round(v, 4) if isinstance(v, float) else v for k, v in self.historical_ratios.items()})
        return self.historical_ratios

    def get_processed_data(self) -> Dict[str, pd.DataFrame]:
        return self.processed_data

    def get_historical_ratios(self) -> Dict[str, any]:
        return self.historical_ratios

    def _get_avg_bs_item(self, bs_df: pd.DataFrame, item_name: str, current_date: pd.Timestamp) -> Tuple[Union[float, None], Union[float, None]]:
        """
        辅助函数：获取指定日期和上一年度对应日期的资产负债表项目值。
        返回 (当期值, 上期值)，如果找不到则为 None。
        """
        current_item = None
        prev_item = None

        # 查找当期值
        current_bs = bs_df[bs_df['end_date'] == current_date]
        if not current_bs.empty and item_name in current_bs.columns:
            current_item_val = current_bs[item_name].iloc[0]
            if pd.notna(current_item_val):
                current_item = float(current_item_val)


        # 查找上期值 (大约一年前)
        prev_date_target = current_date - pd.DateOffset(years=1)
        
        # 优先查找与目标日期完全匹配的上一年度报告期 (例如，年报对年报)
        prev_bs_exact_year_ago = bs_df[bs_df['end_date'] == prev_date_target]
        if not prev_bs_exact_year_ago.empty and item_name in prev_bs_exact_year_ago.columns:
            prev_item_val = prev_bs_exact_year_ago[item_name].iloc[0]
            if pd.notna(prev_item_val):
                 prev_item = float(prev_item_val)
        
        if prev_item is None: # 如果没有精确匹配的上一年度日期
            # 在目标日期前后寻找最近的记录 (例如 +/- 45天)
            prev_bs_candidates = bs_df[
                (bs_df['end_date'] >= prev_date_target - pd.Timedelta(days=45)) &
                (bs_df['end_date'] <= prev_date_target + pd.Timedelta(days=45)) &
                (bs_df['end_date'] < current_date) # 确保是历史数据
            ]
            
            if not prev_bs_candidates.empty and item_name in prev_bs_candidates.columns:
                 prev_bs_candidates = prev_bs_candidates.copy() # 避免 SettingWithCopyWarning
                 prev_bs_candidates.loc[:, 'date_diff'] = abs(prev_bs_candidates['end_date'] - prev_date_target)
                 closest_prev_bs = prev_bs_candidates.sort_values('date_diff').iloc[0]
                 prev_item_val = closest_prev_bs[item_name]
                 if pd.notna(prev_item_val):
                    prev_item = float(prev_item_val)
            
        if prev_item is None: # 如果还是找不到，尝试找严格小于当前日期的最近一期
             prev_bs_strict = bs_df[bs_df['end_date'] < current_date].sort_values('end_date', ascending=False)
             if not prev_bs_strict.empty and item_name in prev_bs_strict.columns:
                  prev_item_val = prev_bs_strict[item_name].iloc[0]
                  if pd.notna(prev_item_val):
                    prev_item = float(prev_item_val)
        
        # 如果 current_item 是 None 但 prev_item 不是，这可能意味着当期数据缺失，不应返回 prev_item 作为当期
        # 但对于计算平均值，如果 prev_item 存在，它仍然是有效的“上一期”数据

        return current_item, prev_item
