"""
Unit tests for Equity Bridge Calculator.
"""
import pytest
import pandas as pd
from decimal import Decimal, getcontext
import numpy as np
import math # Import math for isnan
from unittest.mock import patch
from equity_bridge_calculator import EquityBridgeCalculator

# Set precision for Decimal calculations in tests
getcontext().prec = 10

@pytest.fixture
def sample_latest_bs():
    """Provides a sample latest balance sheet Series."""
    return pd.Series({
        'lt_borr': Decimal('1000'), # Long term debt
        'st_borr': Decimal('500'),  # Short term debt
        'bond_payable': Decimal('200'), # Bonds payable
        'non_cur_liab_due_1y': Decimal('100'), # Non-current liab due in 1y
        'money_cap': Decimal('300'), # Cash and equivalents
        'minority_int': Decimal('50'), # Minority interest
        'oth_eqt_tools_p_shr': Decimal('20') # Preferred equity (example field)
    })

@pytest.fixture
def calculator():
    """Provides an EquityBridgeCalculator instance."""
    return EquityBridgeCalculator()

# --- Test Cases ---

def test_calculate_equity_value_success(calculator, sample_latest_bs):
    enterprise_value = Decimal('5000')
    total_shares = Decimal('100')

    # Total Debt = 1000 + 500 + 200 + 100 = 1800
    # Cash = 300
    # Net Debt = 1800 - 300 = 1500
    # Minority Interest = 50
    # Preferred Equity = 20
    # Equity Value = EV - Net Debt - Minority Interest - Preferred Equity
    # Equity Value = 5000 - 1500 - 50 - 20 = 3430
    # Value Per Share = 3430 / 100 = 34.30
    
    net_debt, equity_value, value_per_share, error = calculator.calculate_equity_value(
        enterprise_value=enterprise_value,
        latest_balance_sheet=sample_latest_bs,
        total_shares=total_shares
    )
    
    assert error is None
    # Compare as floats
    assert net_debt == pytest.approx(1500.0)
    assert equity_value == pytest.approx(3430.0)
    assert value_per_share == pytest.approx(34.30)

def test_calculate_equity_value_invalid_ev(calculator, sample_latest_bs):
    net_debt, equity_value, value_per_share, error = calculator.calculate_equity_value(
        enterprise_value=None,
        latest_balance_sheet=sample_latest_bs,
        total_shares=Decimal('100')
    )
    assert net_debt is None # Calculation stops early
    assert equity_value is None
    assert value_per_share is None
    assert "无效的企业价值" in error

    net_debt, equity_value, value_per_share, error = calculator.calculate_equity_value(
        enterprise_value=Decimal('NaN'),
        latest_balance_sheet=sample_latest_bs,
        total_shares=Decimal('100')
    )
    assert net_debt is None
    assert equity_value is None
    assert value_per_share is None
    assert "无效的企业价值" in error

def test_calculate_equity_value_missing_bs(calculator):
    net_debt, equity_value, value_per_share, error = calculator.calculate_equity_value(
        enterprise_value=Decimal('5000'),
        latest_balance_sheet=None,
        total_shares=Decimal('100')
    )
    assert net_debt is None
    assert equity_value is None
    assert value_per_share is None
    assert "无法获取最新资产负债表数据" in error

    empty_bs = pd.Series(dtype=float)
    net_debt, equity_value, value_per_share, error = calculator.calculate_equity_value(
        enterprise_value=Decimal('5000'),
        latest_balance_sheet=empty_bs,
        total_shares=Decimal('100')
    )
    # Net debt might be calculated as 0 if all fields are missing and default to 0
    # Let's check the error message primarily
    assert "无法获取最新资产负债表数据" in error # Or check specific field missing if logic changes
    assert equity_value is None
    assert value_per_share is None


