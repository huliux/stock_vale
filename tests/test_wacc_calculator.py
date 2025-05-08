"""
Unit tests for WACC Calculator.
"""
import pytest
from decimal import Decimal, getcontext
import pandas as pd
from unittest.mock import patch
import os

from wacc_calculator import WaccCalculator

# Set precision for Decimal calculations in tests
getcontext().prec = 10 # Higher precision for intermediate test calculations if needed

@pytest.fixture
def sample_financials_dict():
    """Provides a sample financials_dict for testing."""
    return {
        'balance_sheet': pd.DataFrame({
            'end_date': [pd.to_datetime('2023-12-31')],
            'lt_borr': [10000000000],      # 100亿
            'st_borr': [5000000000],       # 50亿
            'bond_payable': [2000000000],  # 20亿
            'non_cur_liab_due_1y': [1000000000], # 10亿
            'total_liab': [20000000000]    # 200亿
        })
    }

@pytest.fixture
def default_wacc_params():
    return {
        'target_debt_ratio': Decimal('0.4'),
        'cost_of_debt': Decimal('0.05'),
        'tax_rate': Decimal('0.25'),
        'risk_free_rate': Decimal('0.03'),
        'beta': Decimal('1.1'),
        'market_risk_premium': Decimal('0.06'),
        'size_premium': Decimal('0.01')
    }

# --- Test __init__ ---

def test_wacc_calculator_init_defaults(sample_financials_dict):
    """Test WACC calculator initialization with default environment variables."""
    # Ensure no conflicting env vars are set for this test
    with patch.dict(os.environ, {}, clear=True):
        calculator = WaccCalculator(financials_dict=sample_financials_dict, market_cap=Decimal('1000')) # 1000亿市值
    
    assert calculator.market_cap == Decimal('100000000000') # 1000亿 * 1e8
    assert calculator.default_beta == Decimal('1.0') # Default from code if env not set
    assert calculator.default_risk_free_rate == Decimal('0.03')
    assert calculator.default_market_risk_premium == Decimal('0.05')
    assert calculator.default_cost_of_debt_pretax == Decimal('0.05')
    assert calculator.default_tax_rate == Decimal('0.25')
    assert calculator.default_size_premium == Decimal('0.0')
    assert calculator.default_target_debt_ratio == Decimal('0.45')


@patch.dict(os.environ, {
    'DEFAULT_BETA': '1.2',
    'RISK_FREE_RATE': '0.02',
    'MARKET_RISK_PREMIUM': '0.07',
    'DEFAULT_COST_OF_DEBT': '0.06',
    'DEFAULT_TARGET_TAX_RATE': '0.20',
    'DEFAULT_SIZE_PREMIUM': '0.005',
    'TARGET_DEBT_RATIO': '0.50'
})
def test_wacc_calculator_init_from_env(sample_financials_dict):
    """Test WACC calculator initialization with values from environment variables."""
    calculator = WaccCalculator(financials_dict=sample_financials_dict, market_cap=Decimal('500'))
    assert calculator.default_beta == Decimal('1.2')
    assert calculator.default_risk_free_rate == Decimal('0.02')
    assert calculator.default_market_risk_premium == Decimal('0.07')
    assert calculator.default_cost_of_debt_pretax == Decimal('0.06')
    assert calculator.default_tax_rate == Decimal('0.20')
    assert calculator.default_size_premium == Decimal('0.005')
    assert calculator.default_target_debt_ratio == Decimal('0.50')

@patch.dict(os.environ, {'DEFAULT_BETA': 'invalid_float'}, clear=True)
def test_wacc_calculator_init_invalid_env_fallback(sample_financials_dict, capsys):
    """Test fallback to hardcoded defaults if env var is invalid."""
    calculator = WaccCalculator(financials_dict=sample_financials_dict, market_cap=Decimal('100'))
    captured = capsys.readouterr()
    assert "警告：无法从环境变量加载数值 WACC 参数" in captured.out
    assert calculator.default_beta == Decimal('1.0') # Falls back to hardcoded default

# --- Test get_wacc_and_ke ---

