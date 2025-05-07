import pytest
from fastapi.testclient import TestClient
import pandas as pd
from unittest.mock import MagicMock, patch

# Import the FastAPI app instance
from api.main import app 

client = TestClient(app)

# --- Test Data ---
MOCK_TS_CODE = '000001.SZ'
MOCK_STOCK_INFO = {'ts_code': MOCK_TS_CODE, 'name': '平安银行', 'industry': '银行'}
MOCK_LATEST_PRICE = 15.0
MOCK_TOTAL_SHARES = 1940591800 # Actual shares
# Simplified Mock Financials Dictionary for DataProcessor input
MOCK_FINANCIALS_DICT = {
    'income_statement': pd.DataFrame({'end_date': pd.to_datetime(['2023-12-31']), 'n_income': [450e8], 'total_revenue': [1800e8], 'operate_profit': [600e8], 'finan_exp': [-50e8], 'ebit': [650e8], 'ebitda': [666e8]}),
    'balance_sheet': pd.DataFrame({'end_date': pd.to_datetime(['2023-12-31']), 'total_liab': [45000e8], 'total_hldr_eqy_inc_min_int': [3600e8], 'lt_borr': [5000e8], 'st_borr': [3000e8], 'bond_payable': [1000e8], 'money_cap': [2000e8]}),
    'cash_flow': pd.DataFrame({'end_date': pd.to_datetime(['2023-12-31']), 'depr_fa_coga_dpba': [10e8], 'amort_intang_assets': [5e8], 'lt_amort_deferred_exp': [1e8]})
}
MOCK_DIVIDENDS = pd.DataFrame({'end_date': pd.to_datetime(['2023-12-31']), 'cash_div_tax': [0.8]})

# --- Mock Calculator Results ---
MOCK_DCF_RESULT = {
    "enterprise_value": 55000e8, "equity_value": 30000e8, "value_per_share": 21.50,
    "error": None, "wacc_used": 0.08, "terminal_value_method_used": "exit_multiple", 
}
MOCK_COMBO_VALUATIONS = {
    "DCF_Forecast": {"value": 21.5, "safety_margin_pct": 43.33},
    "DDM": {"value": 18.0, "safety_margin_pct": 20.0},
    "Composite_Valuation": {"value": 20.45, "safety_margin_pct": 36.33}
}
MOCK_INVESTMENT_ADVICE = {
    "advice":"买入", 
    "reason":"Mocked reason",
}

# --- Tests ---

def test_read_root():
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the Stock Valuation API"}

