import pytest
from fastapi.testclient import TestClient
import pandas as pd
from decimal import Decimal
from unittest.mock import MagicMock, patch, AsyncMock, PropertyMock

# Import the FastAPI app instance
from api.main import app
from api.models import StockValuationRequest # Import request model - Corrected Name

client = TestClient(app)

# --- Test Data ---
MOCK_TS_CODE = '000001.SZ'
MOCK_STOCK_BASIC_INFO = {
    'ts_code': MOCK_TS_CODE,
    'name': '平安银行',
    'industry': '银行',
    'list_date': '19910403',
    'exchange': 'SZSE',
    'currency': 'CNY',
    'latest_pe_ttm': Decimal('10.5'),
    'latest_pb_mrq': Decimal('1.2'),
    'total_shares': Decimal('19405918000'), # Example total shares
    'free_float_shares': Decimal('18000000000')
}
MOCK_LATEST_PRICE = Decimal('15.0')

# Raw financial data as returned by DataFetcher
MOCK_RAW_FINANCIAL_DATA = {
    'income_statement': pd.DataFrame({
        'end_date': pd.to_datetime(['2021-12-31', '2022-12-31', '2023-12-31']),
        'total_revenue': [100, 120, 150],
        'revenue': [100, 120, 150], # Added 'revenue' column for the check in ValuationService
        'oper_cost': [60, 70, 80],
        'income_tax': [10, 12, 15],
        'n_income': [30, 38, 55], # Net Income
        'ebit': [40, 50, 70] # Assuming EBIT is available
    }),
    'balance_sheet': pd.DataFrame({
        'end_date': pd.to_datetime(['2020-12-31', '2021-12-31', '2022-12-31', '2023-12-31']),
        'accounts_receiv_bill': [10, 12, 15, 18],
        'inventories': [20, 22, 25, 30],
        'accounts_pay': [15, 18, 20, 22],
        'total_cur_assets': [100,110,120,130],
        'total_cur_liab': [50,55,60,65],
        'money_cap': [10,12,15,20], # Cash and equivalents
        'st_borr': [5,6,7,8], # Short term debt
        'lt_borr': [20,22,25,30], # Long term debt
        'minority_int': [1,1.2,1.5,2], # Minority interest
        'preferred_stk_val': [0,0,0,0] # Preferred equity
    }),
    'cash_flow': pd.DataFrame({
        'end_date': pd.to_datetime(['2021-12-31', '2022-12-31', '2023-12-31']),
        'depr_fa_coga_dpba': [5, 6, 7], # Depreciation
        'amort_intang_assets': [1, 1, 2], # Amortization
        'lt_amort_deferred_exp': [0,1,1],
        'c_pay_acq_const_fiolta': [10,12,15] # Capex
    })
}
MOCK_LATEST_BS_INFO = { # As returned by DataFetcher.get_latest_balance_sheet_info
    'cash_and_equivalents': Decimal('20'),
    'short_term_debt': Decimal('8'),
    'long_term_debt': Decimal('30'),
    'minority_interest': Decimal('2'),
    'preferred_equity': Decimal('0'),
    'net_debt': Decimal('18') # 8 + 30 - 20
}