def test_get_wacc_and_ke_with_valid_params(sample_financials_dict, default_wacc_params):
    calculator = WaccCalculator(financials_dict=sample_financials_dict, market_cap=Decimal('1000'))
    
    # Ke = Rf + Beta * MRP + SP = 0.03 + 1.1 * 0.06 + 0.01 = 0.03 + 0.066 + 0.01 = 0.106
    # Cost of Debt (AT) = Kd * (1 - T) = 0.05 * (1 - 0.25) = 0.05 * 0.75 = 0.0375
    # WACC = E_ratio * Ke + D_ratio * Kd(AT)
    # E_ratio = 1 - 0.4 = 0.6
    # WACC = 0.6 * 0.106 + 0.4 * 0.0375 = 0.0636 + 0.015 = 0.0786
    
    wacc, ke = calculator.get_wacc_and_ke(params=default_wacc_params)
    
    # Compare as floats since the method returns floats now
    assert ke == pytest.approx(0.106)
    assert wacc == pytest.approx(0.0786)

def test_get_wacc_and_ke_uses_defaults_if_params_empty(sample_financials_dict):
    with patch.dict(os.environ, {}, clear=True): # Ensure defaults from code are used
        calculator = WaccCalculator(financials_dict=sample_financials_dict, market_cap=Decimal('1000'))

    # Defaults from code:
    # Rf=0.03, Beta=1.0, MRP=0.05, SP=0.0 => Ke = 0.03 + 1.0 * 0.05 + 0.0 = 0.08
    # Kd=0.05, Tax=0.25 => Kd(AT) = 0.05 * 0.75 = 0.0375
    # DebtRatio=0.45, EquityRatio=0.55
    # WACC = 0.55 * 0.08 + 0.45 * 0.0375 = 0.044 + 0.016875 = 0.060875

    wacc, ke = calculator.get_wacc_and_ke(params={}) # Empty params dict

    # Compare as floats
    assert ke == pytest.approx(0.08)
    assert wacc == pytest.approx(0.060875)

def test_get_wacc_and_ke_invalid_debt_ratio(sample_financials_dict, default_wacc_params, capsys):
    # Need to re-initialize calculator inside patch context if its defaults depend on env vars
    with patch.dict(os.environ, {}, clear=True): 
        calculator = WaccCalculator(financials_dict=sample_financials_dict, market_cap=Decimal('1000'))
    invalid_params = default_wacc_params.copy()
    invalid_params['target_debt_ratio'] = Decimal('1.5') # Invalid
    
    with patch.dict(os.environ, {}, clear=True): # Use calculator's internal defaults for fallback
        wacc, ke = calculator.get_wacc_and_ke(params=invalid_params)
    
    captured = capsys.readouterr()
    assert "无效的目标债务比率 (1.5)" in captured.out
    # Should use calculator.default_target_debt_ratio (0.45 from code default)
    # Ke = 0.106 (from default_wacc_params)
    # Kd(AT) = 0.0375 (from default_wacc_params)
    # WACC = (1-0.45)*0.106 + 0.45*0.0375 = 0.55*0.106 + 0.45*0.0375 = 0.0583 + 0.016875 = 0.075175
    # Compare as floats
    assert ke == pytest.approx(0.106) 
    assert wacc == pytest.approx(0.075175)

def test_get_wacc_and_ke_invalid_ke_calculation(sample_financials_dict, default_wacc_params, capsys):
    # Need to re-initialize calculator inside patch context if its defaults depend on env vars
    with patch.dict(os.environ, {}, clear=True):
        calculator = WaccCalculator(financials_dict=sample_financials_dict, market_cap=Decimal('1000'))
    invalid_params = default_wacc_params.copy()
    invalid_params['beta'] = Decimal('-5.0') # Will make Ke negative
    
    wacc, ke = calculator.get_wacc_and_ke(params=invalid_params)
    captured = capsys.readouterr()
    
    assert "计算出的权益成本(Ke)无效或非正" in captured.out
    assert ke is None # Ke calculation fails
    assert wacc is None

