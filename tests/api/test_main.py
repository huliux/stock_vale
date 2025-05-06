import pytest
from fastapi.testclient import TestClient
import pandas as pd
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
import pandas as pd
from unittest.mock import MagicMock, patch

# Import the FastAPI app instance and models
from api.main import app
from api.models import ValuationResultItem, ValuationMethodResult, DividendAnalysis, GrowthAnalysis, OtherAnalysis, InvestmentAdvice, ValuationResultsContainer

client = TestClient(app)

# --- Test Data ---
MOCK_TS_CODE = '000001.SZ'
MOCK_STOCK_INFO = {'ts_code': MOCK_TS_CODE, 'name': '平安银行', 'industry': '银行'}
MOCK_LATEST_PRICE = 15.0
MOCK_TOTAL_SHARES = 194059.18 # Example value in 10k shares
MOCK_FINANCIALS = pd.DataFrame({
    'year': [2023, 2022, 2021, 2020], # Need 4 years for CAGR
    'ts_code': [MOCK_TS_CODE] * 4,
    'end_date': ['2023-12-31', '2022-12-31', '2021-12-31', '2020-12-31'],
    'n_income': [450e8, 420e8, 390e8, 360e8], # Example in Yuan
    'total_revenue': [1800e8, 1700e8, 1600e8, 1500e8], # Example in Yuan
    'bps': [18.5, 17.0, 15.5, 14.0], # Example
    'operate_profit': [600e8, 550e8, 500e8, 450e8],
    'total_liab': [45000e8, 42000e8, 39000e8, 36000e8],
    'total_hldr_eqy_exc_min_int': [3500e8, 3200e8, 2900e8, 2600e8],
    'total_assets': [48500e8, 45200e8, 41900e8, 38600e8],
    'lt_borr': [5000e8, 4500e8, 4000e8, 3500e8], # Long term borrowings
    'st_borr': [3000e8, 2800e8, 2600e8, 2400e8], # Short term borrowings
    'bond_payable': [1000e8, 900e8, 800e8, 700e8], # Bonds payable
    'money_cap': [2000e8, 1800e8, 1600e8, 1400e8], # Cash and equivalents
    'finan_exp': [-50e8, -45e8, -40e8, -35e8], # Interest expense (often negative)
    'depr_fa_coga_dpba': [10e8, 9e8, 8e8, 7e8], # Depreciation
    'amort_intang_assets': [5e8, 4e8, 3e8, 2e8], # Amortization
    'c_pay_acq_const_fiolta': [50e8, 45e8, 40e8, 35e8], # Basic Capex
    'stot_out_inv_act': [70e8, 65e8, 60e8, 55e8], # Full Capex
    'total_cur_assets': [10000e8, 9000e8, 8000e8, 7000e8],
    'total_cur_liab': [8000e8, 7000e8, 6000e8, 5000e8],
    'c_recp_borrow': [400e8, 380e8, 360e8, 340e8], # Cash from borrowing
    'c_prepay_amt_borr': [200e8, 180e8, 160e8, 140e8], # Cash paid for debt
    'ebit': [650e8, 600e8, 550e8, 500e8], # EBIT
    'ebitda': [665e8, 613e8, 561e8, 509e8], # EBITDA
})
MOCK_DIVIDENDS = pd.DataFrame({
    'year': [2023, 2022, 2021],
    'ts_code': [MOCK_TS_CODE] * 3,
    'end_date': ['2023-12-31', '2022-12-31', '2021-12-31'],
    'cash_div_tax': [0.8, 0.7, 0.6] # Example dividend per share
})

# --- Mock Calculator Results ---
MOCK_VALUATION_ITEM = ValuationResultItem(growth_rate=0.05, discount_rate=0.10, value=20.0, premium=33.33)
MOCK_METHOD_RESULT = ValuationMethodResult(results=[MOCK_VALUATION_ITEM], error_message=None)
MOCK_OTHER_ANALYSIS = OtherAnalysis(
    dividend_analysis=DividendAnalysis(current_yield_pct=5.33, avg_dividend_3y=0.7, payout_ratio_pct=30.0),
    growth_analysis=GrowthAnalysis(net_income_cagr_3y=8.0, revenue_cagr_3y=6.0)
)
MOCK_COMBO_VALUATIONS = {"综合": 19.5, "绝对(基本)+相对": 19.8}
MOCK_INVESTMENT_ADVICE = InvestmentAdvice(
    based_on="DCF (Basic Capex) & 组合3/5", advice="买入", reason="价格低于估值下限",
    min_intrinsic_value=18.0, avg_intrinsic_value=20.0, max_intrinsic_value=22.0,
    safety_margin_pct=20.0, reference_info="PE 估值范围: 16.00-24.00"
)

# --- Tests ---

def test_read_root():
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the Stock Valuation API"}

