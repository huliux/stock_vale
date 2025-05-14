import pandas as pd
import numpy as np
from typing import Dict, Tuple, Union, List, Optional, Any
import traceback # 导入 traceback 模块

pd.set_option('future.no_silent_downcasting', True) # Opt-in to future behavior
from decimal import Decimal, InvalidOperation # Import Decimal and InvalidOperation

# 假设 NwcCalculator 类在 nwc_calculator.py 中定义
from nwc_calculator import NwcCalculator

class DataProcessor:
    """
    负责清洗、处理财务数据，计算历史比率/周转天数中位数，并提取关键信息。
    """
    def __init__(self, 
                 input_data: Dict[str, pd.DataFrame], 
                 latest_pe_pb: Optional[Dict[str, Any]] = None,
                 ttm_dividends_df: Optional[pd.DataFrame] = None, # 新增 TTM 股息数据
                 latest_price: Optional[float] = None): # 新增最新价格
        """
        初始化 DataProcessor。
        Args:
            input_data (Dict[str, pd.DataFrame]): 包含原始数据的字典，
                预期键: 'balance_sheet', 'income_statement', 'cash_flow', 'stock_basic'。
            latest_pe_pb (Optional[Dict[str, Any]]): 包含最新 'pe' 和 'pb' 的字典。
            ttm_dividends_df (Optional[pd.DataFrame]): 包含过去12个月股息数据的DataFrame。
            latest_price (Optional[float]): 最新股价。
        """
        self.input_data = input_data
        self.input_latest_pe_pb = latest_pe_pb or {} # 存储传入的 PE/PB
        self.ttm_dividends_df = ttm_dividends_df # 存储 TTM 股息数据
        self.latest_price_for_yield = latest_price # 存储最新价格，用于股息率计算
        self.processed_data: Dict[str, pd.DataFrame] = {}
        self.historical_ratios: Dict[str, Any] = {}
        self.latest_metrics: Dict[str, Any] = {}
        self.basic_info: Dict[str, Any] = {}
        self.latest_balance_sheet: Optional[pd.Series] = None
        self.base_financial_statement_date: Optional[str] = None # 新增属性
        self.warnings: List[str] = []

        self._process_input_data()
        self.clean_data()
        self.calculate_historical_ratios_and_turnovers() # 初始化时即计算
        self._calculate_and_store_ttm_dividend_yield() # 初始化时计算股息率

    def _process_input_data(self):
        """提取非时间序列信息和最新数据点。"""
        print("Processing input data...")
        # 处理股票基本信息 (现在 input_data['stock_basic'] 是一个 dict)
        df_basic = self.input_data.get('stock_basic') 
        # 修改检查方式，直接检查字典是否为真 (非 None 且非空)
        if df_basic: 
            self.basic_info = df_basic.copy() # 使用副本以避免修改原始传入数据
            print(f"  Using provided basic info for {self.basic_info.get('name', 'N/A')}")
            
            # 处理 act_name 和 act_ent_type 的默认值
            act_name_val = self.basic_info.get('act_name')
            if act_name_val is None or (isinstance(act_name_val, str) and not act_name_val.strip()):
                self.basic_info['act_name'] = "未知"
            
            act_ent_type_val = self.basic_info.get('act_ent_type')
            if act_ent_type_val is None or (isinstance(act_ent_type_val, str) and not act_ent_type_val.strip()):
                self.basic_info['act_ent_type'] = "民营企业"

            # 确保即使原始数据中没有这些键，它们也会被添加到 basic_info 中
            if 'act_name' not in self.basic_info:
                 self.basic_info['act_name'] = "未知"
            if 'act_ent_type' not in self.basic_info:
                 self.basic_info['act_ent_type'] = "民营企业"
            
            # 处理 market 字段的默认值
            market_val = self.basic_info.get('market')
            if market_val is None or (isinstance(market_val, str) and not market_val.strip()):
                self.basic_info['market'] = "未知"
            if 'market' not in self.basic_info: # 确保字段存在
                self.basic_info['market'] = "未知"

        else:
            self.warnings.append("输入数据中缺少 'stock_basic' 表或该表为空。")
            print("Warning: 'stock_basic' table missing or empty.")
            # 如果 df_basic 为空，也应设置默认值
            self.basic_info = {
                'name': '未知名称', # 保留原有默认
                'industry': '未知', # 保留原有默认
                'act_name': '未知',
                'act_ent_type': '民营企业',
                'market': '未知' # 新增 market 的默认值
            }


        # 处理传入的最新 PE/PB
        self.latest_metrics['pe'] = self.input_latest_pe_pb.get('pe')
        self.latest_metrics['pb'] = self.input_latest_pe_pb.get('pb')
        if self.latest_metrics['pe'] is None or self.latest_metrics['pb'] is None:
             warning_msg = "未能获取最新的 PE 或 PB 数据。"
             self.warnings.append(warning_msg); print(f"Warning: {warning_msg}")
        else:
             print(f"  Using provided latest PE: {self.latest_metrics['pe']}, PB: {self.latest_metrics['pb']}")
        
        # 提取最近年报的 diluted_eps
        self.latest_metrics['latest_annual_diluted_eps'] = None
        df_is = self.input_data.get('income_statement')
        if df_is is not None and not df_is.empty and 'end_date' in df_is.columns and 'diluted_eps' in df_is.columns:
            try:
                df_is_copy = df_is.copy() # 操作副本
                df_is_copy['end_date'] = pd.to_datetime(df_is_copy['end_date'])
                # 筛选年报：假设年报的月份是12月，或者 end_type 明确标识 (需要确认 end_type 的含义)
                # 优先使用 end_type (如果存在且含义明确)，否则使用月份判断
                annual_reports = None
                if 'end_type' in df_is_copy.columns: # 假设 '1231' 或类似表示年报
                    # 根据实际 end_type 值调整，这里假设 '4' 代表年报 (Q4累计即全年) 或 '1231'
                    # 如果 end_type 不可靠，则回退到月份判断
                    # 查阅数据库文档，end_type 的含义是报告期类型，但具体值代表年报的约定未知，先用月份
                    annual_reports = df_is_copy[df_is_copy['end_date'].dt.month == 12]
                else: # 如果没有 end_type，则按月份筛选
                    annual_reports = df_is_copy[df_is_copy['end_date'].dt.month == 12]

                if not annual_reports.empty:
                    latest_annual_report = annual_reports.sort_values(by='end_date', ascending=False).iloc[0]
                    if pd.notna(latest_annual_report['diluted_eps']):
                        self.latest_metrics['latest_annual_diluted_eps'] = Decimal(str(latest_annual_report['diluted_eps']))
                        print(f"  Extracted latest annual diluted_eps: {self.latest_metrics['latest_annual_diluted_eps']} for year ending {latest_annual_report['end_date'].year}")
                    else:
                        warning_msg_eps = f"最新年报 ({latest_annual_report['end_date'].year}) 的 diluted_eps 为空。"
                        self.warnings.append(warning_msg_eps); print(f"Warning: {warning_msg_eps}")
                else:
                    warning_msg_eps = "未找到年报数据以提取 diluted_eps。"
                    self.warnings.append(warning_msg_eps); print(f"Warning: {warning_msg_eps}")
            except Exception as e:
                warning_msg_eps = f"提取最新年报 diluted_eps 时出错: {e}"
                self.warnings.append(warning_msg_eps); print(f"Warning: {warning_msg_eps}")
        else:
            warning_msg_eps = "利润表数据不完整，无法提取 diluted_eps。"
            self.warnings.append(warning_msg_eps); print(f"Warning: {warning_msg_eps}")

        # 移除从 valuation_metrics DataFrame 获取 PE/PB 的旧逻辑
        # df_vm = self.input_data.get('valuation_metrics') ... (旧代码移除)

        # 提取最新的资产负债表
        df_bs = self.input_data.get('balance_sheet')
        if df_bs is not None and not df_bs.empty:
            try:
                 if 'end_date' in df_bs.columns:
                    df_bs['end_date'] = pd.to_datetime(df_bs['end_date'])
                    latest_bs_series = df_bs.sort_values(by='end_date', ascending=False).iloc[0]
                    self.latest_balance_sheet = latest_bs_series
                    # 存储基准财务报表日期
                    if pd.notna(latest_bs_series.get('end_date')):
                        self.base_financial_statement_date = pd.to_datetime(latest_bs_series.get('end_date')).strftime('%Y-%m-%d')
                        print(f"  Extracted latest balance sheet for date: {self.base_financial_statement_date}")
                    else:
                        print("  Warning: Latest balance sheet end_date is NaT.")
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

    def _calculate_median_ratio_or_days(self, series1: pd.Series, series2: pd.Series, days_in_year=360) -> Optional[Decimal]: # Use imported Decimal
        """计算两个 Series 比率或周转天数的中位数，忽略无效值，返回 Decimal 类型。"""
        # from decimal import Decimal, InvalidOperation # No longer needed here as it's imported at the top
        try:
            # 确保输入 Series 中的数据是数值类型，并尝试转换为 Decimal
            s1_decimal = series1.apply(lambda x: Decimal(str(x)) if pd.notna(x) else None)
            s2_decimal = series2.apply(lambda x: Decimal(str(x)) if pd.notna(x) else None)

            s1_aligned, s2_aligned = s1_decimal.align(s2_decimal, join='inner')
            
            # Check for non-positive values in denominator before masking
            # 使用 Decimal(0) 进行比较
            if not s2_aligned.empty and (s2_aligned <= Decimal('0')).any(): # Add empty check for s2_aligned
                 warning_msg_nonpos = f"计算比率/天数时 ({series1.name}/{series2.name})，分母包含零或负值。"
                 if warning_msg_nonpos not in self.warnings: 
                     self.warnings.append(warning_msg_nonpos)

            s2_safe = s2_aligned.mask(s2_aligned <= Decimal('0'), None) # 使用 None 替换 np.nan 以便后续 Decimal 处理
            valid_mask = s1_aligned.notna() & s2_safe.notna()
            
            if not valid_mask.any():
                 # 诊断信息
                 diag_info = []
                 s1_name = series1.name if series1.name else 'series1'
                 s2_name = series2.name if series2.name else 'series2'
                 diag_info.append(f"{s1_name} 有效点: {s1_aligned.notna().sum()}")
                 diag_info.append(f"{s2_name} 有效点: {s2_aligned.notna().sum()}")
                 diag_info.append(f"{s2_name} >0 点: {(s2_aligned > Decimal('0')).sum()}")
                 diag_info.append(f"对齐长度: {len(s1_aligned)}")
                 
                 warning_msg = f"无法计算历史中位数 ({s1_name}/{s2_name})：缺少有效配对数据。诊断: [{'; '.join(diag_info)}]. 将使用默认值进行预测。"
                 if warning_msg not in self.warnings: # 避免重复添加完全相同的警告
                    self.warnings.append(warning_msg)
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

        bs_df_orig = self.processed_data.get('balance_sheet')
        is_df_orig = self.processed_data.get('income_statement')
        cf_df_orig = self.processed_data.get('cash_flow')

        if bs_df_orig is None or is_df_orig is None or cf_df_orig is None or bs_df_orig.empty or is_df_orig.empty or cf_df_orig.empty:
            warning_msg = "缺少必要的财务报表数据，无法计算历史比率。"; self.warnings.append(warning_msg); print(f"Error: {warning_msg}")
            return self.historical_ratios

        # 在设置索引前，去除基于 end_date 的重复项，保留最后一条记录
        # 这可以防止 "ValueError: cannot reindex on an axis with duplicate labels"
        if 'end_date' in is_df_orig.columns:
            is_df_orig = is_df_orig.drop_duplicates(subset=['end_date'], keep='last')
        if 'end_date' in cf_df_orig.columns:
            cf_df_orig = cf_df_orig.drop_duplicates(subset=['end_date'], keep='last')
        if 'end_date' in bs_df_orig.columns:
            bs_df_orig = bs_df_orig.drop_duplicates(subset=['end_date'], keep='last')

        # 确保DataFrame使用end_date作为索引并排序
        try:
            is_df = is_df_orig.set_index('end_date').sort_index() if 'end_date' in is_df_orig.columns and not is_df_orig.index.name == 'end_date' else is_df_orig.sort_index()
            cf_df = cf_df_orig.set_index('end_date').sort_index() if 'end_date' in cf_df_orig.columns and not cf_df_orig.index.name == 'end_date' else cf_df_orig.sort_index()
            bs_df = bs_df_orig.set_index('end_date').sort_index() if 'end_date' in bs_df_orig.columns and not bs_df_orig.index.name == 'end_date' else bs_df_orig.sort_index()
        except Exception as e:
            warning_msg = f"设置日期索引时出错: {e}"; self.warnings.append(warning_msg); print(f"Error: {warning_msg}")
            return self.historical_ratios


        # --- 利润表相关比率 ---
        self.historical_ratios['cogs_to_revenue_ratio'] = self._calculate_median_ratio_or_days(
            is_df.get('oper_cost', pd.Series(dtype='float64')), is_df.get('total_revenue', pd.Series(dtype='float64')), days_in_year=None
        )
        
        sga_rd_exp = (is_df.get('sell_exp', pd.Series(0.0, index=is_df.index)) + 
                      is_df.get('admin_exp', pd.Series(0.0, index=is_df.index)) + 
                      is_df.get('rd_exp', pd.Series(0.0, index=is_df.index))).fillna(0).infer_objects(copy=False)
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
        da_cols = ['depr_fa_coga_dpba', 'amort_intang_assets'] #移除了 'use_right_asset_dep'
        existing_da_cols = [col for col in da_cols if col in cf_df.columns] # cf_df 现在有日期索引
        
        total_da_series = pd.Series(dtype=object) # 初始化为空的Series
        if not is_df.empty: # 确保is_df不为空，从而is_df.index有效
            total_da_series = pd.Series(Decimal('0.0'), index=is_df.index, dtype=object).rename('total_da') # 使用Decimal和object


        if existing_da_cols:
             # cf_df 已经设置了 end_date 为索引
             cf_da_sum = cf_df[existing_da_cols].sum(axis=1, skipna=True)
             # 使用 update 或者 reindex + fillna 来合并，确保索引对齐
             total_da_series.update(cf_da_sum) 
             total_da_series = total_da_series.fillna(Decimal('0.0')).infer_objects(copy=False) # 确保更新后没有NaN, 填充Decimal
        else:
             # 如果现金流量表中没有D&A列，total_da_series将保持为全Decimal('0.0') (基于is_df的索引)
             warning_msg = "现金流量表中缺少计算总折旧摊销所需的关键字段（如 depr_fa_coga_dpba, amort_intang_assets）。";
             if warning_msg not in self.warnings: self.warnings.append(warning_msg)
             print(f"Warning: {warning_msg}")
        
        # 针对 da_to_revenue_ratio 的更详细警告
        da_to_revenue_warning_specific = None
        total_revenue_series = is_df.get('total_revenue', pd.Series(dtype='float64'))

        # 检查 total_da_series 是否有效 
        if total_da_series.empty or total_da_series.isnull().all() or (total_da_series.astype(float) == 0.0).all():
            da_to_revenue_warning_specific = "警告：未能从现金流量表构建有效的总折旧摊销数据（数据为空、全为无效值或全为零）。"
        
        # 检查 total_revenue 是否有效
        if total_revenue_series.empty or total_revenue_series.isnull().all() or (total_revenue_series.astype(float) <= 0.0).all(): # 收入通常应为正
            if da_to_revenue_warning_specific: 
                da_to_revenue_warning_specific += " 同时，利润表中总收入数据也为空、全为无效值或全为非正数。"
            else: 
                da_to_revenue_warning_specific = "警告：利润表中总收入数据为空、全为无效值或全为非正数，无法计算D&A/收入比。"

        if da_to_revenue_warning_specific:
            if da_to_revenue_warning_specific not in self.warnings: 
                 self.warnings.append(da_to_revenue_warning_specific)
            print(da_to_revenue_warning_specific)
            self.historical_ratios['da_to_revenue_ratio'] = None 
        else:
            self.historical_ratios['da_to_revenue_ratio'] = self._calculate_median_ratio_or_days(
                total_da_series, total_revenue_series, days_in_year=None
            )
            # _calculate_median_ratio_or_days 内部已有 "缺少有效配对数据" 的警告
            # 如果到这里 self.historical_ratios['da_to_revenue_ratio'] 仍然是 None，
            # 且没有触发上面的 specific warning，则说明是配对问题。
            # 该情况下的通用警告已在 _calculate_median_ratio_or_days 中处理。

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
             # bs_df 和 is_df 已经以 end_date 为索引
             bs_merged_ar = pd.merge(bs_df[['accounts_receiv_bill']], is_df[['revenue']], left_index=True, right_index=True, how='inner')
             self.historical_ratios['accounts_receivable_days'] = self._calculate_median_ratio_or_days(
                 bs_merged_ar['accounts_receiv_bill'], bs_merged_ar['revenue'], days_in_year=360
             )
        else: self.historical_ratios['accounts_receivable_days'] = None

        if 'inventories' in bs_df.columns and 'oper_cost' in is_df.columns:
             # bs_df 和 is_df 已经以 end_date 为索引
             bs_merged_inv = pd.merge(bs_df[['inventories']], is_df[['oper_cost']], left_index=True, right_index=True, how='inner')
             self.historical_ratios['inventory_days'] = self._calculate_median_ratio_or_days(
                 bs_merged_inv['inventories'], bs_merged_inv['oper_cost'], days_in_year=360
             )
        else: self.historical_ratios['inventory_days'] = None

        if 'accounts_pay' in bs_df.columns and 'oper_cost' in is_df.columns:
             # bs_df 和 is_df 已经以 end_date 为索引
             bs_merged_ap = pd.merge(bs_df[['accounts_pay']], is_df[['oper_cost']], left_index=True, right_index=True, how='inner')
             self.historical_ratios['accounts_payable_days'] = self._calculate_median_ratio_or_days(
                 bs_merged_ap['accounts_pay'], bs_merged_ap['oper_cost'], days_in_year=360
             )
        else: self.historical_ratios['accounts_payable_days'] = None
             
        # --- 其他 NWC 相关比率 (中位数) ---
        if 'total_revenue' in is_df.columns:
            # bs_df 和 is_df 已经以 end_date 为索引
            # bs_df 包含所有需要的列，is_df 只需要 total_revenue
            bs_merged_nwc_ratios = pd.merge(bs_df, is_df[['total_revenue']], left_index=True, right_index=True, how='inner')
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
             # 假设 historical_bs_with_nwc 和 is_df 都以 end_date 为索引
             bs_merged_nwc = pd.merge(historical_bs_with_nwc[['nwc']], is_df[['total_revenue']], left_index=True, right_index=True, how='inner')
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

        # --- 计算历史收入 CAGR (优先3年，失败则尝试所有年份) ---
        # from decimal import Decimal, InvalidOperation # No longer needed here
        self.historical_ratios['historical_revenue_cagr'] = None # 初始化为 None
        revenue_col = 'total_revenue' # 确认使用 total_revenue
        
        if revenue_col in is_df.columns and not is_df[revenue_col].isnull().all():
            # is_df 已经以 end_date 为索引并排序，dropna 不会改变索引顺序
            is_df_sorted = is_df.dropna(subset=[revenue_col])
            is_df_sorted[revenue_col] = is_df_sorted[revenue_col].apply(lambda x: Decimal(str(x)) if pd.notna(x) else None) # 转为 Decimal
            is_df_sorted = is_df_sorted.dropna(subset=[revenue_col]) # 再次去除可能因转换失败产生的 None

            calculated_cagr = None

            # 尝试计算3年CAGR
            if len(is_df_sorted) >= 4: # 需要至少4个数据点来计算3年间的CAGR (例如年1, 年2, 年3, 年4 -> 3年期)
                # is_df_sorted.index 是 DatetimeIndex
                if (is_df_sorted.index[-1] - is_df_sorted.index[-4]).days > 365 * 2.5: # 确保时间跨度足够
                    start_revenue = is_df_sorted[revenue_col].iloc[-4]
                    end_revenue = is_df_sorted[revenue_col].iloc[-1]
                    if start_revenue is not None and end_revenue is not None and start_revenue > Decimal('0') and end_revenue > Decimal('0'):
                        try:
                            years_diff = Decimal((is_df_sorted.index[-1] - is_df_sorted.index[-4]).days) / Decimal('365.25')
                            if years_diff > Decimal('0'):
                                # 使用 Decimal 进行幂运算
                                calculated_cagr = (end_revenue / start_revenue) ** (Decimal('1') / years_diff) - Decimal('1')
                                print(f"Calculated 3-year CAGR: {calculated_cagr:.4f}")
                        except Exception as e:
                            warning_msg_cagr_err = f"计算3年收入CAGR时出错: {e}"; self.warnings.append(warning_msg_cagr_err); print(f"Warning: {warning_msg_cagr_err}")
                            calculated_cagr = None # 确保出错时 cagr 为 None
                # else: # 合并警告：3年CAGR因数据点或时间跨度不足而失败
                #     warning_msg_cagr_3y_fail = "无法计算3年收入CAGR：数据点不足或时间跨度不够。"
                #     if warning_msg_cagr_3y_fail not in self.warnings: self.warnings.append(warning_msg_cagr_3y_fail)
            # else: # 合并警告：3年CAGR因数据点或时间跨度不足而失败
            #     warning_msg_cagr_3y_fail = "无法计算3年收入CAGR：数据点不足或时间跨度不够。"
            #     if warning_msg_cagr_3y_fail not in self.warnings: self.warnings.append(warning_msg_cagr_3y_fail)
            
            # 统一处理3年CAGR计算失败的情况
            if calculated_cagr is None:
                 warning_msg_cagr_3y_fail = "无法计算3年收入CAGR：数据不足或计算错误。"
                 if warning_msg_cagr_3y_fail not in self.warnings: self.warnings.append(warning_msg_cagr_3y_fail)

                 # 如果3年CAGR计算失败，尝试计算所有年份CAGR
                 if len(is_df_sorted) >= 2: # 需要至少2个数据点来计算CAGR
                     # is_df_sorted.index 是 DatetimeIndex
                     if (is_df_sorted.index[-1] - is_df_sorted.index[0]).days > 365 * 0.9: # 至少接近一年
                        start_revenue_all = is_df_sorted[revenue_col].iloc[0]
                        end_revenue_all = is_df_sorted[revenue_col].iloc[-1]
                        if start_revenue_all is not None and end_revenue_all is not None and start_revenue_all > Decimal('0') and end_revenue_all > Decimal('0'):
                            try:
                                years_diff_all = Decimal((is_df_sorted.index[-1] - is_df_sorted.index[0]).days) / Decimal('365.25')
                                if years_diff_all > Decimal('0'):
                                    calculated_cagr = (end_revenue_all / start_revenue_all) ** (Decimal('1') / years_diff_all) - Decimal('1')
                                    print(f"Calculated all-years CAGR: {calculated_cagr:.4f}")
                                    # 简化回退警告
                                    warning_msg_cagr_all = "警告：3年收入CAGR计算失败，已回退使用所有年份CAGR。"
                                    if warning_msg_cagr_all not in self.warnings: self.warnings.append(warning_msg_cagr_all)
                            except Exception as e:
                                warning_msg_cagr_all_err = f"计算所有年份收入CAGR时出错: {e}"; self.warnings.append(warning_msg_cagr_all_err); print(f"Warning: {warning_msg_cagr_all_err}")
                                calculated_cagr = None # 确保出错时 cagr 为 None
                     # else: # 合并警告：所有年份CAGR因数据点或时间跨度不足而失败
                     #     warning_msg_cagr_all_fail = "无法计算所有年份收入CAGR：数据点不足或时间跨度不够。"
                     #     if warning_msg_cagr_all_fail not in self.warnings: self.warnings.append(warning_msg_cagr_all_fail)
                 # else: # 合并警告：所有年份CAGR因数据点或时间跨度不足而失败
                 #     warning_msg_cagr_all_fail = "无法计算所有年份收入CAGR：数据点不足或时间跨度不够。"
                 #     if warning_msg_cagr_all_fail not in self.warnings: self.warnings.append(warning_msg_cagr_all_fail)
                 
                 # 统一处理所有年份CAGR也失败的情况
                 if calculated_cagr is None:
                      warning_msg_cagr_all_fail = "警告：无法计算历史收入CAGR（尝试3年及所有年份均失败）。"
                      if warning_msg_cagr_all_fail not in self.warnings: self.warnings.append(warning_msg_cagr_all_fail)


            # 存储最终计算得到的 CAGR (可能是3年的，也可能是所有年份的，或者是 None)
            # 返回给 FinancialForecaster 的应该是小数形式
            self.historical_ratios['historical_revenue_cagr'] = calculated_cagr 

        # 清理结果中的 NaN/NaT 为 None (Decimal 不会有 NaN, 但其他计算可能产生)
        for key, value in self.historical_ratios.items():
            if pd.isna(value):
                self.historical_ratios[key] = None

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

    def get_base_financial_statement_date(self) -> Optional[str]:
        """获取基准财务报表的日期 (YYYY-MM-DD)。"""
        return self.base_financial_statement_date

    def get_latest_actual_ebitda(self) -> Optional[Decimal]:
        """获取最近一个完整财年的实际EBITDA。"""
        is_df = self.processed_data.get('income_statement')
        cf_df = self.processed_data.get('cash_flow')

        if is_df is None or is_df.empty or cf_df is None or cf_df.empty:
            self.warnings.append("无法获取最新实际EBITDA：缺少利润表或现金流量表数据。")
            return None

        try:
            # 确保已排序且日期已转换 (假设 end_date 是 datetime 对象)
            is_df_sorted = is_df.sort_values(by='end_date', ascending=False)
            cf_df_sorted = cf_df.sort_values(by='end_date', ascending=False)

            if is_df_sorted.empty:
                self.warnings.append("无法获取最新实际EBITDA：排序后的利润表为空。")
                return None
                
            latest_is_report = is_df_sorted.iloc[0]
            latest_is_date = latest_is_report['end_date']

            ebit_col_name = 'operate_profit' if 'operate_profit' in latest_is_report.index else 'ebit'
            if ebit_col_name not in latest_is_report.index or pd.isna(latest_is_report[ebit_col_name]):
                # 尝试从第二新的报告中获取 EBIT，以防最新的是季度报告且 EBIT 为空
                if len(is_df_sorted) > 1:
                    second_latest_is_report = is_df_sorted.iloc[1]
                    if ebit_col_name in second_latest_is_report.index and pd.notna(second_latest_is_report[ebit_col_name]):
                        latest_ebit = Decimal(str(second_latest_is_report[ebit_col_name]))
                        latest_is_date = second_latest_is_report['end_date'] # 更新基准日期
                        self.warnings.append(f"最新的利润表报告期 {latest_is_report['end_date'].year} 的 '{ebit_col_name}' 为空, 使用了次新报告期 {latest_is_date.year} 的数据。")
                    else:
                        self.warnings.append(f"无法获取最新实际EBITDA：利润表中缺少 '{ebit_col_name}' 或其值为NaN（已尝试两个最新报告期）。")
                        return None
                else:
                    self.warnings.append(f"无法获取最新实际EBITDA：利润表中缺少 '{ebit_col_name}' 或其值为NaN。")
                    return None
            else:
                latest_ebit = Decimal(str(latest_is_report[ebit_col_name]))


            da_cols = ['depr_fa_coga_dpba', 'amort_intang_assets', 'use_right_asset_dep'] # 根据实际数据列名调整
            existing_da_cols = [col for col in da_cols if col in cf_df_sorted.columns]
            latest_da = Decimal('0')

            if existing_da_cols:
                # 查找与更新后的 latest_is_date 同年份的现金流量表记录
                # 确保 cf_df_sorted['end_date'] 是 datetime 类型
                if not pd.api.types.is_datetime64_any_dtype(cf_df_sorted['end_date']):
                    cf_df_sorted['end_date'] = pd.to_datetime(cf_df_sorted['end_date'])

                cf_df_latest_year = cf_df_sorted[cf_df_sorted['end_date'].dt.year == latest_is_date.year]
                
                if not cf_df_latest_year.empty:
                    # 如果一年有多条记录（例如季度），通常年报的 D&A 是累计值，或者需要加总
                    # 简单起见，如果有多条，取最新的那条记录的 D&A 值（假设它是年报或累计值）
                    # 更准确的做法是识别年报，或加总四个季度（如果数据是单季）
                    latest_cf_for_year = cf_df_latest_year.iloc[0] # 取该年最新的记录
                    
                    da_values_for_latest_year = []
                    for col in existing_da_cols:
                        if col in latest_cf_for_year.index and pd.notna(latest_cf_for_year[col]):
                            da_values_for_latest_year.append(Decimal(str(latest_cf_for_year[col])))
                        else:
                            # 如果某个D&A分项缺失，可以当作0处理或记录警告
                            # self.warnings.append(f"D&A分项 '{col}' 在 {latest_is_date.year} 年的现金流量表中缺失或为NaN。")
                            pass # 暂时忽略单个缺失的D&A分项

                    if da_values_for_latest_year:
                        latest_da = sum(da_values_for_latest_year)
                    else:
                        self.warnings.append(f"无法从现金流量表获取 {latest_is_date.year} 年的有效D&A数据。")
                else:
                    self.warnings.append(f"现金流量表中未找到与利润表年份 {latest_is_date.year} 匹配的D&A数据。")
            else:
                self.warnings.append("现金流量表中缺少足够的D&A相关列来计算最新EBITDA。")
            
            latest_ebitda = latest_ebit + latest_da
            print(f"  Calculated latest actual EBITDA for year ending {latest_is_date.strftime('%Y-%m-%d')}: {latest_ebitda}")
            self.latest_metrics['latest_actual_ebitda'] = latest_ebitda # 存储到 latest_metrics
            return latest_ebitda

        except Exception as e:
            self.warnings.append(f"计算最新实际EBITDA时出错: {e}")
            print(f"Error calculating latest actual EBITDA: {e} \n{traceback.format_exc()}")
            return None

    def _calculate_and_store_ttm_dividend_yield(self):
        """
        计算TTM每股股息 (DPS) 和股息率，并存储到 self.latest_metrics。
        使用 self.ttm_dividends_df 和 self.latest_price_for_yield。
        """
        print("Calculating TTM Dividend Yield...")
        ttm_dps = None
        dividend_yield = None

        if self.ttm_dividends_df is not None and not self.ttm_dividends_df.empty:
            if 'cash_div_tax' in self.ttm_dividends_df.columns:
                # 确保 cash_div_tax 是数值类型
                self.ttm_dividends_df['cash_div_tax'] = pd.to_numeric(self.ttm_dividends_df['cash_div_tax'], errors='coerce')
                # 过滤掉可能的 NaN 值后再求和
                valid_dividends = self.ttm_dividends_df['cash_div_tax'].dropna()
                if not valid_dividends.empty:
                    ttm_dps_float = valid_dividends.sum()
                    ttm_dps = Decimal(str(ttm_dps_float))
                    print(f"  Calculated TTM DPS: {ttm_dps}")
                else:
                    warning_msg = "TTM股息数据中 'cash_div_tax' 列不包含有效数值。"
                    self.warnings.append(warning_msg); print(f"Warning: {warning_msg}")
            else:
                warning_msg = "TTM股息数据中缺少 'cash_div_tax' 列。"
                self.warnings.append(warning_msg); print(f"Warning: {warning_msg}")
        else:
            warning_msg = "未提供TTM股息数据或数据为空。"
            # 不一定是警告，可能就是没有分红
            # self.warnings.append(warning_msg); 
            print(f"Info: {warning_msg}")

        if ttm_dps is not None and self.latest_price_for_yield is not None:
            try:
                latest_price_decimal = Decimal(str(self.latest_price_for_yield))
                if latest_price_decimal > Decimal('0'):
                    dividend_yield_calc = (ttm_dps / latest_price_decimal)
                    dividend_yield = dividend_yield_calc # 已经是 Decimal
                    print(f"  Calculated Dividend Yield: {dividend_yield:.4%}")
                else:
                    warning_msg = "最新股价为0或无效，无法计算股息率。"
                    self.warnings.append(warning_msg); print(f"Warning: {warning_msg}")
            except InvalidOperation:
                warning_msg = f"最新股价 '{self.latest_price_for_yield}' 无法转换为Decimal，无法计算股息率。"
                self.warnings.append(warning_msg); print(f"Warning: {warning_msg}")
        elif ttm_dps is not None and self.latest_price_for_yield is None:
            warning_msg = "缺少最新股价，无法计算股息率。"
            self.warnings.append(warning_msg); print(f"Warning: {warning_msg}")
        
        self.latest_metrics['ttm_dps'] = ttm_dps
        self.latest_metrics['dividend_yield'] = dividend_yield
        print("TTM Dividend Yield calculation finished.")

# End of class DataProcessor