def test_get_wacc_and_ke_invalid_cost_of_debt_after_tax(sample_financials_dict, default_wacc_params, capsys):
    # Need to re-initialize calculator inside patch context if its defaults depend on env vars
    with patch.dict(os.environ, {}, clear=True):
        calculator = WaccCalculator(financials_dict=sample_financials_dict, market_cap=Decimal('1000'))
    invalid_params = default_wacc_params.copy()
    invalid_params['cost_of_debt'] = Decimal('NaN') # Make Kd(AT) NaN

    wacc, ke = calculator.get_wacc_and_ke(params=invalid_params)
    captured = capsys.readouterr()

    assert "计算出的税后债务成本无效" in captured.out
    assert ke == pytest.approx(0.106) # Ke should still be valid (compare as float)
    assert wacc is None

def test_get_wacc_and_ke_invalid_wacc_but_valid_ke(sample_financials_dict, default_wacc_params, capsys):
    # Need to re-initialize calculator inside patch context if its defaults depend on env vars
    with patch.dict(os.environ, {}, clear=True):
        calculator = WaccCalculator(financials_dict=sample_financials_dict, market_cap=Decimal('1000'))
    # To make WACC invalid, e.g., > 1, while Ke is valid.
    # Let Ke be high, and Kd(AT) be high, and debt_ratio high.
    params = {
        'target_debt_ratio': Decimal('0.9'),
        'cost_of_debt': Decimal('0.8'), # High Kd
        'tax_rate': Decimal('0.1'),    # Low tax
        'risk_free_rate': Decimal('0.03'),
        'beta': Decimal('2.0'),        # High Beta
        'market_risk_premium': Decimal('0.10'), # High MRP
        'size_premium': Decimal('0.02')
    }
    # Ke = 0.03 + 2.0 * 0.10 + 0.02 = 0.03 + 0.20 + 0.02 = 0.25 (Valid)
    # Kd(AT) = 0.8 * (1 - 0.1) = 0.8 * 0.9 = 0.72 (Valid)
    # WACC = (1-0.9)*0.25 + 0.9*0.72 = 0.1*0.25 + 0.9*0.72 = 0.025 + 0.648 = 0.673 (Valid, but let's force it higher)
    # To make WACC > 1, let's make Kd(AT) extremely high.
    params['cost_of_debt'] = Decimal('1.5') # Kd = 150%
    # Kd(AT) = 1.5 * 0.9 = 1.35
    # WACC = 0.1*0.25 + 0.9*1.35 = 0.025 + 1.215 = 1.24 (Invalid WACC > 1)

    wacc, ke = calculator.get_wacc_and_ke(params=params)
    captured = capsys.readouterr()

    assert "计算出的 WACC (1.2400) 无效或超出合理范围" in captured.out
    assert ke == pytest.approx(0.25) # Ke is still valid (compare as float)
    assert wacc is None # WACC becomes None

# --- Test calculate_wacc_based_on_market_values ---

def test_calculate_wacc_based_on_market_values_success(sample_financials_dict):
    with patch.dict(os.environ, {}, clear=True): # Use code defaults
        calculator = WaccCalculator(financials_dict=sample_financials_dict, market_cap=Decimal('1000')) # 1000亿市值

    # Defaults: Rf=0.03, Beta=1.0, MRP=0.05, SP=0.0 => Ke = 0.08
    # Kd=0.05, Tax=0.25 => Kd(AT) = 0.0375
    # Market Cap = 1000e8
    # Debt = lt_borr + st_borr + bond_payable + non_cur_liab_due_1y
    # Debt = 100e8 + 50e8 + 20e8 + 10e8 = 180e8
    # Total Capital = 1000e8 + 180e8 = 1180e8
    # Equity Weight = 1000/1180 = 0.8474576
    # Debt Weight = 180/1180 = 0.1525424
    # WACC = 0.8474576 * 0.08 + 0.1525424 * 0.0375
    # WACC = 0.0677966 + 0.00572034 = 0.07351694

    wacc = calculator.calculate_wacc_based_on_market_values()
    # Compare as float
    assert wacc == pytest.approx(0.073517, abs=0.000001)

