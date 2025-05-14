"""
Unit tests for FCF Calculator.
"""
import pytest
import pandas as pd
from decimal import Decimal, getcontext
import numpy as np
from unittest.mock import patch
from fcf_calculator import FcfCalculator

# Set precision for Decimal calculations in tests
getcontext().prec = 10

@pytest.fixture
def sample_forecast_df():
    """Provides a sample forecast DataFrame with necessary columns."""
    return pd.DataFrame({
        'year': [1, 2, 3],
        'nopat': [Decimal('200'), Decimal('220'), Decimal('240')],
        'd_a': [Decimal('50'), Decimal('55'), Decimal('60')], # Depreciation & Amortization
        'capex': [Decimal('80'), Decimal('85'), Decimal('90')], # Capital Expenditures
        'delta_nwc': [Decimal('10'), Decimal('12'), Decimal('15')] # Change in Net Working Capital
    })

@pytest.fixture
def calculator():
    """Provides an FcfCalculator instance."""
    return FcfCalculator()

# --- Test Cases ---

def test_calculate_ufcf_success(calculator, sample_forecast_df):
    result_df = calculator.calculate_ufcf(sample_forecast_df.copy()) # Pass a copy

    assert 'ufcf' in result_df.columns
    # Yr1: 200 + 50 - 80 - 10 = 160
    # Yr2: 220 + 55 - 85 - 12 = 178
    # Yr3: 240 + 60 - 90 - 15 = 195
    expected_ufcf = pd.Series([Decimal('160'), Decimal('178'), Decimal('195')], name='ufcf')
    pd.testing.assert_series_equal(result_df['ufcf'], expected_ufcf, check_dtype=False)

def test_calculate_ufcf_missing_columns(calculator, capsys):
    df_missing_nopat = pd.DataFrame({
        'year': [1], 'd_a': [50], 'capex': [80], 'delta_nwc': [10]
    })
    result_df = calculator.calculate_ufcf(df_missing_nopat.copy())
    captured = capsys.readouterr()
    
    assert 'ufcf' not in result_df.columns # Should not add the column if required are missing
    assert "错误: 预测数据中缺少计算 UFCF 所需的列: nopat" in captured.out

    df_missing_all = pd.DataFrame({'year': [1]})
    result_df_all = calculator.calculate_ufcf(df_missing_all.copy())
    captured_all = capsys.readouterr()
    assert 'ufcf' not in result_df_all.columns
    assert "nopat" in captured_all.out
    assert "d_a" in captured_all.out
    assert "capex" in captured_all.out
    assert "delta_nwc" in captured_all.out

def test_calculate_ufcf_with_nan_values(calculator):
    df_with_nan = pd.DataFrame({
        'year': [1, 2, 3],
        'nopat': [Decimal('200'), Decimal('NaN'), Decimal('240')], # NaN in NOPAT
        'd_a': [Decimal('50'), Decimal('55'), Decimal('60')],
        'capex': [Decimal('80'), Decimal('85'), Decimal('NaN')], # NaN in Capex
        'delta_nwc': [Decimal('10'), Decimal('12'), Decimal('15')]
    })
    result_df = calculator.calculate_ufcf(df_with_nan.copy())

    assert 'ufcf' in result_df.columns
    # Yr1: 200 + 50 - 80 - 10 = 160
    # Yr2: 0 + 55 - 85 - 12 = -42 (NOPAT NaN treated as 0)
    # Yr3: 240 + 60 - 0 - 15 = 285 (Capex NaN treated as 0)
    expected_ufcf = pd.Series([Decimal('160'), Decimal('-42'), Decimal('285')], name='ufcf')
    pd.testing.assert_series_equal(result_df['ufcf'], expected_ufcf, check_dtype=False)

def test_calculate_ufcf_results_in_nan_inf(calculator, sample_forecast_df, capsys):
    # Simulate a case where calculation might result in NaN/Inf (less likely with Decimal)
    # Let's force an input to be Inf
    df_with_inf = sample_forecast_df.copy()
    df_with_inf.loc[1, 'nopat'] = Decimal('inf')

    result_df = calculator.calculate_ufcf(df_with_inf)

    assert 'ufcf' in result_df.columns
    # Yr1: 160
    # Yr2: inf + 55 - 85 - 12 = inf
    # Yr3: 195
    # Compare as float after potential Decimal calculation
    assert float(result_df.loc[0, 'ufcf']) == pytest.approx(160.0) 
    assert result_df.loc[1, 'ufcf'].is_infinite() # Use Decimal's method
    assert float(result_df.loc[2, 'ufcf']) == pytest.approx(195.0)
    
    captured = capsys.readouterr()
    assert "警告: UFCF 计算结果包含无效值 (NaN 或 Inf)" in captured.out


@patch('fcf_calculator.pd.Series.fillna') # Mock a pandas Series method to simulate error
def test_calculate_ufcf_general_exception(mock_fillna, calculator, sample_forecast_df, capsys):
    mock_fillna.side_effect = Exception("Unexpected fillna error")
    
    result_df = calculator.calculate_ufcf(sample_forecast_df.copy())
    captured = capsys.readouterr()

    assert 'ufcf' in result_df.columns # Column should be added but filled with NaN
    assert result_df['ufcf'].isnull().all() # All values should be NaN due to the exception
    assert "错误: 转换 UFCF 输入列为 Decimal 时出错: Unexpected fillna error" in captured.out