MOCK_PROCESSED_DATA_FOR_FORECASTER = MOCK_RAW_FINANCIAL_DATA # Simplified for this mock
MOCK_HISTORICAL_RATIOS = {
    'cogs_to_revenue_ratio': Decimal('0.6'),
    'sga_to_revenue_ratio': Decimal('0.1'),
    'rd_to_revenue_ratio': Decimal('0.05'),
    'da_to_revenue_ratio': Decimal('0.05'),
    'capex_to_revenue_ratio': Decimal('0.08'),
    'effective_tax_rate': Decimal('0.25'),
    'accounts_receivable_days': Decimal('75'),
    'inventory_days': Decimal('180'),
    'accounts_payable_days': Decimal('90'),
    'other_current_assets_to_revenue_ratio': Decimal('0.05'),
    'other_current_liabilities_to_revenue_ratio': Decimal('0.03'),
    'last_actual_nwc': Decimal('50'),
    'last_actual_cogs': Decimal('80'), # from IS 2023
    'historical_revenue_cagr': Decimal('0.2247') # (150/100)^(1/2)-1
}
# Mock for DataProcessor.get_latest_metrics()
MOCK_LATEST_METRICS = {
    'pe': MOCK_STOCK_BASIC_INFO['latest_pe_ttm'],
    'pb': MOCK_STOCK_BASIC_INFO['latest_pb_mrq'],
    'beta': Decimal('1.1') # Example beta
}
MOCK_DETAILED_FORECAST_TABLE = pd.DataFrame({
    'year': [1, 2, 3, 4, 5],
    'revenue': [Decimal('183.71'), Decimal('213.65'), Decimal('243.60'), Decimal('273.54'), Decimal('303.49')],
    'ufcf': [Decimal('20'), Decimal('22'), Decimal('25'), Decimal('28'), Decimal('30')] # Renamed column to ufcf
    # Add other necessary columns if they are directly used by calculators
})

MOCK_LLM_ANALYSIS = {"summary": "Mocked LLM analysis summary.", "rating": "Buy", "confidence": "High"}

DEFAULT_VALUATION_REQUEST_PAYLOAD = {
    "ts_code": MOCK_TS_CODE,
    "risk_free_rate": 0.025,
    "market_risk_premium": 0.06,
    "beta": 1.1,
    "cost_of_debt": 0.045,
    "tax_rate_for_wacc": 0.25, # This is corp tax rate for WACC, not necessarily historical effective
    "debt_to_equity_target": 0.5,
    "prediction_mode": "historical_median",
    "forecast_years": 5,
    "revenue_cagr_decay_rate": 0.01,
    "terminal_growth_rate": 0.02,
    "terminal_ev_ebitda_multiple": 8.0,
    "terminal_value_method": "perpetual_growth", # Corrected method name
    # Target ratios (optional, used if prediction_mode is 'transition_to_target')
    "effective_tax_rate_target": 0.25,
    "cogs_to_revenue_target": 0.6,
    "sga_to_revenue_target": 0.1,
    "rd_to_revenue_target": 0.05,
    "da_to_revenue_target": 0.05,
    "capex_to_revenue_target": 0.08,
    "ar_days_target": 75,
    "inventory_days_target": 180,
    "ap_days_target": 90,
    "other_ca_to_revenue_target": 0.05,
    "other_cl_to_revenue_target": 0.03,
    "transition_years": 3
}


# --- Tests ---

def test_read_root():
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    # Correct the expected message based on api/main.py
    assert response.json() == {"message": "Welcome to the Stock Valuation API (Streamlit Backend)"}

