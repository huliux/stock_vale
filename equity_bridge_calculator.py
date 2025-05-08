import numpy as np
import pandas as pd
from typing import Optional, Tuple, Dict
from decimal import Decimal, InvalidOperation

class EquityBridgeCalculator:
    """负责从企业价值 (EV) 计算到股权价值和每股价值。"""

    def calculate_equity_value(self,
                               enterprise_value: Optional[float],
                               latest_balance_sheet: Optional[pd.Series],
                               total_shares: Optional[float]) -> Tuple[Optional[float], Optional[float], Optional[float], Optional[str]]:
        """
        根据企业价值和最新资产负债表数据计算股权价值和每股价值。
        Args:
            enterprise_value (Optional[float]): 计算出的企业价值。
            latest_balance_sheet (Optional[pd.Series]): 最新的资产负债表数据 Series。
            total_shares (Optional[float]): 最新的总股本数量 (单位：股)。

        Returns:
            Tuple[Optional[float], Optional[float], Optional[float], Optional[str]]:
            (净债务, 股权价值, 每股价值, 错误信息或 None)。
        """
        net_debt_to_return: Optional[float] = None
        equity_value_to_return: Optional[float] = None
        value_per_share_to_return: Optional[float] = None
        error_msg: Optional[str] = None

        try:
            # All processing happens within this main try block
            try:
                ev_decimal = Decimal(enterprise_value) if enterprise_value is not None else None
            except (InvalidOperation, TypeError) as e_conv:
                error_msg = "无效的企业价值输入类型。"
                # Return initial None values for data, plus error
                return net_debt_to_return, equity_value_to_return, value_per_share_to_return, error_msg

            if ev_decimal is None or ev_decimal.is_nan():
                error_msg = "无效的企业价值 (None 或 NaN)，无法计算股权价值。"
                return net_debt_to_return, equity_value_to_return, value_per_share_to_return, error_msg

            if latest_balance_sheet is None or latest_balance_sheet.empty:
                error_msg = "无法获取最新资产负债表数据，无法计算净债务和股权价值。"
                return net_debt_to_return, equity_value_to_return, value_per_share_to_return, error_msg

            # Calculations
            lt_borr = Decimal(latest_balance_sheet.get('lt_borr', 0) or 0)
            st_borr = Decimal(latest_balance_sheet.get('st_borr', 0) or 0)
            bond_payable = Decimal(latest_balance_sheet.get('bond_payable', 0) or 0)
            non_cur_liab_due_1y = Decimal(latest_balance_sheet.get('non_cur_liab_due_1y', 0) or 0)
            total_debt = lt_borr + st_borr + bond_payable + non_cur_liab_due_1y

            money_cap = Decimal(latest_balance_sheet.get('money_cap', 0) or 0)
            cash_equivalents = money_cap
            
            calculated_net_debt = total_debt - cash_equivalents
            net_debt_to_return = float(calculated_net_debt) # Update return value

            minority_interest = Decimal(latest_balance_sheet.get('minority_int', 0) or 0)
            preferred_equity = Decimal(latest_balance_sheet.get('oth_eqt_tools_p_shr', 0) or 0)

            calculated_equity_value = ev_decimal - calculated_net_debt - minority_interest - preferred_equity
            
            if calculated_equity_value.is_nan() or calculated_equity_value.is_infinite():
                error_msg = "计算出的股权价值无效 (NaN 或 Inf)。"
                # net_debt_to_return is already set
                return net_debt_to_return, None, None, error_msg # equity_value_to_return is still None
            
            equity_value_to_return = float(calculated_equity_value) # Update return value

            # Per share calculation
            try:
                ts_decimal = Decimal(total_shares) if total_shares is not None else None
            except (InvalidOperation, TypeError) as e_conv_ts:
                error_msg = "无效的总股本输入类型。"
                # net_debt_to_return and equity_value_to_return are set
                return net_debt_to_return, equity_value_to_return, None, error_msg

            if ts_decimal is not None and not ts_decimal.is_nan() and ts_decimal > Decimal('0'):
                calculated_value_per_share = calculated_equity_value / ts_decimal
                if calculated_value_per_share.is_nan() or calculated_value_per_share.is_infinite():
                    error_msg = "计算出的每股价值无效 (NaN 或 Inf)。"
                    return net_debt_to_return, equity_value_to_return, None, error_msg
                value_per_share_to_return = float(calculated_value_per_share)
            else:
                error_msg = "总股本非正、无效或未提供，无法计算每股价值。"
                # value_per_share_to_return remains None

            return net_debt_to_return, equity_value_to_return, value_per_share_to_return, error_msg

        except Exception as e:
            print(f"计算股权价值桥梁时发生错误: {e}")
            error_msg = f"计算股权价值时发生内部错误: {str(e)}"
            # For a general exception, all calculated values are considered unreliable or not computed.
            # Return the initial None values.
            return None, None, None, error_msg

# End of class EquityBridgeCalculator
