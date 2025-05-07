import pandas as pd
from typing import Dict, List, Tuple, Any

class FinancialForecaster:
    def __init__(self,
                 last_actual_revenue: float,
                 historical_ratios: Dict[str, Any],
                 forecast_assumptions: Dict[str, Any]):
        """
        初始化财务预测器。
        (文档字符串保持不变)
        """
        self.last_actual_revenue = last_actual_revenue
        self.historical_ratios = historical_ratios
        self.assumptions = forecast_assumptions
        self.forecast_years = forecast_assumptions.get("forecast_years", 5)
        self.forecasted_statements = {}

    def predict_revenue(self) -> pd.DataFrame:
        """
        任务 2.1: 实现销售额预测的多阶段增长模型。
        返回一个包含各年预测收入的 DataFrame。
        """
        revenue_forecast = []
        current_revenue = self.last_actual_revenue
        
        growth_stages = self.assumptions.get("revenue_growth_stages", [])
        if not growth_stages: 
            default_growth_rate = self.historical_ratios.get('historical_revenue_cagr', 0.05) 
            print(f"Warning: No revenue growth stages provided. Using default growth rate: {default_growth_rate:.2%}")
            for year in range(1, self.forecast_years + 1):
                current_revenue *= (1 + default_growth_rate)
                revenue_forecast.append({"year": year, "revenue": current_revenue})
        else:
            year_counter = 0
            for stage in growth_stages:
                duration = stage.get("duration", 0)
                growth_rate = stage.get("growth_rate", 0)
                for _ in range(duration):
                    year_counter += 1
                    if year_counter > self.forecast_years:
                        break
                    current_revenue *= (1 + growth_rate)
                    revenue_forecast.append({"year": year_counter, "revenue": current_revenue})
                if year_counter >= self.forecast_years:
                    break
            
            if year_counter < self.forecast_years and growth_stages:
                last_growth_rate = growth_stages[-1].get("growth_rate", 0)
                print(f"Info: Growth stages cover {year_counter} years. Extending with last growth rate {last_growth_rate:.2%} for remaining {self.forecast_years - year_counter} years.")
                for year in range(year_counter + 1, self.forecast_years + 1):
                    current_revenue *= (1 + last_growth_rate)
                    revenue_forecast.append({"year": year, "revenue": current_revenue})

        df_revenue = pd.DataFrame(revenue_forecast)
        # 确保 year 列是整数类型
        df_revenue['year'] = df_revenue['year'].astype(int) 
        self.forecasted_statements['revenue'] = df_revenue
        print("Revenue forecast completed:\n", df_revenue)
        return df_revenue

    def predict_income_statement_items(self) -> pd.DataFrame: # Added return type hint
        """
        任务 2.2 (初步): 预测利润表其他项目 (销货成本、三费、折旧摊销等)
        基于预测的收入和历史比率（可调整）。
        """
        if 'revenue' not in self.forecasted_statements:
            print("Error: Revenue must be predicted first.")
            return pd.DataFrame() # Return empty DataFrame on error

        df_revenue = self.forecasted_statements['revenue']
        forecast_list = []

        def get_adjustment(key_name: str, year_index: int) -> float:
            adjustments = self.assumptions.get(key_name, [])
            return adjustments[year_index] if year_index < len(adjustments) else 0

        for index, row in df_revenue.iterrows():
            # 使用 .get() 访问以防万一，尽管 predict_revenue 应该确保列存在
            year = row.get('year', index + 1) # Fallback to index if 'year' is missing
            revenue = row.get('revenue', 0)
            
            base_cogs_ratio = self.historical_ratios.get('cogs_to_revenue_ratio', 0.6)
            cogs_adjustment = get_adjustment('cogs_to_revenue_adjustment', index)
            predicted_cogs_ratio = base_cogs_ratio * (1 + cogs_adjustment) 
            cogs = revenue * predicted_cogs_ratio
            
            base_sga_rd_ratio = self.historical_ratios.get('sga_rd_to_revenue_ratio', 0.2)
            sga_rd_adjustment = get_adjustment('sga_rd_to_revenue_adjustment', index)
            predicted_sga_rd_ratio = base_sga_rd_ratio * (1 + sga_rd_adjustment)
            sga_rd = revenue * predicted_sga_rd_ratio
            
            # Gross Profit (for reference, not strictly needed for EBIT if using ratios)
            gross_profit = revenue - cogs
            
            # EBIT (using predicted components)
            ebit = gross_profit - sga_rd # Simplified EBIT calculation
            
            effective_tax_rate = self.assumptions.get('effective_tax_rate', 0.25)
            income_tax = ebit * effective_tax_rate if ebit > 0 else 0
            nopat = ebit * (1 - effective_tax_rate) # Renamed from noplat to nopat

            forecast_list.append({
                "year": year,
                "revenue": revenue,
                "cogs": cogs,
                "gross_profit": gross_profit, # Include gross_profit
                "sga_rd": sga_rd, # Renamed from sga_rd_expenses for consistency
                "ebit": ebit,
                "income_tax": income_tax,
                "nopat": nopat # Ensure nopat is included and correctly named
            })
        
        df_income_statement = pd.DataFrame(forecast_list)
        # Ensure year is int
        df_income_statement['year'] = df_income_statement['year'].astype(int)
        self.forecasted_statements['income_statement'] = df_income_statement
        print("Income statement items forecast completed:\n", df_income_statement)
        return df_income_statement

    def predict_balance_sheet_and_cf_items(self) -> pd.DataFrame: # Added return type hint
        """
        任务 2.3 (初步) 和 任务 3.1 (初步): 预测与FCF相关的资产负债表和现金流量表项目
        主要是 D&A, CapEx, 和 营运资本变化 (ΔWC)
        """
        if 'income_statement' not in self.forecasted_statements:
            print("Error: Income statement items must be predicted first.")
            return pd.DataFrame() # Return empty DataFrame on error

        df_income_statement = self.forecasted_statements['income_statement']
        forecast_list = [] 
        
        def get_adjustment(key_name: str, year_index: int) -> float:
            adjustments = self.assumptions.get(key_name, [])
            return adjustments[year_index] if year_index < len(adjustments) else 0

        last_actual_cogs = self.historical_ratios.get('last_actual_cogs', self.last_actual_revenue * self.historical_ratios.get('cogs_to_revenue_ratio', 0.6))
        initial_ar = (self.last_actual_revenue / 360) * self.historical_ratios.get('accounts_receivable_days', 30)
        initial_inv = (last_actual_cogs / 360) * self.historical_ratios.get('inventory_days', 60)
        initial_ap = (last_actual_cogs / 360) * self.historical_ratios.get('accounts_payable_days', 45)
        initial_other_ca = self.last_actual_revenue * self.historical_ratios.get('other_current_assets_to_revenue_ratio', 0.05)
        initial_other_cl = self.last_actual_revenue * self.historical_ratios.get('other_current_liabilities_to_revenue_ratio', 0.03)

        # Check for initial_nwc_override from assumptions
        # Ensure the key matches exactly what's set in the test fixture assumptions
        initial_nwc_override_value = self.assumptions.get('initial_nwc_override')

        if initial_nwc_override_value is not None:
            previous_nwc = initial_nwc_override_value
            print(f"Using provided initial NWC override: {previous_nwc}")
        else:
            # Calculate previous_nwc based on historical ratios if override is not provided
            previous_nwc = (initial_ar + initial_inv + initial_other_ca) - (initial_ap + initial_other_cl)
            print(f"Calculated initial NWC for forecast base (no override): {previous_nwc}")

        for index, row in df_income_statement.iterrows():
            year = row.get('year', index + 1)
            revenue = row.get('revenue', 0)
            cogs = row.get('cogs', 0) 

            base_da_ratio = self.historical_ratios.get('da_to_revenue_ratio', 0.05)
            da_adjustment = get_adjustment('da_to_revenue_adjustment', index)
            predicted_da_ratio = base_da_ratio * (1 + da_adjustment)
            depreciation_amortization = revenue * predicted_da_ratio

            base_capex_ratio = self.historical_ratios.get('capex_to_revenue_ratio', 0.07)
            capex_adjustment = get_adjustment('capex_to_revenue_adjustment', index)
            predicted_capex_ratio = base_capex_ratio * (1 + capex_adjustment)
            capital_expenditures = revenue * predicted_capex_ratio
            
            ar_days_target = self.assumptions.get('accounts_receivable_days_target')
            if ar_days_target is None:
                base_ar_days = self.historical_ratios.get('accounts_receivable_days', 30) 
                ar_days_adjustment = get_adjustment('ar_days_adjustment', index) 
                predicted_ar_days = base_ar_days * (1 + ar_days_adjustment)
            else:
                predicted_ar_days = ar_days_target 
            accounts_receivable = (revenue / 360) * predicted_ar_days

            inv_days_target = self.assumptions.get('inventory_days_target')
            if inv_days_target is None:
                base_inv_days = self.historical_ratios.get('inventory_days', 60) 
                inv_days_adjustment = get_adjustment('inv_days_adjustment', index)
                predicted_inv_days = base_inv_days * (1 + inv_days_adjustment)
            else:
                predicted_inv_days = inv_days_target
            inventories = (cogs / 360) * predicted_inv_days 

            ap_days_target = self.assumptions.get('accounts_payable_days_target')
            if ap_days_target is None:
                base_ap_days = self.historical_ratios.get('accounts_payable_days', 45) 
                ap_days_adjustment = get_adjustment('ap_days_adjustment', index)
                predicted_ap_days = base_ap_days * (1 + ap_days_adjustment)
            else:
                predicted_ap_days = ap_days_target
            accounts_payable = (cogs / 360) * predicted_ap_days

            base_other_curr_assets_ratio = self.historical_ratios.get('other_current_assets_to_revenue_ratio', 0.05)
            oca_adj = get_adjustment('other_ca_ratio_adjustment', index)
            other_current_assets = revenue * (base_other_curr_assets_ratio * (1 + oca_adj))

            base_other_curr_liab_ratio = self.historical_ratios.get('other_current_liabilities_to_revenue_ratio', 0.03)
            ocl_adj = get_adjustment('other_cl_ratio_adjustment', index)
            other_current_liabilities = revenue * (base_other_curr_liab_ratio * (1 + ocl_adj))
            
            current_nwc = (accounts_receivable + inventories + other_current_assets) - \
                          (accounts_payable + other_current_liabilities)
            
            delta_nwc = current_nwc - previous_nwc
            previous_nwc = current_nwc

            forecast_list.append({
                "year": year,
                "depreciation_amortization": depreciation_amortization,
                "capital_expenditures": capital_expenditures,
                "accounts_receivable": accounts_receivable,
                "inventories": inventories, # Ensure inventory is included
                "accounts_payable": accounts_payable,
                "other_current_assets": other_current_assets, 
                "other_current_liabilities": other_current_liabilities, 
                "net_working_capital": current_nwc,
                "delta_net_working_capital": delta_nwc
            })
            
        df_bs_cf_items = pd.DataFrame(forecast_list)
        # Ensure year is int
        df_bs_cf_items['year'] = df_bs_cf_items['year'].astype(int)

        # Merge BS/CF items with Income Statement items
        df_income_statement_processed = self.forecasted_statements['income_statement']
        if 'year' not in df_income_statement_processed.columns:
             print("Error: 'year' column missing in income_statement DataFrame for merge.")
             return pd.DataFrame() # Return empty if merge key is missing

        # Perform the merge
        merged_df = pd.merge(
            df_income_statement_processed, df_bs_cf_items, on="year", how="left"
        )
        
        # Check if merge was successful and contains expected columns
        # 'nopat' is now correctly named from the income statement prediction
        required_merged_cols = ['year', 'revenue', 'cogs', 'nopat', 'depreciation_amortization',
                                'capital_expenditures', 'delta_net_working_capital', 'inventories']
        if not all(col in merged_df.columns for col in required_merged_cols):
             print(f"Error: Merged DataFrame is missing required columns. Required: {required_merged_cols}. Found: {merged_df.columns.tolist()}")
             # Attempt to return at least the BS/CF items if merge failed partially
             self.forecasted_statements['fcf_components'] = df_bs_cf_items
             return df_bs_cf_items

        # Calculate EBITDA after merge
        fcf_df = merged_df # Use merged_df which now contains all columns
        # EBITDA calculation should use 'nopat' now
        if 'nopat' in fcf_df.columns and 'depreciation_amortization' in fcf_df.columns:
             tax_rate = self.assumptions.get('effective_tax_rate', 0.25)
             if abs(1 - tax_rate) < 1e-9: # Check if tax_rate is effectively 1 (or 100%)
                  print("Warning: Tax rate is 100% or invalid, cannot calculate EBIT from NOPAT accurately. Using EBIT + D&A for EBITDA approximation.")
                  if 'ebit' in fcf_df.columns:
                       fcf_df['ebitda'] = fcf_df['ebit'] + fcf_df['depreciation_amortization']
                  else:
                       print("Warning: EBIT column not found, cannot approximate EBITDA.")
                       fcf_df['ebitda'] = 0
             else:
                  # Back-calculate EBIT from NOPAT: EBIT = NOPAT / (1 - Tax Rate)
                  fcf_df['calculated_ebit_from_nopat'] = fcf_df['nopat'] / (1 - tax_rate)
                  fcf_df['ebitda'] = fcf_df['calculated_ebit_from_nopat'] + fcf_df['depreciation_amortization']
                  # Drop the temporary calculated_ebit_from_nopat column
                  if 'calculated_ebit_from_nopat' in fcf_df.columns:
                      fcf_df = fcf_df.drop(columns=['calculated_ebit_from_nopat'])
        elif 'ebit' in fcf_df.columns and 'depreciation_amortization' in fcf_df.columns:
             print("Warning: NOPAT not found (should not happen if income statement ran correctly), approximating EBITDA using EBIT + D&A.")
             fcf_df['ebitda'] = fcf_df['ebit'] + fcf_df['depreciation_amortization']
        else:
             print("Warning: Cannot calculate EBITDA due to missing NOPAT/EBIT or D&A columns.")
             fcf_df['ebitda'] = 0 

        self.forecasted_statements['fcf_components'] = fcf_df 
        print("FCF components forecast (with EBITDA) completed:\n", fcf_df)
        return fcf_df


    def get_full_forecast(self) -> Dict[str, pd.DataFrame]:
        self.predict_revenue()
        self.predict_income_statement_items()
        self.predict_balance_sheet_and_cf_items() 
        return self.forecasted_statements