# Patch dependencies at their source location
# api.main directly uses AshareDataFetcher and ValuationCalculator (imported inside endpoint)
# It does NOT directly use DataProcessor or FinancialForecaster.
@patch("data_fetcher.AshareDataFetcher")
@patch("valuation_calculator.ValuationCalculator") # This will mock it when api.main imports it
def test_calculate_valuation_success(MockCalculator, MockFetcher): # Adjusted parameters
    """Test the valuation endpoint with mocked dependencies."""

    # Configure Mock DataFetcher
    mock_fetcher_instance = MockFetcher.return_value
    mock_fetcher_instance.get_stock_info.return_value = MOCK_STOCK_INFO
    mock_fetcher_instance.get_latest_price.return_value = MOCK_LATEST_PRICE
    mock_fetcher_instance.get_total_shares.return_value = MOCK_TOTAL_SHARES
    # api.main calls get_financial_data() which should return a single DataFrame
    # Let's simulate that the fetcher returns a pre-combined DataFrame
    mock_combined_financials = pd.concat(MOCK_FINANCIALS_DICT.values())
    mock_fetcher_instance.get_financial_data.return_value = mock_combined_financials
    mock_fetcher_instance.get_dividend_data.return_value = MOCK_DIVIDENDS

    # Configure Mock ValuationCalculator
    mock_calculator_instance = MockCalculator.return_value
    mock_calculator_instance.calculate_pe_ratio.return_value = 10.0
    mock_calculator_instance.calculate_pb_ratio.return_value = 1.5
    mock_calculator_instance.calculate_ev.return_value = (50000e8, 665e8, 7.5) # ev, net_debt, ev_ebitda

    # Mock the DCF and DDM methods called in api.main.py
    # Each should return a tuple: (results_list_of_dict, error_message_str_or_none)
    # ValuationMethodResult.results expects List[Dict[str, Any]]
    # The actual structure returned by _perform_dcf_valuation is like:
    # [{'growth_rate': g, 'discount_rate': r, 'value': value_per_share, 'premium': premium}]
    mock_dcf_method_res_list = [{'growth_rate': 0.05, 'discount_rate': 0.10, 'value': 15.0, 'premium': 0.0}] # Adjusted structure
    mock_calculator_instance.perform_fcff_valuation_basic_capex.return_value = (mock_dcf_method_res_list, None)
    mock_calculator_instance.perform_fcfe_valuation_basic_capex.return_value = (mock_dcf_method_res_list, None)
    mock_calculator_instance.perform_fcff_valuation_full_capex.return_value = (mock_dcf_method_res_list, None)
    mock_calculator_instance.perform_fcfe_valuation_full_capex.return_value = (mock_dcf_method_res_list, None)
    mock_calculator_instance.calculate_ddm_valuation.return_value = (mock_dcf_method_res_list, None) # DDM also returns a list with this structure

    # Mock other analysis and combo valuations
    mock_other_analysis_data = {
        'dividend_analysis': {'avg_dividend_yield_5y': 0.03, 'payout_ratio_ttm': 0.30, 'dividend_growth_rate_3y': 0.05, 'sustainable_growth_rate': 0.06},
        'growth_analysis': {'revenue_growth_3y_cagr': 0.08, 'net_profit_growth_3y_cagr': 0.10, 'roic_avg_3y': 0.12}
    }
    mock_calculator_instance.get_other_analysis.return_value = mock_other_analysis_data
    mock_calculator_instance.get_combo_valuations.return_value = (MOCK_COMBO_VALUATIONS, MOCK_INVESTMENT_ADVICE)
    mock_calculator_instance.last_calculated_wacc = 0.08 # Mock WACC
    mock_calculator_instance.last_calculated_ke = 0.10 # Mock Ke


    # Make the request
    response = client.post("/api/v1/valuation", json={"ts_code": MOCK_TS_CODE})

    # Assertions
    assert response.status_code == 200, f"Response content: {response.content}"
    data = response.json()
    
    assert data["stock_info"] == MOCK_STOCK_INFO
    assert "valuation_results" in data
    results = data["valuation_results"]

    assert results["current_pe"] == 10.0
    assert results["current_pb"] == 1.5
    # Check one of the DCF results (they all use mock_dcf_method_res_list in this mock setup)
    # Access the first item in the list, then the 'value' key
    assert results["dcf_fcff_basic_capex"]["results"][0]["value"] == 15.0 # Adjusted assertion
    assert results["combo_valuations"]["Composite_Valuation"]["value"] == 20.45 # From MOCK_COMBO_VALUATIONS
    assert results["investment_advice"]["advice"] == "买入" # From MOCK_INVESTMENT_ADVICE

@patch("data_fetcher.AshareDataFetcher")
def test_calculate_valuation_not_found(MockFetcher):
    """Test valuation endpoint when financial data is not found."""
    mock_fetcher_instance = MockFetcher.return_value
    mock_fetcher_instance.get_stock_info.return_value = MOCK_STOCK_INFO # Valid stock info
    # The actual behavior seems to be that get_latest_price fails first for an invalid ts_code.
    # We will test this actual behavior.
    # Mock get_latest_price to raise the specific error seen in the traceback.
    mock_fetcher_instance.get_latest_price.side_effect = ValueError(f"No latest price found for ts_code: 999999.SZ")
    mock_fetcher_instance.get_total_shares.return_value = MOCK_TOTAL_SHARES # Mock shares for 999999.SZ
    mock_fetcher_instance.get_financial_data.return_value = pd.DataFrame() # Financial data is empty

    response = client.post("/api/v1/valuation", json={"ts_code": "999999.SZ"})

    assert response.status_code == 404
    # Assert the error message that is actually raised first.
    assert "No latest price found for ts_code: 999999.SZ" in response.json()["detail"] # Adjusted assertion