# Adjusted patch targets based on ValuationService structure
@patch("api.main.AshareDataFetcher") # Assuming DI in api.main creates this
@patch("api.main.DataProcessor")    # Assuming DI in api.main creates this
@patch("api.main.WaccCalculator")     # Assuming DI in api.main creates this
@patch("services.valuation_service.FinancialForecaster") # Instantiated in ValuationService
@patch("services.valuation_service.TerminalValueCalculator") # Instantiated in ValuationService
@patch("services.valuation_service.PresentValueCalculator") # Instantiated in ValuationService
@patch("services.valuation_service.EquityBridgeCalculator") # Instantiated in ValuationService
@patch("api.main.call_llm_api")
def test_calculate_valuation_success(
    InjectedMockCallLLM, InjectedMockEquityBridge, InjectedMockPV, InjectedMockTV,
    InjectedMockFinancialForecaster, InjectedMockWACC, InjectedMockDataProcessor, InjectedMockAshareDataFetcher
):
    """Test the valuation endpoint with mocked dependencies (new structure)."""

    # --- Configure Mocks ---
    # DataFetcher
    mock_fetcher_instance = InjectedMockAshareDataFetcher.return_value
    mock_fetcher_instance.get_stock_basic_info.return_value = MOCK_STOCK_BASIC_INFO
    mock_fetcher_instance.get_latest_price.return_value = MOCK_LATEST_PRICE
    mock_fetcher_instance.get_raw_financial_data.return_value = MOCK_RAW_FINANCIAL_DATA
    mock_fetcher_instance.get_latest_balance_sheet_info.return_value = MOCK_LATEST_BS_INFO
    # Mock get_latest_total_shares to return value in 亿股, explicitly convert to float
    mock_fetcher_instance.get_latest_total_shares.return_value = float(MOCK_STOCK_BASIC_INFO['total_shares'] / 100000000)
    mock_fetcher_instance.get_latest_pe_pb.return_value = {'pe': MOCK_STOCK_BASIC_INFO['latest_pe_ttm'], 'pb': MOCK_STOCK_BASIC_INFO['latest_pb_mrq']} # Added this mock

    # DataProcessor
    # DataProcessor
    mock_processor_instance = InjectedMockDataProcessor.return_value
    mock_processor_instance.processed_data = MOCK_PROCESSED_DATA_FOR_FORECASTER # Set the attribute directly
    mock_processor_instance.get_processed_data.return_value = MOCK_PROCESSED_DATA_FOR_FORECASTER
    mock_processor_instance.clean_data.return_value = MOCK_PROCESSED_DATA_FOR_FORECASTER # Cleaned data
    mock_processor_instance.get_base_financial_statement_date = MagicMock(return_value='2023-12-31') # Corrected method name
    # mock_processor_instance.base_report_date = '2023-12-31' # Attribute likely not needed if method is called
    # Corrected mock target method name & using explicit mock object
    mock_get_hist_ratios = MagicMock(return_value=MOCK_HISTORICAL_RATIOS)
    mock_processor_instance.get_historical_ratios = mock_get_hist_ratios
    # mock_processor_instance.get_historical_ratios.return_value = MOCK_HISTORICAL_RATIOS # Original way
    mock_processor_instance.get_basic_info.return_value = MOCK_STOCK_BASIC_INFO # After processing
    mock_processor_instance.get_latest_metrics.return_value = MOCK_LATEST_METRICS # Added mock
    mock_processor_instance.get_latest_balance_sheet_info.return_value = MOCK_LATEST_BS_INFO # After processing
    # Mock the get_warnings() method instead of the attribute
    mock_processor_instance.get_warnings.return_value = ["Mock warning 1", "Mock warning 2"]

    # FinancialForecaster
    mock_forecaster_instance = InjectedMockFinancialForecaster.return_value
    # get_full_forecast should return the DataFrame directly
    mock_forecaster_instance.get_full_forecast.return_value = MOCK_DETAILED_FORECAST_TABLE 
    mock_forecaster_instance.get_last_actual_revenue.return_value = Decimal('150') # Explicitly mock this

    # WACCCalculator
    mock_wacc_instance = InjectedMockWACC.return_value
    # Mock the correct method called in api/main.py
    mock_wacc_instance.get_wacc_and_ke.return_value = (Decimal('0.085'), Decimal('0.10')) # Return tuple (wacc, ke)

    # FCFCalculator is mocked as part of FinancialForecaster if FinancialForecaster is mocked.
    # No need to mock FcfCalculator separately here.
    # The MOCK_DETAILED_FORECAST_TABLE should already include 'free_cash_flow' if it's the output of FinancialForecaster.

    # TerminalValueCalculator
    mock_tv_instance = InjectedMockTV.return_value
    # Return None for the error part in the success case
    mock_tv_instance.calculate_terminal_value.return_value = (Decimal('500'), None) 

    # PresentValueCalculator
    mock_pv_instance = InjectedMockPV.return_value
    # Return tuple (pv_ufcf, pv_tv, error) - use floats as in the other test
    mock_pv_instance.calculate_present_values.return_value = (400.0, 931.38, None) 

    # EquityBridgeCalculator
    mock_eb_instance = InjectedMockEquityBridge.return_value
    # Return tuple (net_debt, equity_value, value_per_share, error)
    mock_eb_instance.calculate_equity_value.return_value = (Decimal('1500'), Decimal('350'), Decimal('18.04'), None) 

    # LLM Call
    # Return only the summary string as expected by the model
    InjectedMockCallLLM.return_value = MOCK_LLM_ANALYSIS["summary"] 
    
    # --- Make the request ---
    response = client.post("/api/v1/valuation", json=DEFAULT_VALUATION_REQUEST_PAYLOAD)

    # --- Assertions ---
    assert response.status_code == 200, f"Response content: {response.content}"
    data = response.json()

    # Use the correct key 'stock_info' based on StockValuationResponse model
    assert data["stock_info"]["name"] == "平安银行" 
    assert data["stock_info"]["latest_pe_ttm"] == 10.5 # Pydantic converts Decimal to float for JSON
    
    results = data["valuation_results"]
    # Updated assertions to match ValuationResultsContainer and DcfForecastDetails structure
    assert results["dcf_forecast_details"]["value_per_share"] == 18.04
    assert results["dcf_forecast_details"]["wacc_used"] == 0.085
    assert results["current_pe"] == 10.5
    assert results["current_pb"] == 1.2
    assert results["llm_analysis_summary"] == "Mocked LLM analysis summary."
    
    assert "detailed_forecast_table" in results # Check within results container
    assert len(results["detailed_forecast_table"]) == DEFAULT_VALUATION_REQUEST_PAYLOAD["forecast_years"] # Corrected key access
    assert "ufcf" in results["detailed_forecast_table"][0] # Corrected key access

    assert "data_warnings" in results # Check within results container
    assert "Mock warning 1" in results["data_warnings"] # Corrected key access

