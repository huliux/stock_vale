import pandas as pd
import numpy as np
from typing import Dict, Tuple, Union, List, Optional, Any

# 假设 NwcCalculator 类在 nwc_calculator.py 中定义
from nwc_calculator import NwcCalculator

class DataProcessor:
    """
    负责清洗、处理财务数据，计算历史比率/周转天数中位数，并提取关键信息。
    """
    def __init__(self, 
                 input_data: Dict[str, pd.DataFrame], 
                 latest_pe_pb: Optional[Dict[str, Any]] = None): # 添加 latest_pe_pb 参数
        """
        初始化 DataProcessor。
        Args:
            input_data (Dict[str, pd.DataFrame]): 包含原始数据的字典，
                预期键: 'balance_sheet', 'income_statement', 'cash_flow', 'stock_basic'。
            latest_pe_pb (Optional[Dict[str, Any]]): 包含最新 'pe' 和 'pb' 的字典。
        """
        self.input_data = input_data
        self.input_latest_pe_pb = latest_pe_pb or {} # 存储传入的 PE/PB
        self.processed_data: Dict[str, pd.DataFrame] = {}
        self.historical_ratios: Dict[str, Any] = {}
        self.latest_metrics: Dict[str, Any] = {}
        self.basic_info: Dict[str, Any] = {}
        self.latest_balance_sheet: Optional[pd.Series] = None
        self.warnings: List[str] = []

        self._process_input_data()
        self.clean_data()
        self.calculate_historical_ratios_and_turnovers() # 初始化时即计算

    def _process_input_data(self):
        """提取非时间序列信息和最新数据点。"""
        print("Processing input data...")
        # 处理股票基本信息 (现在 input_data['stock_basic'] 是一个 dict)
        df_basic = self.input_data.get('stock_basic') 
        # 修改检查方式，直接检查字典是否为真 (非 None 且非空)
        if df_basic: 
            self.basic_info = df_basic # 直接使用传入的字典
            print(f"  Using provided basic info for {self.basic_info.get('name', 'N/A')}")
        else:
            self.warnings.append("输入数据中缺少 'stock_basic' 表或该表为空。")
            print("Warning: 'stock_basic' table missing or empty.")

        # 处理传入的最新 PE/PB
        self.latest_metrics['pe'] = self.input_latest_pe_pb.get('pe')
        self.latest_metrics['pb'] = self.input_latest_pe_pb.get('pb')
        if self.latest_metrics['pe'] is None or self.latest_metrics['pb'] is None:
             warning_msg = "未能获取最新的 PE 或 PB 数据。"
             self.warnings.append(warning_msg); print(f"Warning: {warning_msg}")
        else:
             print(f"  Using provided latest PE: {self.latest_metrics['pe']}, PB: {self.latest_metrics['pb']}")
        
        # 移除从 valuation_metrics DataFrame 获取 PE/PB 的旧逻辑
        # df_vm = self.input_data.get('valuation_metrics') ... (旧代码移除)

        # 提取最新的资产负债表
        df_bs = self.input_data.get('balance_sheet')
        if df_bs is not None and not df_bs.empty:
            try:
                 if 'end_date' in df_bs.columns:
                    df_bs['end_date'] = pd.to_datetime(df_bs['end_date'])
                    self.latest_balance_sheet = df_bs.sort_values(by='end_date', ascending=False).iloc[0]
                    print(f"  Extracted latest balance sheet for date: {self.latest_balance_sheet.get('end_date')}")
                 else:
                    warning_msg = "'balance_sheet' 表缺少 'end_date' 列，无法确定最新报表。"; self.warnings.append(warning_msg); print(f"Warning: {warning_msg}")
            except Exception as e:
                warning_msg = f"提取最新资产负债表时出错: {e}"; self.warnings.append(warning_msg); print(f"Warning: {warning_msg}")
        else:
            self.warnings.append("输入数据中缺少 'balance_sheet' 表或该表为空。"); print("Warning: 'balance_sheet' table missing or empty.")

        # 准备时间序列数据进行清洗 (创建副本)
        for table_name in ['balance_sheet', 'income_statement', 'cash_flow']:
            if table_name in self.input_data and self.input_data[table_name] is not None:
                self.processed_data[table_name] = self.input_data[table_name].copy()
            else:
                 warning_msg = f"输入数据中缺少或为空的时间序列表: '{table_name}'。"
                 self.warnings.append(warning_msg); print(f"Warning: {warning_msg}")
                 self.processed_data[table_name] = pd.DataFrame() # 创建空 DataFrame
        print("Input data processing finished.")

    def get_warnings(self) -> List[str]:
        """返回处理过程中记录的所有警告信息。"""
        return self.warnings

    def clean_data(self):
        """
        强化历史时间序列数据的清洗逻辑。
        - 处理异常值 (基于 IQR)。
        - 处理缺失值 (插值、填充、最终用 0 填充并记录警告)。
        - 在 self.processed_data 中原地修改 DataFrame。
        """
        print("Starting data cleaning for time-series data...")
        key_financial_items = { # 用于指导插值策略
            'income_statement': ['total_revenue', 'revenue', 'oper_cost', 'sell_exp', 'admin_exp', 'rd_exp', 'income_tax', 'total_profit'],
            'balance_sheet': ['accounts_receiv_bill', 'inventories', 'accounts_pay', 'prepayment', 'oth_cur_assets', 'contract_liab', 'adv_receipts', 'payroll_payable', 'taxes_payable', 'oth_payable', 'total_cur_assets', 'total_cur_liab', 'money_cap', 'st_borr', 'non_cur_liab_due_1y'],
            'cash_flow': ['depr_fa_coga_dpba', 'amort_intang_assets', 'lt_amort_deferred_exp', 'c_pay_acq_const_fiolta', 'c_paid_goods_s']
        }

        for table_name, df_to_clean in self.processed_data.items():
            if table_name not in ['balance_sheet', 'income_statement', 'cash_flow']: continue
            if df_to_clean.empty: print(f"Skipping cleaning for empty table: {table_name}"); continue

            print(f"Cleaning table: {table_name}")
            if 'end_date' in df_to_clean.columns:
                try:
                    df_to_clean['end_date'] = pd.to_datetime(df_to_clean['end_date'])
                    df_to_clean.sort_values(by='end_date', inplace=True)
                except Exception as e:
                    warning_msg = f"无法转换 'end_date' 为 datetime 或在 {table_name} 中排序: {e}"; self.warnings.append(warning_msg); print(f"Warning: {warning_msg}")
            else:
                 warning_msg = f"表 '{table_name}' 缺少 'end_date' 列，无法按时间排序。"; self.warnings.append(warning_msg); print(f"Warning: {warning_msg}")

            numeric_cols = df_to_clean.select_dtypes(include=np.number).columns
            for col in numeric_cols:
                if col not in df_to_clean.columns: continue
                # print(f"  Processing column: {col}") # 减少打印

                # 1. 异常值处理 (替换为 NaN)
                if df_to_clean[col].notna().sum() >= 4:
                    q1 = df_to_clean[col].quantile(0.25)
                    q3 = df_to_clean[col].quantile(0.75)
                    iqr = q3 - q1
                    if iqr > 1e-9:
                        lower_bound = q1 - 1.5 * iqr
                        upper_bound = q3 + 1.5 * iqr
                        outliers_mask = (df_to_clean[col] < lower_bound) | (df_to_clean[col] > upper_bound)
                        num_outliers = outliers_mask.sum()
                        if num_outliers > 0:
                            outlier_indices = df_to_clean.index[outliers_mask].tolist()
                            outlier_dates = df_to_clean.loc[outliers_mask, 'end_date'].dt.strftime('%Y-%m-%d').tolist() if 'end_date' in df_to_clean.columns else ['N/A'] * num_outliers
                            outlier_values = [round(v, 2) if pd.notna(v) else v for v in df_to_clean.loc[outliers_mask, col].tolist()]
                            warning_msg_outlier = f"在表 '{table_name}' 的列 '{col}' 中检测到 {num_outliers} 个潜在异常值 (日期: {outlier_dates}, 值: {outlier_values})。已替换为 NaN 进行后续处理。"
                            self.warnings.append(warning_msg_outlier); print(f"    警告: {warning_msg_outlier}")
                            df_to_clean.loc[outliers_mask, col] = np.nan

                # 2. 缺失值处理 (NaN)
                if df_to_clean[col].isnull().any():
                    # print(f"    处理 {col} 中的 NaN 值") # 减少打印
                    original_nan_count = df_to_clean[col].isnull().sum()
                    nan_indices_before = df_to_clean.index[df_to_clean[col].isnull()].tolist()
                    nan_dates_before = df_to_clean.loc[nan_indices_before, 'end_date'].dt.strftime('%Y-%m-%d').tolist() if 'end_date' in df_to_clean.columns else ['N/A'] * original_nan_count

                    # 策略1: 线性插值
                    interpolated_count = 0
                    if table_name in key_financial_items and col in key_financial_items.get(table_name, []) and df_to_clean[col].notna().sum() >= 2:
                        try:
                            interpolated_values = df_to_clean[col].interpolate(method='linear', limit_direction='both', limit_area='inside')
                            df_to_clean[col] = interpolated_values
                            interpolated_count = original_nan_count - df_to_clean[col].isnull().sum()
                            # if interpolated_count > 0: print(f"      对 {col} 应用了线性插值，填充了 {interpolated_count} 个 NaN。") # 减少打印
                        except Exception as e: print(f"      对 {col} 进行插值时出错: {e}")

                    # 策略2: 前向/后向填充
                    ffill_count = 0; bfill_count = 0
                    if df_to_clean[col].isnull().any():
                        filled_ffill = df_to_clean[col].ffill()
                        ffill_count = df_to_clean[col].isnull().sum() - filled_ffill.isnull().sum()
                        if ffill_count > 0: df_to_clean[col] = filled_ffill; # print(f"      对 {col} 应用了前向填充，填充了 {ffill_count} 个 NaN。") # 减少打印
                        
                        filled_bfill = df_to_clean[col].bfill()
                        bfill_count = df_to_clean[col].isnull().sum() - filled_bfill.isnull().sum()
                        if bfill_count > 0: df_to_clean[col] = filled_bfill; # print(f"      对 {col} 应用了后向填充，填充了 {bfill_count} 个 NaN。") # 减少打印

                    # 策略3: 用 0 填充剩余 NaN 并记录警告
                    if df_to_clean[col].isnull().any():
                        remaining_nan_count = df_to_clean[col].isnull().sum()
                        nan_indices_after = df_to_clean.index[df_to_clean[col].isnull()].tolist()
                        nan_dates_after = df_to_clean.loc[nan_indices_after, 'end_date'].dt.strftime('%Y-%m-%d').tolist() if 'end_date' in df_to_clean.columns else ['N/A'] * remaining_nan_count
                        warning_msg_fill_zero = f"在表 '{table_name}' 的列 '{col}' 中，有 {remaining_nan_count} 个 NaN 值（日期: {nan_dates_after}）在插值和填充后仍然存在，已用 0 填充。请注意这可能影响计算结果。"
                        self.warnings.append(warning_msg_fill_zero); print(f"      警告: {warning_msg_fill_zero}")
                        df_to_clean[col] = df_to_clean[col].fillna(0)
            
            self.processed_data[table_name] = df_to_clean 

        print("数据清洗完成。")

    def _calculate_median_ratio_or_days(self, series1: pd.Series, series2: pd.Series, days_in_year=360) -> Optional['Decimal']:
        """计算两个 Series 比率或周转天数的中位数，忽略无效值，返回 Decimal 类型。"""
        from decimal import Decimal, InvalidOperation # 确保 Decimal 在此作用域可用
        try:
            # 确保输入 Series 中的数据是数值类型，并尝试转换为 Decimal
            s1_decimal = series1.apply(lambda x: Decimal(str(x)) if pd.notna(x) else None)
            s2_decimal = series2.apply(lambda x: Decimal(str(x)) if pd.notna(x) else None)

            s1_aligned, s2_aligned = s1_decimal.align(s2_decimal, join='inner')
            
            # Check for non-positive values in denominator before masking
            # 使用 Decimal(0) 进行比较
            if (s2_aligned <= Decimal('0')).any():
                 warning_msg_nonpos = f"计算比率/天数时 ({series1.name}/{series2.name})，分母包含零或负值。"
                 if warning_msg_nonpos not in self.warnings: 
                     self.warnings.append(warning_msg_nonpos)

            s2_safe = s2_aligned.mask(s2_aligned <= Decimal('0'), None) # 使用 None 替换 np.nan 以便后续 Decimal 处理
            valid_mask = s1_aligned.notna() & s2_safe.notna()
            
            if not valid_mask.any():
                 warning_msg = f"计算中位数时，列 '{series1.name}' 和 '{series2.name}' 之间没有有效的配对数据点。"
                 self.warnings.append(warning_msg);
                 return None

            s1_valid = s1_aligned[valid_mask]
            s2_valid = s2_safe[valid_mask]

            if days_in_year:
                # Decimal 运算
                turnover_days_series = (s1_valid * Decimal(days_in_year)) / s2_valid
                # 过滤条件也使用 Decimal
                turnover_days_filtered = turnover_days_series[(turnover_days_series >= Decimal('0')) & (turnover_days_series < Decimal(days_in_year * 10))] 
                if turnover_days_filtered.empty:
                     warning_msg = f"计算周转天数时 ({series1.name}/{series2.name})，所有有效值均被过滤。"
                     self.warnings.append(warning_msg);
                     return None
                # Pandas median() 返回 float, 需要转回 Decimal
                median_float = turnover_days_filtered.median()
                result = Decimal(str(median_float)) if pd.notna(median_float) else None
            else:
                ratio_series = s1_valid / s2_valid
                if ratio_series.empty:
                     warning_msg = f"计算比率时 ({series1.name}/{series2.name})，没有有效的计算结果。"
                     self.warnings.append(warning_msg);
                     return None
                median_float = ratio_series.median()
                result = Decimal(str(median_float)) if pd.notna(median_float) else None
            
            return result
        except InvalidOperation as ie: # 捕获 Decimal 转换错误
            warning_msg = f"计算中位数比率/天数时发生 Decimal 转换错误 ({series1.name}/{series2.name}): {ie}"
            self.warnings.append(warning_msg); print(f"Warning: {warning_msg}")
            return None
        except Exception as e:
            warning_msg = f"计算中位数比率/天数时出错 ({series1.name}/{series2.name}): {e}"
            self.warnings.append(warning_msg); print(f"Warning: {warning_msg}")
            return None

    def calculate_historical_ratios_and_turnovers(self) -> Dict[str, Any]:
        """
        精确计算历史财务比率和周转天数的中位数。
        使用 self.processed_data 中清洗后的数据。
        """
        print("Calculating historical ratios and turnovers (using median)...")
        self.historical_ratios = {} # 重置

        bs_df = self.processed_data.get('balance_sheet')
        is_df = self.processed_data.get('income_statement')
        cf_df = self.processed_data.get('cash_flow')

        if bs_df is None or is_df is None or cf_df is None or bs_df.empty or is_df.empty or cf_df.empty:
            warning_msg = "缺少必要的财务报表数据，无法计算历史比率。"; self.warnings.append(warning_msg); print(f"Error: {warning_msg}")
            return self.historical_ratios

        # --- 利润表相关比率 ---
        self.historical_ratios['cogs_to_revenue_ratio'] = self._calculate_median_ratio_or_days(
            is_df.get('oper_cost', pd.Series()), is_df.get('total_revenue', pd.Series()), days_in_year=None
        )
        
        sga_rd_exp = (is_df.get('sell_exp', 0) + is_df.get('admin_exp', 0) + is_df.get('rd_exp', 0))
        if isinstance(sga_rd_exp, (int, float)) and sga_rd_exp == 0 and not any(c in is_df for c in ['sell_exp', 'admin_exp', 'rd_exp']):
             self.historical_ratios['sga_rd_to_revenue_ratio'] = 0.0
        else:
             self.historical_ratios['sga_rd_to_revenue_ratio'] = self._calculate_median_ratio_or_days(
                 sga_rd_exp, is_df.get('total_revenue', pd.Series()), days_in_year=None
             )
        
        # 计算营业利润率中位数 (需要 EBIT 或 Operating Profit)
        op_profit_col = 'operate_profit' if 'operate_profit' in is_df.columns else 'ebit' # 优先使用 operate_profit
        if op_profit_col in is_df.columns:
             self.historical_ratios['operating_margin_median'] = self._calculate_median_ratio_or_days(
                 is_df[op_profit_col], is_df.get('total_revenue', pd.Series()), days_in_year=None
             )
        else:
             self.historical_ratios['operating_margin_median'] = None
             warning_msg = f"缺少 '{op_profit_col}' 列，无法计算历史营业利润率中位数。"; self.warnings.append(warning_msg); print(f"Warning: {warning_msg}")


        # --- D&A 和 Capex 相关比率 ---
        da_cols = ['depr_fa_coga_dpba', 'amort_intang_assets', 'use_right_asset_dep']
        existing_da_cols = [col for col in da_cols if col in cf_df.columns]
        total_da_series = pd.Series(0, index=is_df.index) # 初始化
        if existing_da_cols:
             cf_indexed = cf_df.set_index('end_date') if 'end_date' in cf_df.columns else cf_df
             is_indexed = is_df.set_index('end_date') if 'end_date' in is_df.columns else is_df
             cf_da = cf_indexed[existing_da_cols].sum(axis=1, skipna=True).rename('total_da')
             is_df_merged = is_indexed.join(cf_da, how='left')
             total_da_series = is_df_merged['total_da'].fillna(0)
        else:
             warning_msg = "现金流量表中缺少足够的 D&A 相关列。"; self.warnings.append(warning_msg); print(f"Warning: {warning_msg}")
             
        self.historical_ratios['da_to_revenue_ratio'] = self._calculate_median_ratio_or_days(
            total_da_series, is_df.get('total_revenue', pd.Series()), days_in_year=None
        )

        if 'c_pay_acq_const_fiolta' in cf_df.columns and 'total_revenue' in is_df.columns:
            cf_indexed = cf_df.set_index('end_date') if 'end_date' in cf_df.columns else cf_df
            is_indexed = is_df.set_index('end_date') if 'end_date' in is_df.columns else is_df
            capex_series = cf_indexed['c_pay_acq_const_fiolta'].abs()
            is_df_merged_capex = is_indexed.join(capex_series.rename('capex_abs'), how='left')
            capex_abs_aligned = is_df_merged_capex['capex_abs'].fillna(0)
            total_revenue_aligned = is_df_merged_capex.get('total_revenue', pd.Series())
            self.historical_ratios['capex_to_revenue_ratio'] = self._calculate_median_ratio_or_days(
                capex_abs_aligned, total_revenue_aligned, days_in_year=None
            )
        else:
            warning_msg = "缺少 Capex 或收入数据，无法计算 Capex/收入比率。"; self.warnings.append(warning_msg); print(f"Warning: {warning_msg}")
            self.historical_ratios['capex_to_revenue_ratio'] = None

        # --- 周转天数 (使用中位数) ---
        if 'accounts_receiv_bill' in bs_df.columns and 'revenue' in is_df.columns:
             bs_merged_ar = pd.merge(bs_df[['end_date', 'accounts_receiv_bill']], is_df[['end_date', 'revenue']], on='end_date', how='inner')
             self.historical_ratios['accounts_receivable_days'] = self._calculate_median_ratio_or_days(
                 bs_merged_ar['accounts_receiv_bill'], bs_merged_ar['revenue'], days_in_year=360
             )
        else: self.historical_ratios['accounts_receivable_days'] = None

        if 'inventories' in bs_df.columns and 'oper_cost' in is_df.columns:
             bs_merged_inv = pd.merge(bs_df[['end_date', 'inventories']], is_df[['end_date', 'oper_cost']], on='end_date', how='inner')
             self.historical_ratios['inventory_days'] = self._calculate_median_ratio_or_days(
                 bs_merged_inv['inventories'], bs_merged_inv['oper_cost'], days_in_year=360
             )
        else: self.historical_ratios['inventory_days'] = None

        if 'accounts_pay' in bs_df.columns and 'oper_cost' in is_df.columns:
             bs_merged_ap = pd.merge(bs_df[['end_date', 'accounts_pay']], is_df[['end_date', 'oper_cost']], on='end_date', how='inner')
             self.historical_ratios['accounts_payable_days'] = self._calculate_median_ratio_or_days(
                 bs_merged_ap['accounts_pay'], bs_merged_ap['oper_cost'], days_in_year=360
             )
        else: self.historical_ratios['accounts_payable_days'] = None
             
        # --- 其他 NWC 相关比率 (中位数) ---
        if 'total_revenue' in is_df.columns:
            bs_merged_nwc_ratios = pd.merge(bs_df, is_df[['end_date', 'total_revenue']], on='end_date', how='inner')
            if not bs_merged_nwc_ratios.empty:
                 other_ca_items = ['prepayment', 'oth_cur_assets']
                 existing_oca_items = [item for item in other_ca_items if item in bs_merged_nwc_ratios.columns]
                 if existing_oca_items:
                     bs_merged_nwc_ratios['calc_other_ca'] = bs_merged_nwc_ratios[existing_oca_items].sum(axis=1, skipna=True)
                     self.historical_ratios['other_current_assets_to_revenue_ratio'] = self._calculate_median_ratio_or_days(
                         bs_merged_nwc_ratios['calc_other_ca'], bs_merged_nwc_ratios['total_revenue'], days_in_year=None
                     )
                 else: self.historical_ratios['other_current_assets_to_revenue_ratio'] = None

                 adv_receipts_col = 'contract_liab' if 'contract_liab' in bs_merged_nwc_ratios.columns else 'adv_receipts'
                 other_cl_items_base = ['payroll_payable', 'taxes_payable', 'oth_payable']
                 other_cl_items_to_sum = [adv_receipts_col] + other_cl_items_base
                 existing_ocl_items = [item for item in other_cl_items_to_sum if item in bs_merged_nwc_ratios.columns]
                 if existing_ocl_items:
                     bs_merged_nwc_ratios['calc_other_cl'] = bs_merged_nwc_ratios[existing_ocl_items].sum(axis=1, skipna=True)
                     self.historical_ratios['other_current_liabilities_to_revenue_ratio'] = self._calculate_median_ratio_or_days(
                         bs_merged_nwc_ratios['calc_other_cl'], bs_merged_nwc_ratios['total_revenue'], days_in_year=None
                     )
                 else: self.historical_ratios['other_current_liabilities_to_revenue_ratio'] = None
            else: # Merge result is empty
                 self.historical_ratios['other_current_assets_to_revenue_ratio'] = None
                 self.historical_ratios['other_current_liabilities_to_revenue_ratio'] = None
        else: # Missing total_revenue
             self.historical_ratios['other_current_assets_to_revenue_ratio'] = None
             self.historical_ratios['other_current_liabilities_to_revenue_ratio'] = None


        # --- NWC 计算 (使用 NwcCalculator) ---
        nwc_calculator = NwcCalculator()
        historical_bs_with_nwc = nwc_calculator.calculate_historical_nwc_and_delta(bs_df) # bs_df is already cleaned and sorted
        self.processed_data['balance_sheet'] = historical_bs_with_nwc # Update with nwc columns

        if 'nwc' in historical_bs_with_nwc.columns and 'total_revenue' in is_df.columns:
             bs_merged_nwc = pd.merge(historical_bs_with_nwc[['end_date', 'nwc']], is_df[['end_date', 'total_revenue']], on='end_date', how='inner')
             self.historical_ratios['nwc_to_revenue_ratio'] = self._calculate_median_ratio_or_days(
                 bs_merged_nwc['nwc'], bs_merged_nwc['total_revenue'], days_in_year=None
             )
        else: self.historical_ratios['nwc_to_revenue_ratio'] = None

        if 'nwc' in historical_bs_with_nwc.columns and not historical_bs_with_nwc.empty:
             self.historical_ratios['last_historical_nwc'] = historical_bs_with_nwc['nwc'].iloc[-1]
        else: self.historical_ratios['last_historical_nwc'] = None

        # --- 有效税率中位数 ---
        if 'income_tax' in is_df.columns and 'total_profit' in is_df.columns:
            is_df['calc_tax_rate'] = is_df['income_tax'] / is_df['total_profit'].replace(0, np.nan)
            valid_tax_rates = is_df['calc_tax_rate'][(is_df['calc_tax_rate'] >= 0) & (is_df['calc_tax_rate'] <= 1)]
            if not valid_tax_rates.empty:
                 self.historical_ratios['effective_tax_rate'] = valid_tax_rates.median()
            else:
                 self.historical_ratios['effective_tax_rate'] = None
                 warning_msg = "无法计算有效的历史税率中位数。"; self.warnings.append(warning_msg); print(f"Warning: {warning_msg}")
        else:
            self.historical_ratios['effective_tax_rate'] = None

        # --- 计算历史 CAGR ---
        if 'revenue' in is_df.columns and len(is_df) >= 4:
            is_df_sorted = is_df.sort_values(by='end_date')
            # Ensure we have at least 3 years difference for 3-year CAGR
            if (is_df_sorted['end_date'].iloc[-1] - is_df_sorted['end_date'].iloc[-4]).days > 365 * 2.5:
                start_revenue = is_df_sorted['revenue'].iloc[-4]
                end_revenue = is_df_sorted['revenue'].iloc[-1]
                if pd.notna(start_revenue) and pd.notna(end_revenue) and start_revenue > 0 and end_revenue > 0:
                    try:
                        # Calculate exact years between the points for accuracy
                        years_diff = (is_df_sorted['end_date'].iloc[-1] - is_df_sorted['end_date'].iloc[-4]).days / 365.25
                        if years_diff > 0: # Avoid division by zero or negative exponent
                            revenue_cagr_3y = ((end_revenue / start_revenue) ** (1/years_diff)) - 1
                            self.historical_ratios['revenue_cagr_3y'] = revenue_cagr_3y * 100 # Store as percentage
                        else: self.historical_ratios['revenue_cagr_3y'] = None
                    except Exception as e:
                        warning_msg_cagr_err = f"计算3年收入CAGR时出错: {e}"; self.warnings.append(warning_msg_cagr_err); print(warning_msg_cagr_err); self.historical_ratios['revenue_cagr_3y'] = None
                else: self.historical_ratios['revenue_cagr_3y'] = None
            else: 
                 self.historical_ratios['revenue_cagr_3y'] = None
                 warning_msg_cagr_span = "Warning: 数据点时间跨度不足3年，无法计算3年收入CAGR。"
                 self.warnings.append(warning_msg_cagr_span); # Removed print(warning_msg_cagr_span)
        else:
            self.historical_ratios['revenue_cagr_3y'] = None
            if len(is_df) < 4: 
                 warning_msg_cagr_len = "Warning: 数据点少于4个，无法计算3年收入CAGR。"
                 self.warnings.append(warning_msg_cagr_len); # Removed print(warning_msg_cagr_len)

        # 清理结果中的 NaN 为 None
        for key, value in self.historical_ratios.items():
            if pd.isna(value): self.historical_ratios[key] = None

        print("Historical ratios (median) and CAGR calculated:", {k: round(v, 4) if isinstance(v, (float, np.number)) and v is not None else v for k, v in self.historical_ratios.items()})
        return self.historical_ratios

    def get_processed_data(self) -> Dict[str, pd.DataFrame]:
        """获取清洗和处理后的时间序列数据。"""
        return self.processed_data

    def get_historical_ratios(self) -> Dict[str, Any]:
        """获取计算出的历史比率/天数中位数。"""
        return self.historical_ratios

    def get_latest_metrics(self) -> Dict[str, Any]:
        """获取最新的估值指标 (PE, PB)。"""
        return self.latest_metrics

    def get_basic_info(self) -> Dict[str, Any]:
        """获取股票基本信息。"""
        return self.basic_info
    
    def get_latest_balance_sheet(self) -> Optional[pd.Series]:
        """获取最新的资产负债表 Series。"""
        return self.latest_balance_sheet

# End of class DataProcessor
