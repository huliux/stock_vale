import pandas as pd
import numpy as np
from typing import Optional
from decimal import Decimal, InvalidOperation

class NwcCalculator:
    """负责计算营运资本净额 (NWC) 及其年度变动 (ΔNWC)。"""

    def calculate_nwc(self, df: pd.DataFrame) -> pd.Series:
        """
        根据给定的财务数据 DataFrame 计算 NWC。
        NWC = 流动资产合计 - 货币资金 - (流动负债合计 - 短期借款 - 一年内到期的非流动负债)
        Args:
            df (pd.DataFrame): 包含所需资产负债表项目的 DataFrame。
                               需要 'total_cur_assets', 'money_cap', 'total_cur_liab',
                               'st_borr' (短期借款), 'non_cur_liab_due_1y' 列。

        Returns:
            pd.Series: 计算出的 NWC Series。如果缺少列，则返回充满 NaN 的 Series。
        """
        required_cols = ['total_cur_assets', 'money_cap', 'total_cur_liab', 'st_borr', 'non_cur_liab_due_1y']
        missing_cols = [col for col in required_cols if col not in df.columns]

        if missing_cols:
            print(f"错误: 计算 NWC 缺少列: {', '.join(missing_cols)}")
            return pd.Series(np.nan, index=df.index)

        try:
            # 确保数据类型为 Decimal，并将 NaN 视为 0
            total_cur_assets = pd.to_numeric(df['total_cur_assets'], errors='coerce').fillna(0).apply(Decimal)
            money_cap = pd.to_numeric(df['money_cap'], errors='coerce').fillna(0).apply(Decimal)
            total_cur_liab = pd.to_numeric(df['total_cur_liab'], errors='coerce').fillna(0).apply(Decimal)
            st_borr = pd.to_numeric(df['st_borr'], errors='coerce').fillna(0).apply(Decimal) # 短期借款
            non_cur_liab_due_1y = pd.to_numeric(df['non_cur_liab_due_1y'], errors='coerce').fillna(0).apply(Decimal) # 一年内到期的非流动负债

            # 计算 NWC (使用 Decimal)
            nwc = (total_cur_assets - money_cap) - \
                  (total_cur_liab - st_borr - non_cur_liab_due_1y)

            return nwc.astype(float) # Convert back to float Series if needed, or keep Decimal

        except Exception as e:
            print(f"计算 NWC 时发生错误: {e}")
            return pd.Series(np.nan, index=df.index)

    def calculate_delta_nwc(self, nwc_series: pd.Series) -> pd.Series:
        """
        计算 NWC 的年度变动 (ΔNWC)。
        Args:
            nwc_series (pd.Series): 按时间顺序排列的 NWC Series (假设索引是时间)。

        Returns:
            pd.Series: 计算出的 ΔNWC Series。第一个值为 NaN。
        """
        if nwc_series is None or nwc_series.empty:
            print("错误: NWC Series 为空，无法计算 ΔNWC。")
            return pd.Series(dtype=float) # Return empty Series of appropriate type

        try:
            # 计算年度差值，假设数据是按年排列且索引是时间
            # 使用 diff() 计算当期与上一期的差值
            delta_nwc = nwc_series.diff()
            # 第一个期间的 diff 结果是 NaN，因为没有前期数据
            return delta_nwc

        except Exception as e:
            print(f"计算 ΔNWC 时发生错误: {e}")
            return pd.Series(np.nan, index=nwc_series.index)

    def calculate_historical_nwc_and_delta(self, historical_bs: pd.DataFrame) -> pd.DataFrame:
        """
        计算历史资产负债表数据的 NWC 和 ΔNWC。
        Args:
            historical_bs (pd.DataFrame): 包含历史资产负债表数据的 DataFrame，
                                          需要按 'end_date' 升序排序。
        Returns:
            pd.DataFrame: 原始 DataFrame 添加了 'nwc' 和 'delta_nwc' 列。
        """
        if historical_bs is None or historical_bs.empty:
             print("历史资产负债表数据为空。")
             return pd.DataFrame() # Return empty DataFrame

        # 确保按日期排序
        historical_bs_sorted = historical_bs.sort_values(by='end_date', ascending=True).copy()

        # 计算 NWC
        historical_bs_sorted['nwc'] = self.calculate_nwc(historical_bs_sorted)

        # 计算 ΔNWC
        historical_bs_sorted['delta_nwc'] = self.calculate_delta_nwc(historical_bs_sorted['nwc'])

        return historical_bs_sorted

    def calculate_forecast_delta_nwc(self, forecast_df: pd.DataFrame, last_historical_nwc: Optional[float]) -> pd.DataFrame:
        """
        计算预测期 DataFrame 的 NWC 和 ΔNWC。
        Args:
            forecast_df (pd.DataFrame): 包含预测期资产负债表项目的 DataFrame，
                                        需要按 'year' 升序排序。
            last_historical_nwc (Optional[float]): 最后一个历史年度的 NWC 值，用于计算第一年的 ΔNWC。

        Returns:
            pd.DataFrame: 原始 DataFrame 添加了 'nwc' 和 'delta_nwc' 列。
        """
        if forecast_df is None or forecast_df.empty:
            print("预测数据为空。")
            return pd.DataFrame()

        try:
            last_hist_nwc_decimal = Decimal(last_historical_nwc) if last_historical_nwc is not None else Decimal('0')
            if last_hist_nwc_decimal.is_nan():
                 print("警告: 提供的最后一个历史 NWC 值无效 (NaN)，将使用 0。")
                 last_hist_nwc_decimal = Decimal('0')
        except (InvalidOperation, TypeError):
             print("警告: 提供的最后一个历史 NWC 值类型无效，将使用 0。")
             last_hist_nwc_decimal = Decimal('0')

        if last_historical_nwc is None: # Print warning only if originally None
             print("警告: 未提供最后一个历史 NWC 值，第一年 ΔNWC 可能不准确 (假设为 0)。")


        forecast_df_sorted = forecast_df.sort_values(by='year', ascending=True).copy()

        # 计算预测期 NWC (结果可能是 float 或 Decimal Series)
        nwc_forecast_series = self.calculate_nwc(forecast_df_sorted)
        forecast_df_sorted['nwc'] = nwc_forecast_series

        # 计算预测期 ΔNWC (确保使用 Decimal 进行计算)
        nwc_decimal_series = nwc_forecast_series.apply(Decimal) # Ensure Decimal for diff calculation
        prev_nwc_list = [last_hist_nwc_decimal] + nwc_decimal_series[:-1].tolist()
        prev_nwc = pd.Series(prev_nwc_list, index=forecast_df_sorted.index) # 对齐索引

        forecast_df_sorted['delta_nwc'] = (nwc_decimal_series - prev_nwc).astype(float) # Convert delta back to float if needed

        return forecast_df_sorted


# End of class NwcCalculator