# For this test, we want to simulate an error from the fetcher instance
# that api.main creates and passes to ValuationService.
@patch("api.main.AshareDataFetcher") # Assuming DI in api.main creates this
def test_calculate_valuation_fetcher_error(MockApiMainAshareDataFetcher):
    """Test valuation endpoint when DataFetcher raises an error."""
    mock_fetcher_instance = MockApiMainAshareDataFetcher.return_value
    # This mock_fetcher_instance is what api.main.py will create and pass to ValuationService
    mock_fetcher_instance.get_stock_info.side_effect = ValueError("Failed to fetch stock basic info") # Corrected method name
    # Mock other fetcher calls that happen before the error or might interfere
    mock_fetcher_instance.get_latest_total_shares.return_value = Decimal('194.05918') # Example value in 亿
    mock_fetcher_instance.get_latest_price.return_value = MOCK_LATEST_PRICE # Mock this call
    mock_fetcher_instance.get_raw_financial_data.return_value = MOCK_RAW_FINANCIAL_DATA # Mock this call

    response = client.post("/api/v1/valuation", json=DEFAULT_VALUATION_REQUEST_PAYLOAD)

    assert response.status_code == 500
    # This error should be caught by the main endpoint's try-except
    assert response.json()["detail"] == "服务器内部错误: Failed to fetch stock basic info"