def test_calculate_valuation_success(monkeypatch):
    """Test the valuation endpoint with mocked data fetcher."""
    # Mock the AshareDataFetcher methods
    mock_fetcher_instance = MagicMock()
    mock_fetcher_instance.get_stock_info.return_value = MOCK_STOCK_INFO
    mock_fetcher_instance.get_latest_price.return_value = MOCK_LATEST_PRICE
    mock_fetcher_instance.get_total_shares.return_value = MOCK_TOTAL_SHARES
    mock_fetcher_instance.get_financial_data.return_value = MOCK_FINANCIALS
    mock_fetcher_instance.get_dividend_data.return_value = MOCK_DIVIDENDS

    # Patch the AshareDataFetcher class in the api.main module where it's used
    monkeypatch.setattr("api.main.AshareDataFetcher", lambda ts_code: mock_fetcher_instance)

    # Make the request
    response = client.post("/api/v1/valuation", json={"ts_code": "000001.SZ"})

    # Mock the ValuationCalculator methods called by the endpoint
    with patch("api.main.ValuationCalculator") as MockCalculator:
        mock_calculator_instance = MockCalculator.return_value
        mock_calculator_instance.calculate_pe_ratio.return_value = 10.0
        mock_calculator_instance.calculate_pb_ratio.return_value = 1.5
        mock_calculator_instance.calculate_ev.return_value = (50000e8, 665e8, 7.5) # ev, ebitda, ev_ebitda
        mock_calculator_instance.wacc = 0.08 # Mock calculated WACC
        mock_calculator_instance.cost_of_equity = 0.10 # Mock calculated Ke

        # Mock valuation methods to return consistent structure
        mock_calculator_instance.perform_fcff_valuation_basic_capex.return_value = ([MOCK_VALUATION_ITEM._asdict()], None) # Use dict for JSON compatibility if needed, or Pydantic model
        mock_calculator_instance.perform_fcfe_valuation_basic_capex.return_value = ([MOCK_VALUATION_ITEM._asdict()], None)
        mock_calculator_instance.perform_fcff_valuation_full_capex.return_value = ([MOCK_VALUATION_ITEM._asdict()], None)
        mock_calculator_instance.perform_fcfe_valuation_full_capex.return_value = ([MOCK_VALUATION_ITEM._asdict()], None)
        mock_calculator_instance.calculate_ddm_valuation.return_value = ([MOCK_VALUATION_ITEM._asdict()], None)

        mock_calculator_instance.get_other_analysis.return_value = MOCK_OTHER_ANALYSIS.dict() # Return as dict
        mock_calculator_instance.get_combo_valuations.return_value = (MOCK_COMBO_VALUATIONS, MOCK_INVESTMENT_ADVICE.dict()) # Return as dict

        # Make the request
        response = client.post("/api/v1/valuation", json={"ts_code": MOCK_TS_CODE})

    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert data["stock_info"] == MOCK_STOCK_INFO
    assert "valuation_results" in data
    results = data["valuation_results"]

    # Check structure based on ValuationResultsContainer
    assert "current_pe" in results
    assert "current_pb" in results
    assert "current_ev_ebitda" in results
    assert "calculated_wacc_pct" in results
    assert "calculated_cost_of_equity_pct" in results
    assert "dcf_fcff_basic_capex" in results
    assert "dcf_fcfe_basic_capex" in results
    assert "dcf_fcff_full_capex" in results
    assert "dcf_fcfe_full_capex" in results
    assert "ddm" in results
    assert "other_analysis" in results
    assert "dividend_analysis" in results["other_analysis"]
    assert "growth_analysis" in results["other_analysis"]
    assert "combo_valuations" in results
    assert "investment_advice" in results
    assert "advice" in results["investment_advice"]

    # Check some mocked values
    assert results["current_pe"] == 10.0
    assert results["current_pb"] == 1.5
    assert results["calculated_wacc_pct"] == 8.0
    assert results["investment_advice"]["advice"] == "买入"
    assert results["combo_valuations"]["综合"] == 19.5

def test_calculate_valuation_not_found(monkeypatch):
    """Test valuation endpoint when financial data is not found."""
    # Mock the AshareDataFetcher methods to return empty financials
    mock_fetcher_instance = MagicMock()
    mock_fetcher_instance.get_stock_info.return_value = MOCK_STOCK_INFO # Still need basic info
    mock_fetcher_instance.get_latest_price.return_value = MOCK_LATEST_PRICE
    mock_fetcher_instance.get_total_shares.return_value = MOCK_TOTAL_SHARES
    mock_fetcher_instance.get_financial_data.return_value = pd.DataFrame() # Empty DataFrame
    # No need to mock dividends if financials are empty
    # No need to mock ValuationCalculator as it won't be reached

    monkeypatch.setattr("api.main.AshareDataFetcher", lambda ts_code: mock_fetcher_instance)

    response = client.post("/api/v1/valuation", json={"ts_code": "999999.SZ"}) # Non-existent code

    assert response.status_code == 404
    assert "Financial data not found" in response.json()["detail"]

def test_calculate_valuation_missing_price(monkeypatch):
    """Test valuation endpoint when latest price is missing."""
    mock_fetcher_instance = MagicMock()
    mock_fetcher_instance.get_stock_info.return_value = MOCK_STOCK_INFO
    # Simulate ValueError from get_latest_price
    mock_fetcher_instance.get_latest_price.side_effect = ValueError("No latest price found")
    # Other methods might not be called if price fails early, but mock them just in case
    mock_fetcher_instance.get_total_shares.return_value = MOCK_TOTAL_SHARES
    mock_fetcher_instance.get_financial_data.return_value = MOCK_FINANCIALS
    mock_fetcher_instance.get_dividend_data.return_value = MOCK_DIVIDENDS

    monkeypatch.setattr("api.main.AshareDataFetcher", lambda ts_code: mock_fetcher_instance)

    response = client.post("/api/v1/valuation", json={"ts_code": "000001.SZ"})

    assert response.status_code == 404
    assert "No latest price found" in response.json()["detail"]
