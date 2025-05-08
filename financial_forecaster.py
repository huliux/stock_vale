import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any, Optional, Union
# Ensure Decimal import is present
from decimal import Decimal, InvalidOperation 

# 假设 NwcCalculator 和 FcfCalculator 类已定义
from nwc_calculator import NwcCalculator
from fcf_calculator import FcfCalculator

class FinancialForecaster:
    def __init__(self,
                 last_actual_revenue: float,
                 historical_ratios: Dict[str, Any],
                 forecast_assumptions: Dict[str, Any]):
        """
        初始化财务预测器。
        Args:
            last_actual_revenue (float): 最后一个已知实际年度的收入。
            historical_ratios (Dict[str, Any]): 包含历史比率/天数中位数和最后一年 NWC 的字典。
            forecast_assumptions (Dict[str, Any]): 包含用户输入的预测假设的字典。
        """
        # 确保 last_actual_revenue 是 Decimal 类型
        try:
            # Convert to string first for floats to ensure precision with Decimal
            self.last_actual_revenue = Decimal(str(last_actual_revenue)) if last_actual_revenue is not None else Decimal('0.0')
        except (InvalidOperation, TypeError, ValueError): # Added ValueError
             print(f"Warning: Invalid last_actual_revenue value '{last_actual_revenue}'. Defaulting to Decimal('0.0').")
             self.last_actual_revenue = Decimal('0.0')
             
        self.historical_ratios = historical_ratios if historical_ratios is not None else {}
        # Convert historical_ratios values to Decimal where appropriate upon initialization or use
        # For now, conversion is done at point of use.

        self.assumptions = forecast_assumptions if forecast_assumptions is not None else {}
        self.forecast_years = self.assumptions.get("forecast_years", 5)
        self.forecasted_statements: Dict[str, pd.DataFrame] = {}

    def _predict_metric_with_mode(self,
                                  metric_name: str,
                                  base_value: Union[float, Dict[str, float]],
                                  hist_median: Optional[float],
                                  year: int,
                                  default_value: float = 0.0) -> Decimal: # Return Decimal
        """
        辅助函数：根据预测模式计算指标值（比率或绝对值）。
        """
        # Ensure inputs are Decimal where appropriate
        try:
            base_value_decimal = Decimal(str(base_value)) if isinstance(base_value, (int, float)) else (Decimal(base_value) if isinstance(base_value, str) else base_value)
            hist_median_decimal = Decimal(str(hist_median)) if hist_median is not None else None # Convert via str for float inputs
            
            # Fetch the target value from assumptions
            # Common key pattern for target values in assumptions is like 'metric_name_target_value' or 'metric_name_target'
            # Let's try a common pattern; this might need adjustment based on actual assumption keys.
            target_key = f'{metric_name}_target_value' # Default assumption key pattern
            if "operating_margin" in metric_name: # Specific key for operating margin
                target_key = 'op_margin_target_value' 
            # Add other specific key patterns if necessary, e.g., for NWC days, ratios etc.
            # Based on test_financial_forecaster.py, assumption keys are like:
            # 'op_margin_target_value', 'sga_rd_ratio_target_value', 'da_ratio_target_value', etc.
            # So, a more generic approach for target key might be needed or specific handling.
            # For now, let's assume a convention like metric_name_target or metric_name_target_value
            # Update: Check multiple possible key patterns based on test fixtures
            target_raw = self.assumptions.get(f'target_{metric_name}') # Pattern like target_operating_margin
            if target_raw is None:
                 target_raw = self.assumptions.get(f'{metric_name}_target') # Pattern like operating_margin_target
            if target_raw is None: 
                 target_raw = self.assumptions.get(f'{metric_name}_target_value') # Pattern like operating_margin_target_value

            target_decimal = Decimal(str(target_raw)) if target_raw is not None else None # Convert via str
            default_value_decimal = Decimal(str(default_value)) # Convert via str
            year_int = int(year) # Year should be int
        except (InvalidOperation, TypeError, ValueError) as e:
             print(f"Warning: Error converting inputs for {metric_name} (target_raw: {target_raw if 'target_raw' in locals() else 'N/A'}) to Decimal/int: {e}. Returning default.")
             return default_value_decimal

        mode = self.assumptions.get(f'{metric_name}_forecast_mode', 'historical_median')
        # target already fetched and converted to target_decimal

        # Determine transition years key based on metric type
        transition_years_key = f'{metric_name}_transition_years' # Default key
        if "days" in metric_name: 
            transition_years_key = 'nwc_days_transition_years'
        elif "other_current" in metric_name: 
            transition_years_key = 'other_nwc_ratio_transition_years'
        elif "operating_margin" in metric_name:
             transition_years_key = 'op_margin_transition_years'
        # Add specific checks for sga and rd transition year keys
        elif metric_name == "sga_to_revenue_ratio":
             transition_years_key = 'sga_transition_years' # Match fixture key
        elif metric_name == "rd_to_revenue_ratio":
             transition_years_key = 'rd_transition_years' # Match fixture key
        # Remove or adjust combined key check if SGA/RD are always separate
        # elif "sga_rd_to_revenue_ratio" in metric_name:
        #      transition_years_key = 'sga_rd_transition_years'
        elif "da_to_revenue_ratio" in metric_name:
             transition_years_key = 'da_ratio_transition_years'
        elif "capex_to_revenue_ratio" in metric_name:
             transition_years_key = 'capex_ratio_transition_years'
        transition_years_input = self.assumptions.get(transition_years_key, self.forecast_years)
        try:
            transition_years = int(transition_years_input) if transition_years_input is not None else int(self.forecast_years)
        except (ValueError, TypeError):
            transition_years = int(self.forecast_years)


        if hist_median_decimal is None:
             start_value = target_decimal if target_decimal is not None else default_value_decimal
             print(f"Warning: Historical median for {metric_name} not available. Using {'target value' if target_decimal is not None else f'default {default_value_decimal}'} as base.")
        else:
             start_value = hist_median_decimal

        current_metric_value = start_value # Default to start_value (hist_median or fallback)

        if mode == 'transition_to_target' and target_decimal is not None and transition_years > 0:
            diff = target_decimal - start_value
            # Ensure transition_years is not zero before division
            step = diff / Decimal(transition_years) if transition_years != 0 else Decimal('0')
            target_year_value = start_value + step * Decimal(min(year_int, transition_years))
            # Ensure transition doesn't overshoot target
            if diff < Decimal('0'): current_metric_value = max(target_decimal, target_year_value)
            else: current_metric_value = min(target_decimal, target_year_value)

        # Apply the calculated metric value (ratio or days) to the base value (using Decimal)
        if "ratio" in metric_name or "operating_margin" in metric_name:
            if isinstance(base_value_decimal, Decimal):
                 return base_value_decimal * current_metric_value
            else:
                 print(f"Warning: Invalid base_value type for ratio calculation: {metric_name}"); return Decimal('0.0')
        elif "days" in metric_name:
            days = current_metric_value
            if metric_name == 'accounts_receivable_days':
                revenue = base_value_decimal if isinstance(base_value_decimal, Decimal) else Decimal('0')
                return (revenue / Decimal('360')) * days if revenue > Decimal('0') else Decimal('0')
            elif metric_name in ['inventory_days', 'accounts_payable_days']:
                 # Base value for these should be a dict containing COGS
                 if isinstance(base_value, dict):
                     try:
                         cogs = Decimal(base_value.get('cogs', 0))
                     except (InvalidOperation, TypeError):
                         cogs = Decimal('0')
                 else:
                     cogs = Decimal('0')
                 return (cogs / Decimal('360')) * days if cogs > Decimal('0') else Decimal('0')
            else: print(f"Warning: Unknown metric type for days calculation: {metric_name}"); return Decimal('0.0')
        else:
             print(f"Warning: Metric name '{metric_name}' doesn't contain 'ratio' or 'days'. Returning calculated value directly."); return current_metric_value

    def predict_revenue(self) -> pd.DataFrame:
        """预测收入 (基于历史 CAGR 和衰减率)。"""
        revenue_forecast = []
        current_revenue = self.last_actual_revenue
        
        # Use the correct key 'historical_revenue_cagr' as provided in the fixture
        historical_cagr_raw = self.historical_ratios.get('historical_revenue_cagr') 
        try:
            # Convert historical CAGR raw value (assumed already a fraction or convertible) to Decimal
            # The fixture provides Decimal('0.12'), so no division by 100 needed.
            default_cagr = Decimal('0.05')
            historical_cagr = default_cagr # Default value
            if historical_cagr_raw is not None:
                try:
                    historical_cagr = Decimal(str(historical_cagr_raw))
                except (InvalidOperation, TypeError, ValueError):
                     print(f"警告：无效的历史收入CAGR值 '{historical_cagr_raw}'。现采用默认值 {default_cagr:.1%}")
                     historical_cagr = default_cagr # Use default if conversion fails
            else:
                 # 简化警告信息，符合用户示例
                 print(f"警告：无法计算历史收入CAGR。现采用默认值 {default_cagr:.1%}")
                 historical_cagr = default_cagr # Use default if raw value is None
        except Exception as e: # Catch potential unexpected errors during get/conversion
             print(f"处理历史收入CAGR时发生错误: {e}。现采用默认值 {default_cagr:.1%}")
             historical_cagr = default_cagr


        decay_rate_input = self.assumptions.get('revenue_cagr_decay_rate') # Renamed key
        try:
            decay_rate = Decimal(decay_rate_input) if decay_rate_input is not None else Decimal('0.1')
            if not (Decimal('0') <= decay_rate <= Decimal('1')):
                 print(f"Warning: 无效的 CAGR 衰减率 ({decay_rate})，将使用默认值 0.1。")
                 decay_rate = Decimal('0.1')
        except (InvalidOperation, TypeError):
             print(f"Warning: 无效的 CAGR 衰减率类型 ({type(decay_rate_input)})，将使用默认值 0.1。")
             decay_rate = Decimal('0.1')


        print(f"Predicting revenue using Historical CAGR ({historical_cagr:.2%}) with decay rate ({decay_rate:.1%})...")
        for year in range(1, self.forecast_years + 1):
            # Use Decimal for calculations
            current_growth_rate = historical_cagr * ((Decimal('1') - decay_rate) ** (year - 1))
            current_revenue *= (Decimal('1') + current_growth_rate)
            revenue_forecast.append({"year": year, "revenue": current_revenue, "revenue_growth_rate": current_growth_rate}) # Corrected key name
            # print(f"  Year {year}: Growth Rate={current_growth_rate:.4f}, Revenue={current_revenue:.2f}")

        # Convert final DataFrame columns to float if needed, or keep as object/Decimal
        df_revenue = pd.DataFrame(revenue_forecast)
        df_revenue['year'] = df_revenue['year'].astype(int)
        # Keep revenue and growth rate as Decimal for now
        # df_revenue['revenue'] = df_revenue['revenue'].astype(float)
        # df_revenue['growth_rate'] = df_revenue['growth_rate'].astype(float)
        self.forecasted_statements['revenue'] = df_revenue
        print("Revenue forecast completed.")
        return df_revenue

    def predict_income_statement_items(self) -> pd.DataFrame:
        """预测利润表项目 (COGS, SGA&RD, EBIT, Income Tax, NOPAT)。"""
        if 'revenue' not in self.forecasted_statements:
            print("Error: Revenue must be predicted first."); return pd.DataFrame()

        df_revenue = self.forecasted_statements['revenue']
        forecast_list = []
        # Use Decimal for historical ratios, handle potential None from .get() before Decimal()
        op_margin_raw = self.historical_ratios.get('operating_margin_median')
        hist_op_margin_median = Decimal(str(op_margin_raw)) if op_margin_raw is not None else Decimal('0.15')

        sga_ratio_raw = self.historical_ratios.get('sga_to_revenue_ratio')
        hist_sga_ratio_median = Decimal(str(sga_ratio_raw)) if sga_ratio_raw is not None else Decimal('0.10')

        rd_ratio_raw = self.historical_ratios.get('rd_to_revenue_ratio')
        hist_rd_ratio_median = Decimal(str(rd_ratio_raw)) if rd_ratio_raw is not None else Decimal('0.05')

        print("Predicting income statement items...")
        for index, row in df_revenue.iterrows():
            year = int(row.get('year', index + 1))
            revenue = Decimal(row.get('revenue', '0'))

            # Predict individual components
            sga_expenses = self._predict_metric_with_mode('sga_to_revenue_ratio', revenue, hist_sga_ratio_median, year, default_value=0.10)
            rd_expenses = self._predict_metric_with_mode('rd_to_revenue_ratio', revenue, hist_rd_ratio_median, year, default_value=0.05)
            ebit = self._predict_metric_with_mode('operating_margin', revenue, hist_op_margin_median, year, default_value=0.15)
            
            # Calculate COGS based on others
            cogs = revenue - ebit - sga_expenses - rd_expenses
            gross_profit = revenue - cogs

            # --- Predict Effective Tax Rate with Transition ---
            hist_tax_rate = Decimal(self.historical_ratios.get('effective_tax_rate', '0.25'))
            target_tax_rate_raw = self.assumptions.get('effective_tax_rate_target')
            target_tax_rate = Decimal(str(target_tax_rate_raw)) if target_tax_rate_raw is not None else hist_tax_rate # Default to hist if no target
            
            # Use general transition years for tax rate
            transition_years_input = self.assumptions.get('transition_years', self.forecast_years)
            try:
                transition_years = int(transition_years_input) if transition_years_input is not None else int(self.forecast_years)
            except (ValueError, TypeError):
                transition_years = int(self.forecast_years)

            # Determine mode (assume target mode if target is provided, else historical)
            # A specific mode key like 'tax_rate_forecast_mode' could be added to assumptions for more control
            tax_rate_mode = 'transition_to_target' if target_tax_rate_raw is not None else 'historical_median'

            current_year_tax_rate = hist_tax_rate # Default to historical

            if tax_rate_mode == 'transition_to_target' and transition_years > 0:
                 diff = target_tax_rate - hist_tax_rate
                 step = diff / Decimal(transition_years) if transition_years != 0 else Decimal('0')
                 target_year_value = hist_tax_rate + step * Decimal(min(year, transition_years))
                 if diff < Decimal('0'): current_year_tax_rate = max(target_tax_rate, target_year_value)
                 else: current_year_tax_rate = min(target_tax_rate, target_year_value)
            
            # Ensure rate is within bounds [0, 1]
            current_year_tax_rate = max(Decimal('0'), min(Decimal('1'), current_year_tax_rate))
            # --- End Tax Rate Prediction ---

            taxes = ebit * current_year_tax_rate if ebit > Decimal('0') else Decimal('0') # Use calculated rate
            nopat = ebit * (Decimal('1') - current_year_tax_rate) # Use calculated rate
            
            # Get revenue_growth_rate from the corresponding row in df_revenue
            # Need to ensure df_revenue has this column and the index aligns
            revenue_growth_rate = df_revenue.loc[index, 'revenue_growth_rate'] if 'revenue_growth_rate' in df_revenue.columns else Decimal('0')


            forecast_list.append({
                "year": year, "revenue": revenue, "revenue_growth_rate": revenue_growth_rate, # Added revenue_growth_rate
                "cogs": cogs, "gross_profit": gross_profit,
                "sga_expenses": sga_expenses, "rd_expenses": rd_expenses, # Separated columns
                "ebit": ebit, "taxes": taxes, "nopat": nopat # Renamed income_tax to taxes
            })
            # print(f"  Year {year}: Revenue={revenue:.2f}, EBIT={ebit:.2f}, NOPAT={nopat:.2f}")

        # Convert final DataFrame columns to float if needed
        df_income_statement = pd.DataFrame(forecast_list)
        df_income_statement['year'] = df_income_statement['year'].astype(int)
        # for col in df_income_statement.columns:
        #     if col != 'year': df_income_statement[col] = df_income_statement[col].astype(float)
        self.forecasted_statements['income_statement'] = df_income_statement
        print("Income statement items forecast completed.")
        return df_income_statement

    def predict_balance_sheet_and_cf_items(self) -> pd.DataFrame:
        """预测与FCF相关的 BS 和 CF 项目 (D&A, CapEx, NWC)。"""
        if 'income_statement' not in self.forecasted_statements:
            print("Error: Income statement items must be predicted first."); return pd.DataFrame()

        df_income_statement = self.forecasted_statements['income_statement']
        forecast_list = []
        # Use Decimal for historical ratios/values, handle potential None from .get() before Decimal()
        da_ratio_raw = self.historical_ratios.get('da_to_revenue_ratio')
        hist_da_ratio = Decimal(str(da_ratio_raw)) if da_ratio_raw is not None else Decimal('0.05')

        capex_ratio_raw = self.historical_ratios.get('capex_to_revenue_ratio')
        hist_capex_ratio = Decimal(str(capex_ratio_raw)) if capex_ratio_raw is not None else Decimal('0.07')

        ar_days_raw = self.historical_ratios.get('accounts_receivable_days')
        hist_ar_days = Decimal(str(ar_days_raw)) if ar_days_raw is not None else Decimal('30')

        inv_days_raw = self.historical_ratios.get('inventory_days')
        hist_inv_days = Decimal(str(inv_days_raw)) if inv_days_raw is not None else Decimal('60')

        ap_days_raw = self.historical_ratios.get('accounts_payable_days')
        hist_ap_days = Decimal(str(ap_days_raw)) if ap_days_raw is not None else Decimal('45')

        oca_ratio_raw = self.historical_ratios.get('other_current_assets_to_revenue_ratio')
        hist_oca_ratio = Decimal(str(oca_ratio_raw)) if oca_ratio_raw is not None else Decimal('0.05')

        ocl_ratio_raw = self.historical_ratios.get('other_current_liabilities_to_revenue_ratio')
        hist_ocl_ratio = Decimal(str(ocl_ratio_raw)) if ocl_ratio_raw is not None else Decimal('0.03')
        
        # Correct key is 'last_actual_nwc' based on fixture
        previous_nwc_raw = self.historical_ratios.get('last_actual_nwc') 
        try:
            previous_nwc = Decimal(str(previous_nwc_raw)) if previous_nwc_raw is not None else Decimal('0.0') # Use str() for safety
            if previous_nwc.is_nan(): previous_nwc = Decimal('0.0')
        except (InvalidOperation, TypeError):
             print(f"Warning: Invalid last_historical_nwc value '{previous_nwc_raw}'. Assuming 0.")
             previous_nwc = Decimal('0.0')
        if previous_nwc_raw is None: print("Warning: Last historical NWC not available, assuming 0.")


        print("Predicting balance sheet and cash flow items...")
        for index, row in df_income_statement.iterrows():
            year = int(row.get('year', index + 1))
            revenue = Decimal(row.get('revenue', '0'))
            cogs = Decimal(row.get('cogs', '0'))

            # Get results as Decimal
            d_a = self._predict_metric_with_mode('da_to_revenue_ratio', revenue, hist_da_ratio, year, default_value=0.05)
            capex = self._predict_metric_with_mode('capex_to_revenue_ratio', revenue, hist_capex_ratio, year, default_value=0.07)
            accounts_receivable = self._predict_metric_with_mode('accounts_receivable_days', revenue, hist_ar_days, year, default_value=30)
            inventories = self._predict_metric_with_mode('inventory_days', {'cogs': cogs}, hist_inv_days, year, default_value=60)
            accounts_payable = self._predict_metric_with_mode('accounts_payable_days', {'cogs': cogs}, hist_ap_days, year, default_value=45)
            other_current_assets = self._predict_metric_with_mode('other_current_assets_to_revenue_ratio', revenue, hist_oca_ratio, year, default_value=0.05)
            other_current_liabilities = self._predict_metric_with_mode('other_current_liabilities_to_revenue_ratio', revenue, hist_ocl_ratio, year, default_value=0.03)

            current_nwc = (accounts_receivable + inventories + other_current_assets) - (accounts_payable + other_current_liabilities)
            delta_nwc = current_nwc - previous_nwc
            previous_nwc = current_nwc # Update for next iteration

            forecast_list.append({
                "year": year, "d_a": d_a, "capex": capex, # Use d_a, capex
                "accounts_receivable": accounts_receivable, "inventories": inventories, "accounts_payable": accounts_payable,
                "other_current_assets": other_current_assets, "other_current_liabilities": other_current_liabilities,
                "nwc": current_nwc, "delta_nwc": delta_nwc # Use nwc, delta_nwc
            })
            # print(f"  Year {year}: D&A={depreciation_amortization:.2f}, Capex={capital_expenditures:.2f}, NWC={current_nwc:.2f}, DeltaNWC={delta_nwc:.2f}")

        # Convert final DataFrame columns to float if needed
        df_bs_cf_items = pd.DataFrame(forecast_list)
        df_bs_cf_items['year'] = df_bs_cf_items['year'].astype(int)
        # for col in df_bs_cf_items.columns:
        #      if col != 'year': df_bs_cf_items[col] = df_bs_cf_items[col].astype(float)


        # 合并 IS 和 BS/CF 项目
        df_income_statement_processed = self.forecasted_statements['income_statement']
        if 'year' not in df_income_statement_processed.columns: print("Error: 'year' column missing in income_statement DataFrame for merge."); return pd.DataFrame()
        # Ensure merge keys are compatible
        merged_df = pd.merge(df_income_statement_processed.astype({'year': int}), df_bs_cf_items.astype({'year': int}), on="year", how="left")

        # 计算 EBITDA (using Decimal)
        if 'nopat' in merged_df.columns and 'd_a' in merged_df.columns:
             # Get target tax rate as Decimal
             target_tax_rate_input = self.assumptions.get('effective_tax_rate_target') # Corrected key name
             try:
                 tax_rate = Decimal(target_tax_rate_input) if target_tax_rate_input is not None else Decimal('0.25')
                 if not (Decimal('0') <= tax_rate <= Decimal('1')): tax_rate = Decimal('0.25')
             except (InvalidOperation, TypeError): tax_rate = Decimal('0.25')

             if abs(Decimal('1') - tax_rate) < Decimal('1e-9'): # Check tax rate is not 1
                  print("Warning: Tax rate is 100% or invalid. Using EBIT + D&A for EBITDA.")
                  if 'ebit' in merged_df.columns: merged_df['ebitda'] = merged_df['ebit'] + merged_df['d_a']
                  else: print("Warning: EBIT column not found."); merged_df['ebitda'] = Decimal('0')
             else:
                  # Ensure nopat and d_a are Decimal before calculation
                  nopat_dec = merged_df['nopat'].apply(Decimal)
                  d_a_dec = merged_df['d_a'].apply(Decimal)
                  calculated_ebit = nopat_dec / (Decimal('1') - tax_rate)
                  merged_df['ebitda'] = calculated_ebit + d_a_dec
        elif 'ebit' in merged_df.columns and 'd_a' in merged_df.columns:
             print("Warning: NOPAT not found, approximating EBITDA using EBIT + D&A.")
             merged_df['ebitda'] = merged_df['ebit'].apply(Decimal) + merged_df['d_a'].apply(Decimal)
        else:
             print("Warning: Cannot calculate EBITDA."); merged_df['ebitda'] = Decimal('0')

        # 计算 UFCF (FcfCalculator should handle Decimal or float inputs now)
        fcf_calculator = FcfCalculator()
        # Pass the merged_df which might have Decimal columns
        final_forecast_df = fcf_calculator.calculate_ufcf(merged_df) 

        # Convert final DataFrame columns to float for output consistency, handling Decimal
        for col in final_forecast_df.columns:
            if col == 'year': # 年份保持整数
                try:
                    final_forecast_df[col] = final_forecast_df[col].astype(int)
                except Exception as e:
                     print(f"Warning: Could not convert year column {col} to int: {e}")
            # Check if the column contains Decimal objects or is a standard numeric type
            elif final_forecast_df[col].apply(lambda x: isinstance(x, Decimal)).any() or pd.api.types.is_numeric_dtype(final_forecast_df[col]):
                try:
                    # Convert Decimal to float, keep other numerics as float
                    final_forecast_df[col] = final_forecast_df[col].apply(lambda x: float(x) if isinstance(x, Decimal) else x).astype(float)
                except Exception as e:
                     print(f"Warning: Could not convert column {col} to float: {e}")
            # else: Keep non-numeric columns as they are (e.g., potentially strings if errors occurred)

        self.forecasted_statements['final_forecast'] = final_forecast_df
        print("Balance sheet/CF items forecast and final merge completed.")
        return final_forecast_df

    def get_full_forecast(self) -> pd.DataFrame:
        """执行完整的预测流程并返回包含所有预测项的 DataFrame。"""
        self.predict_revenue()
        self.predict_income_statement_items()
        self.predict_balance_sheet_and_cf_items()
        return self.forecasted_statements.get('final_forecast', pd.DataFrame())

# 需要 FcfCalculator 类定义
from fcf_calculator import FcfCalculator
