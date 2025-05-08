import numpy as np
import pandas as pd
import os
from typing import Optional, Tuple, Dict, Any
from decimal import Decimal, InvalidOperation

class WaccCalculator:
    """负责计算加权平均资本成本 (WACC) 和股权成本 (Ke)"""

    def __init__(self, financials_dict: Dict[str, pd.DataFrame], market_cap: Optional[float]):
        """
        初始化 WaccCalculator。
        Args:
            financials_dict (Dict[str, pd.DataFrame]): 包含处理后财务数据的字典，至少需要 'balance_sheet'。
            market_cap (Optional[float]): 最新的市值（单位：亿元）。
        """
        self.financials_dict = financials_dict if isinstance(financials_dict, dict) else {}
        # Convert market cap (in yi yuan) to yuan and then Decimal
        try:
            market_cap_yuan = market_cap * 100000000 if market_cap is not None else 0
            self.market_cap = Decimal(str(market_cap_yuan)) 
        except (InvalidOperation, TypeError, ValueError):
             print(f"警告: 无效的市值输入 ({market_cap})，将使用 0。")
             self.market_cap = Decimal('0')


        # 从环境变量加载或设置默认 WACC 参数 (使用 Decimal)
        try:
            self.default_beta = Decimal(os.getenv('DEFAULT_BETA', '1.0'))
            self.default_risk_free_rate = Decimal(os.getenv('RISK_FREE_RATE', '0.03'))
            self.default_market_risk_premium = Decimal(os.getenv('MARKET_RISK_PREMIUM', '0.05'))
            self.default_cost_of_debt_pretax = Decimal(os.getenv('DEFAULT_COST_OF_DEBT', '0.05'))
            self.default_tax_rate = Decimal(os.getenv('DEFAULT_TARGET_TAX_RATE', '0.25')) # 使用默认目标税率
            self.default_size_premium = Decimal(os.getenv('DEFAULT_SIZE_PREMIUM', '0.0'))
            # 注意：目标债务比率现在作为参数传入 get_wacc_and_ke，但保留默认值
            self.default_target_debt_ratio = Decimal(os.getenv('TARGET_DEBT_RATIO', '0.45'))
        except (ValueError, InvalidOperation): # Catch Decimal conversion errors too
            print("警告：无法从环境变量加载数值 WACC 参数或格式无效，将使用硬编码 Decimal 默认值。")
            self.default_beta = Decimal('1.0')
            self.default_risk_free_rate = Decimal('0.03')
            self.default_market_risk_premium = Decimal('0.05')
            self.default_cost_of_debt_pretax = Decimal('0.05')
            self.default_tax_rate = Decimal('0.25')
            self.default_size_premium = Decimal('0.0')
            self.default_target_debt_ratio = Decimal('0.45')

    def get_wacc_and_ke(self, params: Dict[str, Any] = {}) -> Tuple[Optional[float], Optional[float]]:
        """
        根据提供的参数或默认值计算 WACC 和 Ke。
        Args:
            params (dict): 包含 WACC 计算覆盖参数的字典。
                           键如 'target_debt_ratio', 'cost_of_debt', 'tax_rate',
                           'risk_free_rate', 'beta', 'market_risk_premium', 'size_premium'。
        Returns:
            tuple: (wacc, cost_of_equity) 或 (None, None) 如果计算失败。
        """
        try:
            # 获取参数，检查 None，然后转换为 Decimal (通过 str)
            debt_ratio_raw = params.get('target_debt_ratio', self.default_target_debt_ratio)
            debt_ratio = Decimal(str(debt_ratio_raw)) if debt_ratio_raw is not None else self.default_target_debt_ratio

            cost_of_debt_raw = params.get('cost_of_debt', self.default_cost_of_debt_pretax)
            cost_of_debt = Decimal(str(cost_of_debt_raw)) if cost_of_debt_raw is not None else self.default_cost_of_debt_pretax

            tax_rate_raw = params.get('tax_rate', self.default_tax_rate)
            tax_rate = Decimal(str(tax_rate_raw)) if tax_rate_raw is not None else self.default_tax_rate

            rf_rate_raw = params.get('risk_free_rate', self.default_risk_free_rate)
            rf_rate = Decimal(str(rf_rate_raw)) if rf_rate_raw is not None else self.default_risk_free_rate

            beta_raw = params.get('beta', self.default_beta)
            beta = Decimal(str(beta_raw)) if beta_raw is not None else self.default_beta

            mrp_raw = params.get('market_risk_premium', self.default_market_risk_premium)
            mrp = Decimal(str(mrp_raw)) if mrp_raw is not None else self.default_market_risk_premium

            size_premium_raw = params.get('size_premium', self.default_size_premium)
            size_premium = Decimal(str(size_premium_raw)) if size_premium_raw is not None else self.default_size_premium

            # 参数验证 (使用 Decimal 比较)
            if not (Decimal('0') <= debt_ratio <= Decimal('1')):
                print(f"警告: 无效的目标债务比率 ({debt_ratio})，将使用默认值 {self.default_target_debt_ratio}")
                debt_ratio = self.default_target_debt_ratio
            equity_ratio = Decimal('1.0') - debt_ratio

            if not (Decimal('0') <= tax_rate <= Decimal('1')):
                 print(f"警告: 无效的税率 ({tax_rate})，将使用默认值 {self.default_tax_rate}")
                 tax_rate = self.default_tax_rate

            # 计算股权成本 (Ke)
            cost_of_equity = rf_rate + beta * mrp + size_premium
            if cost_of_equity.is_nan() or cost_of_equity.is_infinite() or cost_of_equity <= Decimal('0'):
                 print(f"警告: 计算出的权益成本(Ke)无效或非正 ({cost_of_equity:.4f})，无法计算 WACC。参数: Rf={rf_rate}, Beta={beta}, MRP={mrp}, SP={size_premium}")
                 return None, None # Ke 无效，WACC 也无法计算

            # 计算税后债务成本
            cost_of_debt_after_tax = cost_of_debt * (Decimal('1') - tax_rate)
            if cost_of_debt_after_tax.is_nan() or cost_of_debt_after_tax.is_infinite():
                 print(f"警告: 计算出的税后债务成本无效 ({cost_of_debt_after_tax:.4f})，无法计算 WACC。参数: Kd={cost_of_debt}, Tax={tax_rate}")
                 # 即使 Kd(AT) 无效，Ke 可能仍然有效，返回 Ke as float
                 return None, float(cost_of_equity) 

            # 计算 WACC
            wacc = (equity_ratio * cost_of_equity) + (debt_ratio * cost_of_debt_after_tax)

            if wacc.is_nan() or wacc.is_infinite() or not (Decimal('0') < wacc < Decimal('1')):
                 print(f"警告: 计算出的 WACC ({wacc:.4f}) 无效或超出合理范围 (0-100%)。Ke={cost_of_equity:.4f}, Kd(AT)={cost_of_debt_after_tax:.4f}, DebtRatio={debt_ratio:.2f}")
                 # WACC 无效，但 Ke 可能有效
                 return None, cost_of_equity

            # 返回 Decimal 类型
            return float(wacc), float(cost_of_equity) # Convert back to float for compatibility if needed, or keep Decimal

        except Exception as e:
            print(f"计算 WACC 和 Ke 时出错: {e}")
            return None, None

    def calculate_wacc_based_on_market_values(self) -> Optional[float]:
        """
        计算基于当前市场价值的 WACC (保留原始逻辑，可能用于参考或回退)。
        注意：此方法使用当前市场价值计算权重，而非目标资本结构。
        """
        try:
            # 使用默认参数计算 Ke (确保是 Decimal)
            cost_of_equity_default = self.default_risk_free_rate + self.default_beta * self.default_market_risk_premium + self.default_size_premium

            bs_df = self.financials_dict.get('balance_sheet')
            if bs_df is None or bs_df.empty:
                print("财务数据(资产负债表)为空，无法计算基于市值的 WACC")
                return None

            latest_finance = bs_df.iloc[-1] # 假设已按日期升序排序

            # Use self.market_cap which is already Decimal
            if self.market_cap <= Decimal('0'):
                print("市值非正，无法计算基于市值的 WACC")
                return None

            # 计算总附息债务 (账面价值近似市场价值) - 使用 Decimal, convert via str()
            lt_borr = Decimal(str(latest_finance.get('lt_borr', 0) or 0))
            st_borr = Decimal(str(latest_finance.get('st_borr', 0) or 0))
            bond_payable = Decimal(str(latest_finance.get('bond_payable', 0) or 0))
            non_cur_liab_due_1y = Decimal(str(latest_finance.get('non_cur_liab_due_1y', 0) or 0)) # 加入一年内到期非流动负债
            debt_market_value = lt_borr + st_borr + bond_payable + non_cur_liab_due_1y

            # 如果没有明确的有息负债，尝试使用总负债（风险较高）
            if debt_market_value <= Decimal('0'):
                 total_liab = Decimal(str(latest_finance.get('total_liab', 0) or 0)) # Convert via str()
                 if total_liab <= Decimal('0'):
                      print("警告: 无法获取有效债务数据（有息或总负债），假设债务为零计算基于市值的 WACC")
                      debt_market_value = Decimal('0')
                 else:
                      debt_market_value = total_liab
                      print("警告: 未找到明确的有息负债数据，使用总负债近似债务市值计算 WACC，结果可能不准确")

            total_capital = self.market_cap + debt_market_value # Use self.market_cap
            if total_capital <= Decimal('0'):
                 print("总资本非正，无法计算基于市值的 WACC")
                 return None

            # 使用默认参数计算税后债务成本 (确保是 Decimal)
            cost_of_debt_after_tax = self.default_cost_of_debt_pretax * (Decimal('1') - self.default_tax_rate)

            # 计算权重 (Decimal)
            equity_weight = self.market_cap / total_capital # Use self.market_cap
            debt_weight = debt_market_value / total_capital

            # 计算 WACC (Decimal)
            wacc = (equity_weight * cost_of_equity_default) + (debt_weight * cost_of_debt_after_tax)

            if not (Decimal('0') < wacc < Decimal('1')):
                 print(f"警告：计算出的基于市值的 WACC ({wacc:.2%}) 超出合理范围 (0% - 100%)，请检查输入参数。")

            return float(wacc) # Convert back to float for compatibility if needed

        except Exception as e:
            print(f"计算基于市值的 WACC 时出错: {e}")
            return None

# End of class WaccCalculator
