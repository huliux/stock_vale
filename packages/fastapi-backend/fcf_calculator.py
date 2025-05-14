import pandas as pd
import numpy as np
from typing import Optional
from decimal import Decimal, InvalidOperation

class FcfCalculator:
    """负责根据预测的财务数据计算无杠杆自由现金流 (UFCF)。"""

    def calculate_ufcf(self, forecast_df: pd.DataFrame) -> pd.DataFrame:
        """
        在预测 DataFrame 中计算并添加 UFCF 列。
        Args:
            forecast_df (pd.DataFrame): 包含预测期财务数据的 DataFrame。
                                        必须包含 'nopat', 'd_a', 'capex', 'delta_nwc' 列。
                                        'nopat' 代表税后营业利润 (Operating Profit * (1 - Tax Rate))。
                                        'd_a' 代表预测的折旧与摊销。
                                        'capex' 代表预测的资本性支出 (通常为正值)。
                                        'delta_nwc' 代表预测的营运资本净额变动。

        Returns:
            pd.DataFrame: 添加了 'ufcf' 列的原始 DataFrame。如果计算失败或缺少列，
                          'ufcf' 列可能包含 NaN 或不被添加，并打印错误信息。
        """
        required_cols = ['nopat', 'd_a', 'capex', 'delta_nwc']
        missing_cols = [col for col in required_cols if col not in forecast_df.columns]

        if missing_cols:
            print(f"错误: 预测数据中缺少计算 UFCF 所需的列: {', '.join(missing_cols)}")
            # 返回原始 DataFrame，或者可以添加一个充满 NaN 的 'ufcf' 列
            # forecast_df['ufcf'] = np.nan
            return forecast_df

        try:
            # 确保数据类型为 Decimal，并将 NaN 视为 0 处理
            try:
                nopat = pd.to_numeric(forecast_df['nopat'], errors='coerce').fillna(0).apply(Decimal)
                d_a = pd.to_numeric(forecast_df['d_a'], errors='coerce').fillna(0).apply(Decimal)
                capex = pd.to_numeric(forecast_df['capex'], errors='coerce').fillna(0).apply(Decimal) # Capex 通常是正值代表支出
                delta_nwc = pd.to_numeric(forecast_df['delta_nwc'], errors='coerce').fillna(0).apply(Decimal)
            except Exception as conversion_error:
                 print(f"错误: 转换 UFCF 输入列为 Decimal 时出错: {conversion_error}")
                 forecast_df['ufcf'] = np.nan # Assign NaN if conversion fails
                 return forecast_df


            # 计算 UFCF: NOPAT + D&A - Capex - ΔNWC (使用 Decimal)
            ufcf_series = nopat + d_a - capex - delta_nwc
            forecast_df['ufcf'] = ufcf_series # Store as Decimal or convert back

            # 检查计算结果是否有效 (使用 Decimal 方法)
            if ufcf_series.apply(lambda x: x.is_nan() or x.is_infinite()).any():
                 print("警告: UFCF 计算结果包含无效值 (NaN 或 Inf)。")

        except Exception as e:
            print(f"计算 UFCF 时发生错误: {e}")
            # 在出错时，添加 NaN 列
            forecast_df['ufcf'] = np.nan # Assign NaN on error

        return forecast_df

# End of class FcfCalculator