def test_calculate_wacc_market_no_bs_data(capsys):
    with patch.dict(os.environ, {}, clear=True):
        calculator = WaccCalculator(financials_dict={}, market_cap=Decimal('1000'))
    wacc = calculator.calculate_wacc_based_on_market_values()
    captured = capsys.readouterr()
    assert "财务数据(资产负债表)为空" in captured.out
    assert wacc is None

def test_calculate_wacc_market_zero_market_cap(sample_financials_dict, capsys):
    with patch.dict(os.environ, {}, clear=True):
        calculator = WaccCalculator(financials_dict=sample_financials_dict, market_cap=Decimal('0'))
    wacc = calculator.calculate_wacc_based_on_market_values()
    captured = capsys.readouterr()
    assert "市值非正" in captured.out
    assert wacc is None

def test_calculate_wacc_market_zero_debt_uses_total_liab(sample_financials_dict, capsys):
    # Modify BS to have zero interest-bearing debt
    modified_bs = sample_financials_dict['balance_sheet'].copy()
    modified_bs['lt_borr'] = 0
    modified_bs['st_borr'] = 0
    modified_bs['bond_payable'] = 0
    modified_bs['non_cur_liab_due_1y'] = 0
    # total_liab is 200e8
    
    with patch.dict(os.environ, {}, clear=True):
        calculator = WaccCalculator(financials_dict={'balance_sheet': modified_bs}, market_cap=Decimal('1000'))
    
    # Ke = 0.08, Kd(AT) = 0.0375
    # Market Cap = 1000e8
    # Debt = total_liab = 200e8
    # Total Capital = 1000e8 + 200e8 = 1200e8
    # Equity Weight = 1000/1200 = 0.833333
    # Debt Weight = 200/1200 = 0.166667
    # WACC = 0.833333 * 0.08 + 0.166667 * 0.0375
    # WACC = 0.06666664 + 0.00625001 = 0.07291665
    wacc = calculator.calculate_wacc_based_on_market_values()
    captured = capsys.readouterr()
    assert "未找到明确的有息负债数据，使用总负债近似债务市值计算 WACC" in captured.out
    # Compare as float
    assert wacc == pytest.approx(0.072917, abs=0.000001)

def test_calculate_wacc_market_zero_total_capital(sample_financials_dict, capsys):
    # Modify BS to have zero total_liab as well
    modified_bs = sample_financials_dict['balance_sheet'].copy()
    modified_bs['lt_borr'] = 0
    modified_bs['st_borr'] = 0
    modified_bs['bond_payable'] = 0
    modified_bs['non_cur_liab_due_1y'] = 0
    modified_bs['total_liab'] = 0
    
    with patch.dict(os.environ, {}, clear=True):
        # Market cap also zero to make total capital zero
        calculator = WaccCalculator(financials_dict={'balance_sheet': modified_bs}, market_cap=Decimal('0'))
    wacc = calculator.calculate_wacc_based_on_market_values()
    captured = capsys.readouterr()
    # "市值非正" is checked first
    assert "市值非正" in captured.out # This check comes before total capital check if market_cap is 0
    assert wacc is None

    # Test case where market_cap > 0 but debt is 0 and total_liab is 0, leading to total_capital = market_cap
    # This should actually succeed, with debt_weight = 0
    modified_bs_no_debt = sample_financials_dict['balance_sheet'].copy()
    for col in ['lt_borr', 'st_borr', 'bond_payable', 'non_cur_liab_due_1y', 'total_liab']:
        modified_bs_no_debt[col] = 0
    
    with patch.dict(os.environ, {}, clear=True):
        calculator_no_debt = WaccCalculator(financials_dict={'balance_sheet': modified_bs_no_debt}, market_cap=Decimal('1000'))
    # Ke = 0.08. Debt = 0. WACC = Ke = 0.08
    wacc_no_debt = calculator_no_debt.calculate_wacc_based_on_market_values()
    captured_no_debt = capsys.readouterr()
    assert "无法获取有效债务数据（有息或总负债），假设债务为零计算基于市值的 WACC" in captured_no_debt.out
    # Compare as float
    assert wacc_no_debt == pytest.approx(0.08)
