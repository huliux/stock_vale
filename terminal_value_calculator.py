import numpy as np
import pandas as pd
from typing import Optional, Dict, Any, Tuple
from decimal import Decimal, InvalidOperation

class TerminalValueCalculator:
    """负责计算预测期结束后的公司价值（终值）。"""

    def __init__(self, risk_free_rate: float):
        """
        初始化 TerminalValueCalculator。
        Args:
            risk_free_rate (float): 无风险利率，用于限制永续增长率。
        """
        try:
            self.risk_free_rate = Decimal(risk_free_rate)
        except (InvalidOperation, TypeError):
             print(f"警告: 无效的无风险利率类型 ({type(risk_free_rate)})，将使用 0.03。")
             self.risk_free_rate = Decimal('0.03')

    def calculate_terminal_value(self,
                                 last_forecast_year_data: pd.Series,
                                 wacc: float,
                                 method: str = 'exit_multiple',
                                 exit_multiple: Optional[float] = None,
                                 perpetual_growth_rate: Optional[float] = None) -> Tuple[Optional[float], Optional[str]]:
        """
        计算终值。
        Args:
            last_forecast_year_data (pd.Series): 包含预测期最后一年数据的 Pandas Series，
                                                 需要 'ebitda' (用于退出乘数法) 或 'ufcf' (用于永续增长法)。
            wacc (float): 加权平均资本成本。
            method (str): 计算方法 ('exit_multiple' 或 'perpetual_growth')。
            exit_multiple (Optional[float]): 退出乘数 (基于 EBITDA)。
            perpetual_growth_rate (Optional[float]): 永续增长率。

        Returns:
            Tuple[Optional[float], Optional[str]]: (计算出的终值, 错误信息字符串或 None)。
        """
        terminal_value_decimal = None
        error_msg = None

        try:
            # Convert inputs to Decimal
            wacc_decimal = Decimal(wacc)
            exit_multiple_decimal = Decimal(exit_multiple) if exit_multiple is not None else None
            pg_rate_decimal = Decimal(perpetual_growth_rate) if perpetual_growth_rate is not None else None

            if method == 'exit_multiple':
                if exit_multiple_decimal is None or exit_multiple_decimal <= Decimal('0'):
                    error_msg = "使用退出乘数法需要提供有效的正退出乘数。"
                    return None, error_msg

                last_ebitda_val = last_forecast_year_data.get('ebitda')
                if last_ebitda_val is None or pd.isna(last_ebitda_val):
                    error_msg = "预测期最后一年的 EBITDA 数据无效，无法使用退出乘数法。"
                    return None, error_msg
                
                # Convert via str() for safety with potential numpy types
                last_ebitda_decimal = Decimal(str(last_ebitda_val)) 
                if last_ebitda_decimal.is_nan() or last_ebitda_decimal.is_infinite():
                     error_msg = "预测期最后一年的 EBITDA 数据无效 (NaN/Inf)，无法使用退出乘数法。"
                     return None, error_msg

                if last_ebitda_decimal <= Decimal('0'):
                    print(f"警告: 预测期最后一年的 EBITDA ({last_ebitda_decimal:.2f}) 非正，退出乘数法计算的终值可能不切实际。")

                terminal_value_decimal = last_ebitda_decimal * exit_multiple_decimal

            elif method == 'perpetual_growth':
                if pg_rate_decimal is None or pg_rate_decimal.is_nan():
                    error_msg = "使用永续增长法需要提供有效的永续增长率。"
                    return None, error_msg

                # 限制永续增长率不超过无风险利率
                pg_rate_to_use = min(pg_rate_decimal, self.risk_free_rate)
                print(f"使用的永续增长率 (已限制为不高于无风险利率): {pg_rate_to_use:.4f}")

                if pg_rate_to_use >= wacc_decimal:
                    # Corrected error message format string
                    error_msg = f"永续增长率 ({pg_rate_to_use:.4f}) 必须小于 WACC ({wacc_decimal:.4f})。"
                    return None, error_msg

                last_ufcf_val = last_forecast_year_data.get('ufcf')
                if last_ufcf_val is None or pd.isna(last_ufcf_val):
                     error_msg = "预测期最后一年的 UFCF 数据无效，无法使用永续增长法。"
                     return None, error_msg
                
                # Convert via str() for safety with potential numpy types
                last_ufcf_decimal = Decimal(str(last_ufcf_val)) 
                if last_ufcf_decimal.is_nan() or last_ufcf_decimal.is_infinite():
                     error_msg = "预测期最后一年的 UFCF 数据无效 (NaN/Inf)，无法使用永续增长法。"
                     return None, error_msg

                if last_ufcf_decimal <= Decimal('0'):
                     error_msg_warn = f"预测期最后一年的 UFCF ({last_ufcf_decimal:.2f}) 非正，无法使用永续增长法计算终值。"
                     print(f"警告: {error_msg_warn}")
                     terminal_value_decimal = Decimal('0') # Set TV to 0 for non-positive UFCF

                # 检查分母是否过小
                denominator = wacc_decimal - pg_rate_to_use
                if abs(denominator) < Decimal('1e-9'): # Use Decimal for comparison
                     error_msg = f"WACC ({wacc_decimal:.4f}) 与永续增长率 ({pg_rate_to_use:.4f}) 过于接近，无法计算终值。"
                     return None, error_msg

                if terminal_value_decimal is None: # Only calculate if UFCF was positive
                    terminal_value_decimal = last_ufcf_decimal * (Decimal('1') + pg_rate_to_use) / denominator

            else:
                error_msg = f"无效的终值计算方法: {method}"
                return None, error_msg

            if terminal_value_decimal is None or terminal_value_decimal.is_nan() or terminal_value_decimal.is_infinite():
                error_msg = "终值计算结果无效 (None, NaN 或 Inf)。"
                return None, error_msg

            return float(terminal_value_decimal), None # 成功计算，无错误

        except Exception as e:
            print(f"计算终值时发生错误: {e}")
            error_msg = f"计算终值时发生内部错误: {str(e)}"
            return None, error_msg

# End of class TerminalValueCalculator