def test_calculate_equity_value_missing_bs_fields(calculator):
    # BS missing some debt/cash components
    bs_missing_fields = pd.Series({
        'lt_borr': Decimal('1000'),
        # 'st_borr': Missing
        'bond_payable': Decimal('200'),
        # 'non_cur_liab_due_1y': Missing
        # 'money_cap': Missing
        'minority_int': Decimal('50'),
        'oth_eqt_tools_p_shr': Decimal('20')
    })
    enterprise_value = Decimal('5000')
    total_shares = Decimal('100')

    # Total Debt = 1000 + 0 + 200 + 0 = 1200
    # Cash = 0
    # Net Debt = 1200 - 0 = 1200
    # Equity Value = 5000 - 1200 - 50 - 20 = 3730
    # Value Per Share = 3730 / 100 = 37.30
    
    net_debt, equity_value, value_per_share, error = calculator.calculate_equity_value(
        enterprise_value=enterprise_value,
        latest_balance_sheet=bs_missing_fields,
        total_shares=total_shares
    )
    
    assert error is None
    # Compare as floats
    assert net_debt == pytest.approx(1200.0)
    assert equity_value == pytest.approx(3730.0)
    assert value_per_share == pytest.approx(37.30)

def test_calculate_equity_value_invalid_shares(calculator, sample_latest_bs):
    enterprise_value = Decimal('5000')
    
    # Case 1: total_shares is None
    net_debt, equity_value, value_per_share, error = calculator.calculate_equity_value(
        enterprise_value=enterprise_value,
        latest_balance_sheet=sample_latest_bs,
        total_shares=None
    )
    # Compare as floats
    assert net_debt == pytest.approx(1500.0) # Net debt calculated
    assert equity_value == pytest.approx(3430.0) # Equity value calculated
    assert value_per_share is None # Per share value is None
    # Update expected error message to match the code exactly
    assert "总股本非正、无效或未提供，无法计算每股价值。" == error 

    # Case 2: total_shares is 0
    net_debt, equity_value, value_per_share, error = calculator.calculate_equity_value(
        enterprise_value=enterprise_value,
        latest_balance_sheet=sample_latest_bs,
        total_shares=Decimal('0')
    )
    # Compare as floats
    assert net_debt == pytest.approx(1500.0)
    assert equity_value == pytest.approx(3430.0)
    assert value_per_share is None
    # Update expected error message
    assert "总股本非正、无效或未提供，无法计算每股价值。" == error 

def test_calculate_equity_value_results_in_nan(calculator, sample_latest_bs):
    # Make EV very large and Net Debt negative and large?
    # Easier to test if equity_value calculation itself results in NaN
    # This is unlikely with Decimal unless inputs are NaN, which are checked earlier.
    
    # Test if value_per_share results in NaN/Inf
    # This happens if equity_value is valid but total_shares is problematic (already tested)
    # Or if equity_value is Inf (unlikely with Decimal)
    
    # Let's simulate an internal calculation error leading to NaN equity_value
    # by making one of the balance sheet items NaN
    bs_with_nan = sample_latest_bs.copy()
    bs_with_nan['lt_borr'] = Decimal('NaN') # Introduce NaN directly

    net_debt, equity_value, value_per_share, error = calculator.calculate_equity_value(
        enterprise_value=Decimal('5000'),
        latest_balance_sheet=bs_with_nan, # Use the modified BS
        total_shares=Decimal('100')
    )
    # If lt_borr is NaN, total_debt becomes NaN, net_debt becomes NaN.
    # Then equity_value = EV - NaN_net_debt - ... also becomes NaN.
    # The calculator should detect equity_value.is_nan()

    assert math.isnan(net_debt) # net_debt itself will be float NaN
    assert equity_value is None # equity_value should be None as per calculator logic
    assert value_per_share is None
    assert "计算出的股权价值无效 (NaN 或 Inf)。" == error # Check against the exact error message

@patch('equity_bridge_calculator.Decimal') # Mock Decimal conversion to simulate error
def test_calculate_equity_value_general_exception(mock_decimal, calculator, sample_latest_bs):
    mock_decimal.side_effect = Exception("Unexpected conversion error")
    net_debt, equity_value, value_per_share, error = calculator.calculate_equity_value(
        enterprise_value=Decimal('5000'), # This conversion happens before the try block
        latest_balance_sheet=sample_latest_bs,
        total_shares=Decimal('100')
    )
    # Error happens inside the try block during Decimal conversion of BS items
    assert net_debt is None 
    assert equity_value is None
    assert value_per_share is None
    assert "计算股权价值时发生内部错误: Unexpected conversion error" in error
