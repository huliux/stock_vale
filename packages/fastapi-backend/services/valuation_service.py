import os
import logging
import traceback
import pandas as pd
from typing import Dict, Any, Optional, Tuple, List
from decimal import Decimal, InvalidOperation

# 假设模型和计算器在项目的根目录或可访问的路径
# 需要根据实际项目结构调整这些导入
try:
    from data_processor import DataProcessor
    from financial_forecaster import FinancialForecaster
    from wacc_calculator import WaccCalculator
    from terminal_value_calculator import TerminalValueCalculator
    from present_value_calculator import PresentValueCalculator
    from equity_bridge_calculator import EquityBridgeCalculator
    # 假设 DcfForecastDetails 模型定义在 api.models
    from api.models import DcfForecastDetails, StockValuationRequest # Added StockValuationRequest
    from api.sensitivity_models import SensitivityAnalysisRequest, SensitivityAnalysisResult, SensitivityAxisInput, MetricType, SUPPORTED_SENSITIVITY_OUTPUT_METRICS
    from api.utils import regenerate_axis_if_needed # For axis regeneration
except ImportError as e:
    # 处理潜在的导入错误，例如在不同环境运行时
    logging.error(f"Error importing modules in valuation_service.py: {e}")
    # Define placeholders if necessary for the script to be parsable,
    # though runtime will likely fail if imports are truly missing.
    class DataProcessor: pass #type: ignore
    class FinancialForecaster: pass #type: ignore
    class WaccCalculator: pass #type: ignore
    class TerminalValueCalculator: pass #type: ignore
    class PresentValueCalculator: pass #type: ignore
    class EquityBridgeCalculator: pass #type: ignore
    class DcfForecastDetails: pass #type: ignore
    class StockValuationRequest: pass #type: ignore
    class SensitivityAnalysisRequest: pass #type: ignore
    class SensitivityAnalysisResult: pass #type: ignore
    class SensitivityAxisInput: pass #type: ignore
    class MetricType: #type: ignore
        WACC = "wacc"
        TERMINAL_GROWTH_RATE = "perpetual_growth_rate"
        TERMINAL_EBITDA_MULTIPLE = "exit_multiple"
    SUPPORTED_SENSITIVITY_OUTPUT_METRICS = None #type: ignore
    def regenerate_axis_if_needed(*args, **kwargs): pass #type: ignore


logger = logging.getLogger(__name__)