# Corrected patch targets based on DI and internal instantiation
@patch("api.main.AshareDataFetcher") # DI via api.main
@patch("api.main.DataProcessor")    # DI via api.main
@patch("services.valuation_service.FinancialForecaster") # Instantiated in ValuationService
@patch("api.main.WaccCalculator")     # DI via api.main
@patch("api.main.call_llm_api")
def test_calculate_valuation_calculator_error(
    InjectedMockCallLLM, InjectedMockWACC, InjectedMockFinancialForecaster, 
    InjectedMockDataProcessor, InjectedMockAshareDataFetcher
):
    """Test valuation endpoint for an internal server error during a calculation step."""
    # Setup mocks up to the point of error
    mock_fetcher_instance = InjectedMockAshareDataFetcher.return_value
    mock_fetcher_instance.get_stock_info.return_value = MOCK_STOCK_BASIC_INFO # Use get_stock_info
    mock_fetcher_instance.get_latest_price.return_value = MOCK_LATEST_PRICE
    mock_fetcher_instance.get_raw_financial_data.return_value = MOCK_RAW_FINANCIAL_DATA
    mock_fetcher_instance.get_latest_balance_sheet_info.return_value = MOCK_LATEST_BS_INFO
    mock_fetcher_instance.get_latest_pe_pb.return_value = {'pe': MOCK_STOCK_BASIC_INFO['latest_pe_ttm'], 'pb': MOCK_STOCK_BASIC_INFO['latest_pb_mrq']}
    # get_latest_total_shares is already mocked above, ensure it's correct for this test's needs
    # If it was just 'total_shares', it needs conversion to float for consistency if other parts expect float for '亿股'
    mock_fetcher_instance.get_latest_total_shares.return_value = float(MOCK_STOCK_BASIC_INFO['total_shares'] / 100000000)


    mock_processor_instance = InjectedMockDataProcessor.return_value
    mock_processor_instance.get_processed_data.return_value = MOCK_PROCESSED_DATA_FOR_FORECASTER # Added mock
    # Ensure processed_data is a dict, not None or empty for the check in api/main
    mock_processor_instance.processed_data = {'income_statement': pd.DataFrame({'revenue': [100]})} # Minimal valid structure
    mock_processor_instance.get_historical_ratios.return_value = MOCK_HISTORICAL_RATIOS # Use get method
    mock_processor_instance.get_basic_info.return_value = MOCK_STOCK_BASIC_INFO
    mock_processor_instance.get_latest_balance_sheet.return_value = pd.Series(MOCK_LATEST_BS_INFO) # Use get method, return Series
    mock_processor_instance.get_warnings.return_value = [] # Use get method

    mock_forecaster_instance = InjectedMockFinancialForecaster.return_value
    # Ensure get_full_forecast returns a DataFrame with 'ufcf' column
    mock_forecaster_instance.get_full_forecast.return_value = MOCK_DETAILED_FORECAST_TABLE 

    # Simulate an error in WACCCalculator
    mock_wacc_instance = InjectedMockWACC.return_value
    mock_wacc_instance.get_wacc_and_ke.side_effect = Exception("WACC calculation failed unexpectedly") # Use get_wacc_and_ke

    InjectedMockCallLLM.return_value = MOCK_LLM_ANALYSIS # LLM might still be called for partial data

    response = client.post("/api/v1/valuation", json=DEFAULT_VALUATION_REQUEST_PAYLOAD)

    assert response.status_code == 500
    # Check the actual error message format from the except block in api/main.py
    assert "基础估值计算失败: 单次估值计算失败: WACC calculation failed unexpectedly" in response.json()["detail"] 

