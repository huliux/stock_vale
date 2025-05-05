import pytest
from fastapi.testclient import TestClient
import pandas as pd
from unittest.mock import MagicMock

# Import the FastAPI app instance
# Adjust the import path based on your project structure and how you run pytest
# If running pytest from the root directory:
from api.main import app
# If api is not directly importable, you might need to adjust PYTHONPATH or use relative imports if structure allows

client = TestClient(app)

# --- Test Data ---
MOCK_STOCK_INFO = {'ts_code': '000001.SZ', 'name': '平安银行', 'industry': '银行'}
MOCK_LATEST_PRICE = 15.0
MOCK_TOTAL_SHARES = 194059.18 # Example value in 10k shares
MOCK_FINANCIALS = pd.DataFrame({
    'year': [2023, 2022],
    'ts_code': ['000001.SZ', '000001.SZ'],
    'end_date': ['2023-12-31', '2022-12-31'],
    'n_income': [450.0 * 100000000, 420.0 * 100000000], # Example in Yuan
    'total_revenue': [1800.0 * 100000000, 1700.0 * 100000000], # Example in Yuan
    'bps': [18.5, 17.0], # Example
    'operate_profit': [600.0 * 100000000, 550.0 * 100000000],
    'total_liab': [45000.0 * 100000000, 42000.0 * 100000000],
    'total_hldr_eqy_exc_min_int': [3500.0 * 100000000, 3200.0 * 100000000],
    'total_assets': [48500.0 * 100000000, 45200.0 * 100000000],
    # Add other necessary columns used by ValuationCalculator with dummy data
})
MOCK_DIVIDENDS = pd.DataFrame({
    'year': [2023, 2022],
    'ts_code': ['000001.SZ', '000001.SZ'],
    'end_date': ['2023-12-31', '2022-12-31'],
    'cash_div_tax': [0.8, 0.7] # Example dividend per share
})

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

    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert data["stock_info"] == MOCK_STOCK_INFO
    assert "valuation_results" in data
    assert "pe_ratio" in data["valuation_results"]
    assert "pb_ratio" in data["valuation_results"]
    assert "dividend_yield_current" in data["valuation_results"]
    # Add more specific checks on valuation results if needed

def test_calculate_valuation_not_found(monkeypatch):
    """Test valuation endpoint when financial data is not found."""
    # Mock the AshareDataFetcher methods to return empty financials
    mock_fetcher_instance = MagicMock()
    mock_fetcher_instance.get_stock_info.return_value = MOCK_STOCK_INFO # Still need basic info
    mock_fetcher_instance.get_latest_price.return_value = MOCK_LATEST_PRICE
    mock_fetcher_instance.get_total_shares.return_value = MOCK_TOTAL_SHARES
    mock_fetcher_instance.get_financial_data.return_value = pd.DataFrame() # Empty DataFrame
    mock_fetcher_instance.get_dividend_data.return_value = pd.DataFrame()

    # Also mock the calculator import/instantiation path, although it shouldn't be reached
    mock_calculator_instance = MagicMock()
    # Patch the calculator class in the api.main module where it's imported/used
    # Note: If ValuationCalculator is imported at the top level, patch "api.main.ValuationCalculator"
    # If imported inside the function, the path might differ or patching might be trickier.
    # Assuming top-level or function-level import resolves to api.main namespace for patching.
    try:
        monkeypatch.setattr("api.main.ValuationCalculator", lambda *args, **kwargs: mock_calculator_instance)
    except AttributeError:
        # If calculator is imported inside the function, patching the module directly might not work easily.
        # This is a fallback, the test might still fail if the import itself causes issues.
        print("Warning: Could not directly patch ValuationCalculator, might be imported inside function.")
        pass


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