# ValuationService class to encapsulate valuation logic
class ValuationService:
    def __init__(self, 
                 processed_data_container: DataProcessor, 
                 wacc_calculator: WaccCalculator,
                 logger_override: Optional[logging.Logger] = None):
        self.processed_data_container = processed_data_container
        self.wacc_calculator = wacc_calculator
        self.logger = logger_override if logger_override else logger # Use override if provided

    def run_single_valuation(self, # Now a method of ValuationService
        request_dict: Dict[str, Any],
        total_shares_actual: Optional[float],
        override_wacc: Optional[float] = None,
        override_exit_multiple: Optional[float] = None,
        override_perpetual_growth_rate: Optional[float] = None
    ) -> Tuple[Optional[DcfForecastDetails], Optional[pd.DataFrame], List[str]]: # Return signature remains the same externally for now
        """
        执行单次估值计算的核心逻辑。
        接收请求参数字典、总股本，以及可选的覆盖参数。
        使用服务实例中的 processed_data_container 和 wacc_calculator。
        返回 DCF 详情、预测 DataFrame 和警告列表。
        """
        local_warnings = []
        final_forecast_df = None
        dcf_details = None

        try:
            self.logger.debug("  Running single valuation: Step 3 - Forecasting financials...")
            # Extract forecast assumptions, excluding keys not relevant for FinancialForecaster
            forecast_assumptions_raw = {k: v for k, v in request_dict.items() if k not in ['ts_code', 'market', 'valuation_date', 'sensitivity_analysis']}
            
            # Create a mutable copy for potential key mapping
            forecast_assumptions = forecast_assumptions_raw.copy()

            # Map cagr_decay_rate to revenue_cagr_decay_rate for FinancialForecaster
            if 'cagr_decay_rate' in forecast_assumptions and forecast_assumptions['cagr_decay_rate'] is not None:
                self.logger.debug(f"Mapping cagr_decay_rate ({forecast_assumptions['cagr_decay_rate']}) to revenue_cagr_decay_rate.")
                forecast_assumptions['revenue_cagr_decay_rate'] = forecast_assumptions.pop('cagr_decay_rate')

            # --- Comprehensive mapping for other forecast assumptions ---
            self.logger.debug(f"Original forecast_assumptions from API: {forecast_assumptions_raw}")

            # Helper to pop and set if key exists
            def map_key(current_assumptions, api_key, forecaster_key):
                if api_key in current_assumptions and current_assumptions[api_key] is not None:
                    current_assumptions[forecaster_key] = current_assumptions.pop(api_key)
                    self.logger.debug(f"Mapped API key '{api_key}' to Forecaster key '{forecaster_key}' with value: {current_assumptions[forecaster_key]}")
                elif api_key in current_assumptions and current_assumptions[api_key] is None: # Pop if None to avoid sending None with old key
                    current_assumptions.pop(api_key)


            # Operating Margin
            map_key(forecast_assumptions, 'op_margin_forecast_mode', 'operating_margin_forecast_mode')
            map_key(forecast_assumptions, 'target_operating_margin', 'operating_margin_target_value') # Corrected forecaster key
            map_key(forecast_assumptions, 'op_margin_transition_years', 'op_margin_transition_years') # Key matches, but pop to be clean

            # SGA & RD Ratios (API sends combined, Forecaster expects separate)
            # We'll apply the combined mode and years to both SGA and RD.
            # The target combined ratio will be used for both individual target ratios.
            sga_rd_mode = forecast_assumptions.pop('sga_rd_ratio_forecast_mode', None)
            sga_rd_target = forecast_assumptions.pop('target_sga_rd_to_revenue_ratio', None)
            sga_rd_trans_years = forecast_assumptions.pop('sga_rd_transition_years', None)

            if sga_rd_mode is not None:
                forecast_assumptions['sga_to_revenue_ratio_forecast_mode'] = sga_rd_mode
                forecast_assumptions['rd_to_revenue_ratio_forecast_mode'] = sga_rd_mode
                self.logger.debug(f"Mapped sga_rd_ratio_forecast_mode to sga_to_revenue_ratio_forecast_mode and rd_to_revenue_ratio_forecast_mode with value: {sga_rd_mode}")
            if sga_rd_target is not None:
                # FinancialForecaster will try target_sga_to_revenue_ratio and target_rd_to_revenue_ratio
                forecast_assumptions['target_sga_to_revenue_ratio'] = sga_rd_target 
                forecast_assumptions['target_rd_to_revenue_ratio'] = sga_rd_target
                self.logger.debug(f"Mapped target_sga_rd_to_revenue_ratio to target_sga_to_revenue_ratio and target_rd_to_revenue_ratio with value: {sga_rd_target}")
            if sga_rd_trans_years is not None:
                forecast_assumptions['sga_transition_years'] = sga_rd_trans_years
                forecast_assumptions['rd_transition_years'] = sga_rd_trans_years
                self.logger.debug(f"Mapped sga_rd_transition_years to sga_transition_years and rd_transition_years with value: {sga_rd_trans_years}")

            # D&A to Revenue Ratio
            map_key(forecast_assumptions, 'da_ratio_forecast_mode', 'da_to_revenue_ratio_forecast_mode')
            map_key(forecast_assumptions, 'target_da_to_revenue_ratio', 'target_da_to_revenue_ratio') # Forecaster will find target_metric_name
            map_key(forecast_assumptions, 'da_ratio_transition_years', 'da_ratio_transition_years') # Key matches

            # Capex to Revenue Ratio
            map_key(forecast_assumptions, 'capex_ratio_forecast_mode', 'capex_to_revenue_ratio_forecast_mode')
            map_key(forecast_assumptions, 'target_capex_to_revenue_ratio', 'target_capex_to_revenue_ratio') # Forecaster will find target_metric_name
            map_key(forecast_assumptions, 'capex_ratio_transition_years', 'capex_ratio_transition_years') # Key matches

            # NWC Days (AR, Inventory, AP)
            nwc_days_mode = forecast_assumptions.pop('nwc_days_forecast_mode', None)
            nwc_days_trans_years = forecast_assumptions.pop('nwc_days_transition_years', None)
            if nwc_days_mode is not None:
                forecast_assumptions['accounts_receivable_days_forecast_mode'] = nwc_days_mode
                forecast_assumptions['inventory_days_forecast_mode'] = nwc_days_mode
                forecast_assumptions['accounts_payable_days_forecast_mode'] = nwc_days_mode
                self.logger.debug(f"Mapped nwc_days_forecast_mode to individual day forecast modes with value: {nwc_days_mode}")
            if nwc_days_trans_years is not None:
                 forecast_assumptions['nwc_days_transition_years'] = nwc_days_trans_years # Forecaster uses this common key
                 self.logger.debug(f"Set nwc_days_transition_years for Forecaster with value: {nwc_days_trans_years}")
            map_key(forecast_assumptions, 'target_accounts_receivable_days', 'target_accounts_receivable_days')
            map_key(forecast_assumptions, 'target_inventory_days', 'target_inventory_days')
            map_key(forecast_assumptions, 'target_accounts_payable_days', 'target_accounts_payable_days')

            # Other NWC Ratios (OCA, OCL)
            other_nwc_mode = forecast_assumptions.pop('other_nwc_ratio_forecast_mode', None)
            other_nwc_trans_years = forecast_assumptions.pop('other_nwc_ratio_transition_years', None)
            if other_nwc_mode is not None:
                forecast_assumptions['other_current_assets_to_revenue_ratio_forecast_mode'] = other_nwc_mode
                forecast_assumptions['other_current_liabilities_to_revenue_ratio_forecast_mode'] = other_nwc_mode
                self.logger.debug(f"Mapped other_nwc_ratio_forecast_mode to individual ratio forecast modes with value: {other_nwc_mode}")
            if other_nwc_trans_years is not None:
                forecast_assumptions['other_nwc_ratio_transition_years'] = other_nwc_trans_years # Forecaster uses this common key
                self.logger.debug(f"Set other_nwc_ratio_transition_years for Forecaster with value: {other_nwc_trans_years}")
            map_key(forecast_assumptions, 'target_other_current_assets_to_revenue_ratio', 'target_other_current_assets_to_revenue_ratio')
            map_key(forecast_assumptions, 'target_other_current_liabilities_to_revenue_ratio', 'target_other_current_liabilities_to_revenue_ratio')

            # Effective Tax Rate
            map_key(forecast_assumptions, 'target_effective_tax_rate', 'effective_tax_rate_target')
            # Transition years for tax rate uses a general 'transition_years' key in forecaster if present, or defaults to forecast_years.
            # If a specific transition year for tax is desired from API, it would need a dedicated API field and mapping here.
            # For now, we rely on the forecaster's default handling or a general 'transition_years' if we decide to pass one.
            # Example: if request_dict.get('tax_transition_years'): forecast_assumptions['transition_years'] = request_dict['tax_transition_years']
            # For now, let's assume the forecaster's default (using self.forecast_years if 'transition_years' is not in assumptions) is acceptable for tax rate transition.

            self.logger.debug(f"Final forecast_assumptions for FinancialForecaster: {forecast_assumptions}")
            # --- End of comprehensive mapping ---
            
            last_actual_revenue = None
            if 'income_statement' in self.processed_data_container.processed_data and \
               not self.processed_data_container.processed_data['income_statement'].empty and \
               'revenue' in self.processed_data_container.processed_data['income_statement'].columns:
                last_actual_revenue = self.processed_data_container.processed_data['income_statement']['revenue'].iloc[-1]
            
            if last_actual_revenue is None or pd.isna(last_actual_revenue):
                 raise ValueError("无法获取有效的上一年度实际收入用于财务预测。")

            financial_forecaster = FinancialForecaster(
                last_actual_revenue=last_actual_revenue,
                historical_ratios=self.processed_data_container.get_historical_ratios(),
                forecast_assumptions=forecast_assumptions # Use the potentially modified forecast_assumptions
            )
            final_forecast_df = financial_forecaster.get_full_forecast()
            if final_forecast_df is None or final_forecast_df.empty or 'ufcf' not in final_forecast_df.columns:
                raise ValueError("财务预测失败或未能生成 UFCF。")
            self.logger.debug("  Single valuation: Financial forecast complete.")

            self.logger.debug("  Running single valuation: Step 4 - Calculating WACC...")
            wacc = None
            cost_of_equity = None
            if override_wacc is not None:
                wacc = override_wacc
                cost_of_equity = None # Simplified when WACC is overridden
                self.logger.debug(f"  Using overridden WACC: {wacc:.4f}")
            else:
                # Prepare params for WaccCalculator, including the direct discount_rate if available
                wacc_params_input = {
                    k: request_dict.get(k) for k in 
                    ['target_debt_ratio', 'cost_of_debt', 'risk_free_rate', 
                     'beta', 'market_risk_premium', 'size_premium', 'discount_rate'] # Added 'discount_rate'
                }
                wacc_params_input['tax_rate'] = request_dict.get('target_effective_tax_rate')
                
                # Ensure beta is sourced correctly if not in request_dict
                if wacc_params_input.get('beta') is None:
                    beta_from_metrics = self.processed_data_container.get_latest_metrics().get('beta')
                    if beta_from_metrics is not None:
                        wacc_params_input['beta'] = beta_from_metrics
                
                wacc_params_filtered = {k: v for k, v in wacc_params_input.items() if v is not None}
                current_wacc_weight_mode = request_dict.get('wacc_weight_mode', "target")
                
                self.logger.debug(f"  Params for WACC calculation: {wacc_params_filtered}")
                wacc, cost_of_equity = self.wacc_calculator.get_wacc_and_ke(
                    params=wacc_params_filtered, # This now includes 'discount_rate' if provided
                    wacc_weight_mode=current_wacc_weight_mode
                )
                if wacc is None:
                    raise ValueError(f"WACC 计算失败。Ke: {cost_of_equity}")
                self.logger.debug(f"  WACC calculated: {wacc:.4f} (mode: {current_wacc_weight_mode}), Ke: {cost_of_equity:.4f}")

            self.logger.debug("  Running single valuation: Step 5 - Calculating Terminal Value...")
            base_rf = request_dict.get('risk_free_rate') or self.wacc_calculator.default_risk_free_rate
            tv_calculator = TerminalValueCalculator(risk_free_rate=float(base_rf))

            tv_method = request_dict.get('terminal_value_method', 'exit_multiple')
            exit_multiple_to_use = override_exit_multiple if override_exit_multiple is not None else request_dict.get('exit_multiple')
            perpetual_growth_rate_to_use = override_perpetual_growth_rate if override_perpetual_growth_rate is not None else request_dict.get('perpetual_growth_rate')

            if tv_method == 'exit_multiple' and (exit_multiple_to_use is None or exit_multiple_to_use <= 0):
                exit_multiple_to_use = float(os.getenv('DEFAULT_EXIT_MULTIPLE', '8.0'))
                local_warnings.append(f"敏感性分析中退出乘数无效或未提供，使用默认值: {exit_multiple_to_use}")
            elif tv_method == 'perpetual_growth' and perpetual_growth_rate_to_use is None:
                 perpetual_growth_rate_to_use = float(os.getenv('DEFAULT_PERPETUAL_GROWTH_RATE', '0.025'))
                 local_warnings.append(f"敏感性分析中永续增长率无效或未提供，使用默认值: {perpetual_growth_rate_to_use:.3f}")

            terminal_value, tv_error = tv_calculator.calculate_terminal_value(
                last_forecast_year_data=final_forecast_df.iloc[-1], wacc=wacc,
                method=tv_method,
                exit_multiple=exit_multiple_to_use if tv_method == 'exit_multiple' else None,
                perpetual_growth_rate=perpetual_growth_rate_to_use if tv_method == 'perpetual_growth' else None
            )
            if tv_error: raise ValueError(f"终值计算失败: {tv_error}")
            self.logger.debug(f"  Terminal Value calculated: {terminal_value:.2f} using method {tv_method}")

            self.logger.debug("  Running single valuation: Step 6 - Calculating Present Values...")
            pv_calculator = PresentValueCalculator()
            # pv_calculator.calculate_present_values now returns 4 items
            pv_forecast_ufcf, pv_terminal_value, forecast_df_with_pv, pv_error = pv_calculator.calculate_present_values(
                forecast_df=final_forecast_df, terminal_value=terminal_value, wacc=wacc
            )
            if pv_error: raise ValueError(f"现值计算失败: {pv_error}")
            
            # Update final_forecast_df to the one that includes 'pv_ufcf' column
            if forecast_df_with_pv is not None:
                final_forecast_df = forecast_df_with_pv
                self.logger.debug("  Updated final_forecast_df with pv_ufcf column from PresentValueCalculator.")
            
            self.logger.debug(f"  Present Values calculated. PV(UFCF): {pv_forecast_ufcf:.2f}, PV(TV): {pv_terminal_value:.2f}")

            self.logger.debug("  Running single valuation: Step 7 - Calculating Equity Value...")
            enterprise_value = pv_forecast_ufcf + pv_terminal_value
            equity_bridge_calculator = EquityBridgeCalculator()
            net_debt, equity_value, value_per_share, eb_error = equity_bridge_calculator.calculate_equity_value(
                enterprise_value=enterprise_value,
                latest_balance_sheet=self.processed_data_container.get_latest_balance_sheet(),
                total_shares=total_shares_actual
            )
            if eb_error: local_warnings.append(f"股权价值桥梁计算警告: {eb_error}")
            equity_value_str = f"{equity_value:.2f}" if equity_value is not None else "N/A"
            value_per_share_str = f"{value_per_share:.2f}" if value_per_share is not None else "N/A"
            self.logger.debug(f"  Equity Value calculated: {equity_value_str}, Value/Share: {value_per_share_str}")

            self.logger.debug("  Running single valuation: Step 8 - Building DCF results object...")
            dcf_details = DcfForecastDetails(
                enterprise_value=enterprise_value, equity_value=equity_value, value_per_share=value_per_share,
                net_debt=net_debt, pv_forecast_ufcf=pv_forecast_ufcf, pv_terminal_value=pv_terminal_value,
                terminal_value=terminal_value, wacc_used=wacc, cost_of_equity_used=cost_of_equity,
                terminal_value_method_used=tv_method,
                exit_multiple_used=exit_multiple_to_use if tv_method == 'exit_multiple' else None,
                perpetual_growth_rate_used=perpetual_growth_rate_to_use if tv_method == 'perpetual_growth' else None,
                forecast_period_years=request_dict.get('forecast_years', 5)
            )
            self.logger.debug("  Single valuation run completed successfully.")
            return dcf_details, final_forecast_df, local_warnings

        except Exception as e:
            self.logger.error(f"Error during single valuation run: {e}\n{traceback.format_exc()}")
            local_warnings.append(f"单次估值计算失败: {str(e)}")
            return None, None, local_warnings

    def run_sensitivity_analysis(
        self,
        sa_request_model: SensitivityAnalysisRequest,
        base_dcf_details: DcfForecastDetails,
        base_request_dict: Dict[str, Any],
        total_shares_actual: Optional[float],
        base_latest_metrics: Dict[str, Any]
    ) -> Tuple[Optional[SensitivityAnalysisResult], List[str]]:
        self.logger.info("Starting sensitivity analysis in service...")
        sensitivity_warnings: List[str] = []
        
        row_param = sa_request_model.row_axis.parameter_name
        col_param = sa_request_model.column_axis.parameter_name

        # Axis regeneration using the utility function
        actual_row_values = regenerate_axis_if_needed(
            axis_input=sa_request_model.row_axis,
            base_details=base_dcf_details,
            param_name=row_param,
            is_row_axis=True,
            base_req_dict=base_request_dict,
            logger_obj=self.logger,
            sensitivity_warnings_list=sensitivity_warnings
        )
        actual_col_values = regenerate_axis_if_needed(
            axis_input=sa_request_model.column_axis,
            base_details=base_dcf_details,
            param_name=col_param,
            is_row_axis=False,
            base_req_dict=base_request_dict,
            logger_obj=self.logger,
            sensitivity_warnings_list=sensitivity_warnings
        )

        if not actual_row_values or not actual_col_values:
            self.logger.error("Sensitivity analysis cannot proceed with empty axis values after regeneration.")
            sensitivity_warnings.append("敏感性分析轴值在重新生成后为空，无法继续。")
            return None, sensitivity_warnings

        output_metrics_to_calculate = list(SUPPORTED_SENSITIVITY_OUTPUT_METRICS.__args__) # type: ignore
        result_tables: Dict[str, List[List[Optional[float]]]] = {
            metric: [[None for _ in actual_col_values] for _ in actual_row_values]
            for metric in output_metrics_to_calculate
        }

        for i, row_val in enumerate(actual_row_values):
            for j, col_val in enumerate(actual_col_values):
                self.logger.debug(f"  Running sensitivity case: {row_param}={row_val}, {col_param}={col_val}")
                temp_request_dict = base_request_dict.copy()
                override_wacc = None
                override_exit_multiple = None
                override_perpetual_growth_rate = None

                if row_param == MetricType.WACC.value: override_wacc = float(row_val)
                elif row_param == MetricType.TERMINAL_EBITDA_MULTIPLE.value: override_exit_multiple = float(row_val)
                elif row_param == MetricType.TERMINAL_GROWTH_RATE.value: override_perpetual_growth_rate = float(row_val)

                if col_param == MetricType.WACC.value: override_wacc = float(col_val)
                elif col_param == MetricType.TERMINAL_EBITDA_MULTIPLE.value: override_exit_multiple = float(col_val)
                elif col_param == MetricType.TERMINAL_GROWTH_RATE.value: override_perpetual_growth_rate = float(col_val)
                
                if override_exit_multiple is not None:
                    temp_request_dict['terminal_value_method'] = 'exit_multiple'
                    temp_request_dict['perpetual_growth_rate'] = None
                elif override_perpetual_growth_rate is not None:
                    temp_request_dict['terminal_value_method'] = 'perpetual_growth'
                    temp_request_dict['exit_multiple'] = None

                dcf_details_sens, _, run_warnings_sens = self.run_single_valuation(
                    request_dict=temp_request_dict,
                    total_shares_actual=total_shares_actual,
                    override_wacc=override_wacc,
                    override_exit_multiple=override_exit_multiple,
                    override_perpetual_growth_rate=override_perpetual_growth_rate
                )
                sensitivity_warnings.extend(run_warnings_sens)
                
                if dcf_details_sens:
                    result_tables["value_per_share"][i][j] = dcf_details_sens.value_per_share
                    result_tables["enterprise_value"][i][j] = dcf_details_sens.enterprise_value
                    result_tables["equity_value"][i][j] = dcf_details_sens.equity_value
                    if dcf_details_sens.enterprise_value and dcf_details_sens.enterprise_value != 0:
                        result_tables["tv_ev_ratio"][i][j] = (dcf_details_sens.pv_terminal_value or 0) / dcf_details_sens.enterprise_value
                    else:
                        result_tables["tv_ev_ratio"][i][j] = None
                    
                    result_tables["dcf_implied_pe"][i][j] = dcf_details_sens.dcf_implied_diluted_pe

                    base_actual_ebitda = base_latest_metrics.get('latest_actual_ebitda')
                    if base_actual_ebitda and isinstance(base_actual_ebitda, Decimal) and base_actual_ebitda > Decimal('0'):
                        if dcf_details_sens.enterprise_value is not None:
                            try:
                                result_tables["ev_ebitda"][i][j] = float(Decimal(str(dcf_details_sens.enterprise_value)) / base_actual_ebitda)
                            except (InvalidOperation, TypeError, ZeroDivisionError) as e_calc:
                                self.logger.warning(f"Error calculating EV/EBITDA for sensitivity: EV={dcf_details_sens.enterprise_value}, BaseEBITDA={base_actual_ebitda}. Error: {e_calc}")
                                result_tables["ev_ebitda"][i][j] = None
                        else:
                            result_tables["ev_ebitda"][i][j] = None
                    else:
                        result_tables["ev_ebitda"][i][j] = None
                        # Warning already added by regenerate_axis_if_needed or main logic if base_actual_ebitda is problematic
                else:
                    self.logger.warning(f"  Sensitivity case failed for {row_param}={row_val}, {col_param}={col_val}")

        sensitivity_result_obj = SensitivityAnalysisResult(
            row_parameter=row_param,
            column_parameter=col_param,
            row_values=actual_row_values,
            column_values=actual_col_values,
            result_tables=result_tables
        )
        self.logger.info("Sensitivity analysis in service complete.")
        return sensitivity_result_obj, sensitivity_warnings