# Adjusted patch targets based on ValuationService structure
@patch("api.main.AshareDataFetcher") # Assuming DI in api.main creates this
@patch("api.main.DataProcessor")    # Assuming DI in api.main creates this
@patch("api.main.WaccCalculator")     # Assuming DI in api.main creates this
@patch("services.valuation_service.FinancialForecaster") # Instantiated in ValuationService
@patch("services.valuation_service.TerminalValueCalculator") # Instantiated in ValuationService
@patch("services.valuation_service.PresentValueCalculator") # Instantiated in ValuationService
@patch("services.valuation_service.EquityBridgeCalculator") # Instantiated in ValuationService
@patch("api.main.call_llm_api")
def test_calculate_valuation_llm_error(
    InjectedMockCallLLM, InjectedMockEBC, InjectedMockPVC, InjectedMockTVC, 
    InjectedMockFF, InjectedMockW, InjectedMockDataProcessor, InjectedMockAshareDataFetcher
):
    """Test valuation endpoint when LLM call fails."""
    # Setup mocks for successful DCF calculation
    mock_fetcher_instance = InjectedMockAshareDataFetcher.return_value
    mock_fetcher_instance.get_stock_info.return_value = MOCK_STOCK_BASIC_INFO # Use get_stock_info
    mock_fetcher_instance.get_latest_price.return_value = MOCK_LATEST_PRICE
    mock_fetcher_instance.get_raw_financial_data.return_value = MOCK_RAW_FINANCIAL_DATA
    mock_fetcher_instance.get_latest_balance_sheet_info.return_value = MOCK_LATEST_BS_INFO
    mock_fetcher_instance.get_latest_pe_pb.return_value = {'pe': MOCK_STOCK_BASIC_INFO['latest_pe_ttm'], 'pb': MOCK_STOCK_BASIC_INFO['latest_pb_mrq']}
    mock_fetcher_instance.get_latest_total_shares.return_value = MOCK_STOCK_BASIC_INFO['total_shares'] / 100000000

    mock_processor_instance = InjectedMockDataProcessor.return_value
    mock_processor_instance.get_processed_data.return_value = MOCK_PROCESSED_DATA_FOR_FORECASTER # Added mock
    mock_processor_instance.get_base_financial_statement_date = MagicMock(return_value='2023-12-31') # Corrected method name
    # mock_processor_instance.base_report_date = '2023-12-31' # Attribute likely not needed
    mock_processor_instance.processed_data = {'income_statement': pd.DataFrame({'revenue': [100]})} # Minimal valid structure
    # Corrected mock target method name
    mock_processor_instance.get_historical_ratios.return_value = MOCK_HISTORICAL_RATIOS
    mock_processor_instance.get_basic_info.return_value = MOCK_STOCK_BASIC_INFO
    mock_processor_instance.get_latest_metrics.return_value = MOCK_LATEST_METRICS # Added mock
    mock_processor_instance.get_latest_balance_sheet.return_value = pd.Series(MOCK_LATEST_BS_INFO)
    mock_processor_instance.get_warnings.return_value = []
    
    # Simulate FinancialForecaster and other calculators returning valid data
    InjectedMockFF.return_value.get_full_forecast.return_value = MOCK_DETAILED_FORECAST_TABLE # Return DataFrame directly with 'ufcf'
    InjectedMockW.return_value.get_wacc_and_ke.return_value = (0.085, 0.10) # Return tuple (wacc, ke)
    # FcfCalculator is used internally by FinancialForecaster, no need to patch here if FF is mocked
    InjectedMockTVC.return_value.calculate_terminal_value.return_value = (Decimal('500'), None) # Return tuple (value, error)
    InjectedMockPVC.return_value.calculate_present_values.return_value = (400.0, 931.38, None) # Return tuple (pv_ufcf, pv_tv, error) - use floats
    # Return tuple (net_debt, equity_val, per_share, error) - use Decimals where appropriate
    InjectedMockEBC.return_value.calculate_equity_value.return_value = (Decimal('1500'), Decimal('350'), Decimal('18.04'), None) 

    # Simulate LLM call failure
    InjectedMockCallLLM.side_effect = Exception("LLM API unavailable")

    # This block should be outside the 'with' statement
    response = client.post("/api/v1/valuation", json=DEFAULT_VALUATION_REQUEST_PAYLOAD)

    assert response.status_code == 200 # Should still return DCF results
    data = response.json()
    # Access llm_analysis_summary directly
    assert data["valuation_results"]["llm_analysis_summary"] == "Error in LLM analysis: LLM API unavailable"
    # Rating is not part of the error response structure
    # assert data["valuation_results"]["llm_analysis"]["rating"] is None
    # DCF results should still be present
    # Updated assertion to match DcfForecastDetails structure
    assert data["valuation_results"]["dcf_forecast_details"]["value_per_share"] == 18.04

def test_calculate_valuation_invalid_input_ts_code():
    """Test valuation with invalid input (e.g., missing ts_code)."""
    payload = DEFAULT_VALUATION_REQUEST_PAYLOAD.copy()
    del payload["ts_code"]
    response = client.post("/api/v1/valuation", json=payload)
    assert response.status_code == 422 # Unprocessable Entity for Pydantic validation error
    assert "ts_code" in response.json()["detail"][0]["loc"]

def test_calculate_valuation_invalid_input_beta_type():
    """Test valuation with invalid input type for beta."""
    payload = DEFAULT_VALUATION_REQUEST_PAYLOAD.copy()
    payload["beta"] = "not-a-float"
    response = client.post("/api/v1/valuation", json=payload)
    assert response.status_code == 422
    assert "beta" in response.json()["detail"][0]["loc"]
    assert "Input should be a valid number" in response.json()["detail"][0]["msg"]
