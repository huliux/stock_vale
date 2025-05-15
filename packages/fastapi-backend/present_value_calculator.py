import numpy as np
import pandas as pd
from typing import Optional, Tuple
from decimal import Decimal, InvalidOperation

class PresentValueCalculator:
    """负责计算现金流和终值的现值。"""

    def calculate_present_values(self,
                                 forecast_df: pd.DataFrame,
                                 terminal_value: Optional[float],
                                 wacc: float) -> Tuple[Optional[float], Optional[float], Optional[pd.DataFrame], Optional[str]]:
        """
        计算预测期 UFCF 的累计现值和终值的现值。
        同时返回包含每期UFCF现值的预测DataFrame。
        Args:
            forecast_df (pd.DataFrame): 包含预测期数据的 DataFrame，
                                        必须包含 'year', 'ufcf' 列。
            terminal_value (Optional[float]): 预测期末计算出的终值。
            wacc (float): 加权平均资本成本，用于折现。

        Returns:
            Tuple[Optional[float], Optional[float], Optional[pd.DataFrame], Optional[str]]:
            (预测期 UFCF 累计现值, 终值现值, 包含pv_ufcf列的预测DataFrame, 错误信息或 None)。
        """
        pv_forecast_ufcf = None
        pv_terminal_value = None
        updated_forecast_df_with_pv = None # Initialize new return value
        error_msg = None

        if forecast_df is None or forecast_df.empty:
            error_msg = "预测数据为空，无法计算现值。"
            return None, None, None, error_msg
        if 'ufcf' not in forecast_df.columns or 'year' not in forecast_df.columns:
            error_msg = "预测数据缺少 'ufcf' 或 'year' 列。"
            return None, None, None, error_msg

        try:
            # --- Move initial conversions inside main try block ---
            try:
                wacc_decimal = Decimal(str(wacc)) # Use str() for float safety
                if not (Decimal('0') < wacc_decimal < Decimal('1')):
                    error_msg = f"无效的 WACC 值: {wacc_decimal:.4f} (应在 0 和 1 之间)。"
                    return None, None, None, error_msg
            except (InvalidOperation, TypeError, ValueError):
                error_msg = f"无效的 WACC 类型: {type(wacc)}。"
                return None, None, None, error_msg

            try:
                tv_decimal = Decimal(str(terminal_value)) if terminal_value is not None else None # Use str()
                # Allow TV=0, but not None or NaN
                if tv_decimal is None:
                     error_msg = "终值未提供 (None)。" # Changed error message slightly
                     return None, None, None, error_msg
                if tv_decimal.is_nan():
                     error_msg = "传入的终值无效 (NaN)。"
                     return None, None, None, error_msg
            except (InvalidOperation, TypeError, ValueError):
                 error_msg = f"无效的终值类型: {type(terminal_value)}。"
                 return None, None, None, error_msg
            # --- End initial conversions ---

            forecast_df_copy = forecast_df.copy()

            # Ensure columns are Decimal for calculation
            forecast_df_copy['year'] = pd.to_numeric(forecast_df_copy['year'], errors='coerce')
            forecast_df_copy['ufcf'] = pd.to_numeric(forecast_df_copy['ufcf'], errors='coerce').apply(Decimal)
            forecast_df_copy = forecast_df_copy.dropna(subset=['year']) # Drop rows where year is invalid

            if forecast_df_copy.empty:
                 error_msg = "有效预测数据为空 (检查 'year' 列)。"
                 return None, None, None, error_msg

            # 计算折现因子 (Decimal)
            one_plus_wacc = Decimal('1') + wacc_decimal
            forecast_df_copy['discount_factor'] = [ (Decimal('1') / one_plus_wacc) ** int(year) for year in forecast_df_copy['year']]

            # 计算每期 UFCF 的现值 (Decimal)
            forecast_df_copy['pv_ufcf'] = forecast_df_copy['ufcf'] * forecast_df_copy['discount_factor']
            updated_forecast_df_with_pv = forecast_df_copy # Assign the df with pv_ufcf column

            # --- Add check for NaN/Inf in individual PVs before summing ---
            if forecast_df_copy['pv_ufcf'].apply(lambda x: isinstance(x, Decimal) and (x.is_nan() or x.is_infinite())).any():
                error_msg = "计算出的单期 UFCF 现值包含无效值 (NaN 或 Inf)。"
                return None, None, updated_forecast_df_with_pv, error_msg # Return df even if sum fails
            # --- End check ---

            # 计算预测期 UFCF 累计现值 (Decimal)
            # Sum should now only contain valid Decimals if the check above passed
            pv_ufcf_decimal = forecast_df_copy['pv_ufcf'].sum()
            # This check might be redundant now but kept for safety
            if pv_ufcf_decimal.is_nan() or pv_ufcf_decimal.is_infinite():
                 error_msg = "计算出的预测期 UFCF 累计现值无效 (NaN 或 Inf)。"
                 return None, None, updated_forecast_df_with_pv, error_msg

            # 计算终值现值 (Decimal)
            last_discount_factor = forecast_df_copy['discount_factor'].iloc[-1]
            pv_terminal_value_decimal = tv_decimal * last_discount_factor
            if pv_terminal_value_decimal.is_nan() or pv_terminal_value_decimal.is_infinite():
                 error_msg = "计算出的终值现值无效 (NaN 或 Inf)。"
                 # 可能 UFCF 现值仍然有效
                 return float(pv_ufcf_decimal), None, updated_forecast_df_with_pv, error_msg

            # Convert results back to float
            return float(pv_ufcf_decimal), float(pv_terminal_value_decimal), updated_forecast_df_with_pv, None # 成功

        except Exception as e:
            print(f"计算现值时发生错误: {e}") # Keep for debugging
            error_msg = f"计算现值时发生内部错误: {str(e)}"
            # Return None for all values in case of a general error
            return None, None, None, error_msg

# End of class PresentValueCalculator