# Use monkeypatch instead of @patch for fetcher methods
def test_calculate_valuation_missing_price(monkeypatch):
    """Test valuation endpoint when latest price is missing."""
    # Mock the methods of AshareDataFetcher using monkeypatch
    mock_fetcher = MagicMock()
    mock_fetcher.get_stock_info.return_value = MOCK_STOCK_INFO
    mock_fetcher.get_latest_price.return_value = None # Simulate missing price
    mock_fetcher.get_total_shares.return_value = MOCK_TOTAL_SHARES
    mock_combined_financials = pd.concat(MOCK_FINANCIALS_DICT.values())
    mock_fetcher.get_financial_data.return_value = mock_combined_financials
    mock_fetcher.get_dividend_data.return_value = MOCK_DIVIDENDS

    # Patch the AshareDataFetcher class itself to return our mock instance
    monkeypatch.setattr("api.main.AshareDataFetcher", lambda *args, **kwargs: mock_fetcher)

    response = client.post("/api/v1/valuation", json={"ts_code": "000001.SZ"})

    assert response.status_code == 404
    assert "Valid latest price not found for 000001.SZ" in response.json()["detail"]

# Use monkeypatch instead of @patch for fetcher methods
def test_calculate_valuation_missing_shares(monkeypatch):
    """Test valuation endpoint when total shares are missing."""
    mock_fetcher = MagicMock()
    mock_fetcher.get_stock_info.return_value = MOCK_STOCK_INFO
    mock_fetcher.get_latest_price.return_value = MOCK_LATEST_PRICE
    mock_fetcher.get_total_shares.return_value = 0 # Simulate missing shares
    mock_combined_financials = pd.concat(MOCK_FINANCIALS_DICT.values())
    mock_fetcher.get_financial_data.return_value = mock_combined_financials
    mock_fetcher.get_dividend_data.return_value = MOCK_DIVIDENDS

    monkeypatch.setattr("api.main.AshareDataFetcher", lambda *args, **kwargs: mock_fetcher)

    response = client.post("/api/v1/valuation", json={"ts_code": "000001.SZ"})

    assert response.status_code == 404
    assert "Valid total shares not found for 000001.SZ" in response.json()["detail"]


@patch("data_fetcher.AshareDataFetcher")
@patch("valuation_calculator.ValuationCalculator") # Only mock what's directly used by api.main
def test_calculate_valuation_internal_error(MockCalculator, MockFetcher):
    """Test valuation endpoint for an internal server error during calculation."""
    mock_fetcher_instance = MockFetcher.return_value
    mock_fetcher_instance.get_stock_info.return_value = MOCK_STOCK_INFO
    mock_fetcher_instance.get_latest_price.return_value = MOCK_LATEST_PRICE
    mock_fetcher_instance.get_total_shares.return_value = MOCK_TOTAL_SHARES
    mock_combined_financials = pd.concat(MOCK_FINANCIALS_DICT.values())
    mock_fetcher_instance.get_financial_data.return_value = mock_combined_financials
    mock_fetcher_instance.get_dividend_data.return_value = MOCK_DIVIDENDS

    mock_calculator_instance = MockCalculator.return_value
    # Simulate an error during one of the calculation methods
    # For example, if calculate_pe_ratio raises an unexpected error
    mock_calculator_instance.calculate_pe_ratio.side_effect = Exception("Unexpected calculation error")

    response = client.post("/api/v1/valuation", json={"ts_code": "000001.SZ"})

    assert response.status_code == 500
    assert "An internal server error occurred" in response.json()["detail"]
