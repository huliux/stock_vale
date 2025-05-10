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

    def get_wacc_and_ke(self, params: Dict[str, Any] = {}, wacc_weight_mode: str = "target") -> Tuple[Optional[float], Optional[float]]:
        """
        根据提供的参数或默认值计算 WACC 和 Ke。
        Args:
            params (dict): 包含 WACC 计算覆盖参数的字典。
                           键如 'target_debt_ratio', 'cost_of_debt', 'tax_rate',
                           'risk_free_rate', 'beta', 'market_risk_premium', 'size_premium'。
            wacc_weight_mode (str): WACC权重计算模式: 'target' (使用目标债务比例) 
                                   或 'market' (使用最新市场价值计算权重)。
        Returns:
            tuple: (wacc, cost_of_equity) 或 (None, None) 如果计算失败。
        """
        try:
            # 先计算股权成本 (Ke)，因为它不依赖于权重模式
            rf_rate_raw = params.get('risk_free_rate', self.default_risk_free_rate)
            rf_rate = Decimal(str(rf_rate_raw)) if rf_rate_raw is not None else self.default_risk_free_rate

            beta_raw = params.get('beta', self.default_beta)
            beta = Decimal(str(beta_raw)) if beta_raw is not None else self.default_beta

            mrp_raw = params.get('market_risk_premium', self.default_market_risk_premium)
            mrp = Decimal(str(mrp_raw)) if mrp_raw is not None else self.default_market_risk_premium

            size_premium_raw = params.get('size_premium', self.default_size_premium)
            size_premium = Decimal(str(size_premium_raw)) if size_premium_raw is not None else self.default_size_premium
            
            cost_of_equity = rf_rate + beta * mrp + size_premium
            if cost_of_equity.is_nan() or cost_of_equity.is_infinite() or cost_of_equity <= Decimal('0'):
                 print(f"警告: 计算出的权益成本(Ke)无效或非正 ({cost_of_equity:.4f})，无法计算 WACC。参数: Rf={rf_rate}, Beta={beta}, MRP={mrp}, SP={size_premium}")
                 return None, None # Ke 无效，WACC 也无法计算
            
            cost_of_equity_float = float(cost_of_equity)

            # 初始化 debt_ratio 和 equity_ratio
            debt_ratio: Optional[Decimal] = None
            equity_ratio: Optional[Decimal] = None

            if wacc_weight_mode == "market":
                debt_mv, equity_mv = self._get_market_value_debt_and_equity()
                if debt_mv is not None and equity_mv is not None:
                    total_mv = debt_mv + equity_mv
                    if total_mv > Decimal('0'):
                        debt_ratio = debt_mv / total_mv
                        equity_ratio = equity_mv / total_mv
                        print(f"信息: 使用市场价值权重计算 WACC。债务市值: {debt_mv}, 股权市值: {equity_mv}, 债务比例: {debt_ratio:.4f}")
                    else:
                        print("警告: 市场价值计算的总资本为零或负，无法使用市场价值权重。")
                        # 对于市场模式，如果权重计算失败，则 WACC 计算也失败
                        return None, cost_of_equity_float 
                else:
                    print("警告: 无法获取市场价值组件，无法使用市场价值权重。")
                     # 对于市场模式，如果权重计算失败，则 WACC 计算也失败
                    return None, cost_of_equity_float

            # 如果不是市场模式，或者市场模式成功获取了 debt_ratio 和 equity_ratio
            if debt_ratio is None or equity_ratio is None: # 这意味着是目标模式，或者市场模式意外未设置（理论上不应发生）
                if wacc_weight_mode == "target": # 明确是目标模式
                    debt_ratio_raw = params.get('target_debt_ratio', self.default_target_debt_ratio)
                    debt_ratio = Decimal(str(debt_ratio_raw)) if debt_ratio_raw is not None else self.default_target_debt_ratio
                    if not (Decimal('0') <= debt_ratio <= Decimal('1')):
                        print(f"警告: 无效的目标债务比率 ({debt_ratio})，将使用默认值 {self.default_target_debt_ratio}")
                        debt_ratio = self.default_target_debt_ratio
                    equity_ratio = Decimal('1.0') - debt_ratio
                elif wacc_weight_mode == "market": 
                    # 此处不应到达，因为市场模式失败时已提前返回
                    print("错误: 市场模式权重计算逻辑异常。")
                    return None, cost_of_equity_float


            # 确保 debt_ratio 和 equity_ratio 此时已定义且有效
            if debt_ratio is None or equity_ratio is None:
                print("错误: 无法确定债务和股权比例。")
                return None, cost_of_equity_float # Ke 可能有效

            # 获取其他参数
            cost_of_debt_raw = params.get('cost_of_debt', self.default_cost_of_debt_pretax)
            cost_of_debt = Decimal(str(cost_of_debt_raw)) if cost_of_debt_raw is not None else self.default_cost_of_debt_pretax

            tax_rate_raw = params.get('tax_rate', self.default_tax_rate)
            tax_rate = Decimal(str(tax_rate_raw)) if tax_rate_raw is not None else self.default_tax_rate
            if not (Decimal('0') <= tax_rate <= Decimal('1')):
                 print(f"警告: 无效的税率 ({tax_rate})，将使用默认值 {self.default_tax_rate}")
                 tax_rate = self.default_tax_rate

            # 计算税后债务成本
            cost_of_debt_after_tax = cost_of_debt * (Decimal('1') - tax_rate)
            if cost_of_debt_after_tax.is_nan() or cost_of_debt_after_tax.is_infinite():
                 print(f"警告: 计算出的税后债务成本无效 ({cost_of_debt_after_tax:.4f})，无法计算 WACC。参数: Kd={cost_of_debt}, Tax={tax_rate}")
                 return None, cost_of_equity_float

            # 计算 WACC
            wacc = (equity_ratio * cost_of_equity) + (debt_ratio * cost_of_debt_after_tax)

            if wacc.is_nan() or wacc.is_infinite() or not (Decimal('0') < wacc < Decimal('1')):
                 print(f"警告: 计算出的 WACC ({wacc:.4f}) 无效或超出合理范围 (0-100%)。Ke={cost_of_equity:.4f}, Kd(AT)={cost_of_debt_after_tax:.4f}, DebtRatio={debt_ratio:.2f}")
                 return None, cost_of_equity_float # WACC 无效，但 Ke 可能有效

            return float(wacc), cost_of_equity_float

        except Exception as e:
            print(f"计算 WACC 和 Ke 时出错: {e}")
            return None, None

    def _get_market_value_debt_and_equity(self) -> Tuple[Optional[Decimal], Optional[Decimal]]:
        """
        获取债务和股权的市场价值（股权价值即为市值）。
        债务的市场价值通常用其最新的账面价值近似。
        Returns:
            tuple: (debt_market_value, equity_market_value) 或 (None, None) 如果无法计算。
                   equity_market_value 即为 self.market_cap。
        """
        try:
            bs_df = self.financials_dict.get('balance_sheet')
            if bs_df is None or bs_df.empty:
                print("财务数据(资产负债表)为空，无法获取市场价值债务。")
                return None, None

            latest_finance = bs_df.iloc[-1] # 假设已按日期升序排序

            if self.market_cap <= Decimal('0'): # self.market_cap is already Decimal
                print("市值非正，无法计算市场价值权重。")
                # 即使市值非正，债务价值可能仍可计算，但通常一起返回None表示权重计算失败
                return None, None 

            # 计算总附息债务 (账面价值近似市场价值) - 使用 Decimal, convert via str()
            lt_borr = Decimal(str(latest_finance.get('lt_borr', 0) or 0))
            st_borr = Decimal(str(latest_finance.get('st_borr', 0) or 0))
            bond_payable = Decimal(str(latest_finance.get('bond_payable', 0) or 0))
            non_cur_liab_due_1y = Decimal(str(latest_finance.get('non_cur_liab_due_1y', 0) or 0))
            debt_market_value = lt_borr + st_borr + bond_payable + non_cur_liab_due_1y

            # 如果没有明确的有息负债，尝试使用总负债（风险较高）
            if debt_market_value <= Decimal('0'):
                 total_liab = Decimal(str(latest_finance.get('total_liab', 0) or 0))
                 if total_liab <= Decimal('0'):
                      print("警告: 无法获取有效债务数据（有息或总负债），市场价值债务将视为零。")
                      debt_market_value = Decimal('0')
                 else:
                      debt_market_value = total_liab
                      print("警告: 未找到明确的有息负债数据，使用总负债近似债务市值，结果可能不准确。")
            
            return debt_market_value, self.market_cap

        except Exception as e:
            print(f"获取市场价值债务和股权时出错: {e}")
            return None, None

# End of class WaccCalculator
