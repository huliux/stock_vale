"""
Unit tests for NWC Calculator.
"""
import pytest
import pandas as pd
from decimal import Decimal, getcontext
import numpy as np
from nwc_calculator import NwcCalculator

# Set precision for Decimal calculations in tests
getcontext().prec = 10

@pytest.fixture
def sample_bs_df():
    """Provides a sample DataFrame with balance sheet items."""
    return pd.DataFrame({
        'end_date': pd.to_datetime(['2021-12-31', '2022-12-31', '2023-12-31']),
        'year': [2021, 2022, 2023], # For forecast testing
        'total_cur_assets': [Decimal('1000'), Decimal('1200'), Decimal('1400')],
        'money_cap': [Decimal('100'), Decimal('150'), Decimal('200')],
        'total_cur_liab': [Decimal('500'), Decimal('600'), Decimal('700')],
        'st_borr': [Decimal('50'), Decimal('60'), Decimal('70')],
        'non_cur_liab_due_1y': [Decimal('20'), Decimal('25'), Decimal('30')]
    })

@pytest.fixture
def calculator():
    """Provides an NwcCalculator instance."""
    return NwcCalculator()

# --- Test calculate_nwc ---

def test_calculate_nwc_success(calculator, sample_bs_df):
    nwc_series = calculator.calculate_nwc(sample_bs_df)
    # Yr1: (1000 - 100) - (500 - 50 - 20) = 900 - 430 = 470
    # Yr2: (1200 - 150) - (600 - 60 - 25) = 1050 - 515 = 535
    # Yr3: (1400 - 200) - (700 - 70 - 30) = 1200 - 600 = 600
    expected_nwc = pd.Series([Decimal('470'), Decimal('535'), Decimal('600')])
    pd.testing.assert_series_equal(nwc_series, expected_nwc, check_index=False, check_dtype=False)

def test_calculate_nwc_missing_columns(calculator, sample_bs_df, capsys):
    df_missing = sample_bs_df.drop(columns=['st_borr'])
    nwc_series = calculator.calculate_nwc(df_missing)
    captured = capsys.readouterr()
    assert nwc_series.isnull().all()
    assert "错误: 计算 NWC 缺少列: st_borr" in captured.out

def test_calculate_nwc_with_nan(calculator, sample_bs_df):
    sample_bs_df.loc[1, 'money_cap'] = np.nan # Introduce NaN
    sample_bs_df.loc[2, 'st_borr'] = np.nan
    nwc_series = calculator.calculate_nwc(sample_bs_df)
    # Yr1: (1000 - 100) - (500 - 50 - 20) = 900 - 430 = 470
    # Yr2: (1200 - 0) - (600 - 60 - 25) = 1200 - 515 = 685 (money_cap NaN treated as 0)
    # Yr3: (1400 - 200) - (700 - 0 - 30) = 1200 - 670 = 530 (st_borr NaN treated as 0)
    expected_nwc = pd.Series([Decimal('470'), Decimal('685'), Decimal('530')])
    pd.testing.assert_series_equal(nwc_series, expected_nwc, check_index=False, check_dtype=False)

def test_calculate_nwc_empty_df(calculator):
    nwc_series = calculator.calculate_nwc(pd.DataFrame())
    assert nwc_series.empty

# --- Test calculate_delta_nwc ---

def test_calculate_delta_nwc_success(calculator):
    nwc = pd.Series([Decimal('470'), Decimal('535'), Decimal('600')])
    delta_nwc = calculator.calculate_delta_nwc(nwc)
    # Yr1: NaN
    # Yr2: 535 - 470 = 65
    # Yr3: 600 - 535 = 65
    expected_delta = pd.Series([Decimal('NaN'), Decimal('65'), Decimal('65')])
    # Convert expected_delta to float to ensure NaN is np.nan for comparison
    # delta_nwc from .diff() is already float with np.nan
    pd.testing.assert_series_equal(delta_nwc, expected_delta.astype(float), check_index=False, check_dtype=False)

def test_calculate_delta_nwc_with_nan(calculator):
    nwc = pd.Series([Decimal('470'), Decimal('NaN'), Decimal('600')])
    delta_nwc = calculator.calculate_delta_nwc(nwc)
    # Yr1: NaN
    # Yr2: NaN - 470 = NaN
    # Yr3: 600 - NaN = NaN
    assert delta_nwc.isnull().all()

def test_calculate_delta_nwc_empty_series(calculator):
    delta_nwc = calculator.calculate_delta_nwc(pd.Series(dtype=float))
    assert delta_nwc.empty

def test_calculate_delta_nwc_single_value(calculator):
    nwc = pd.Series([Decimal('500')])
    delta_nwc = calculator.calculate_delta_nwc(nwc)
    assert len(delta_nwc) == 1
    assert pd.isna(delta_nwc.iloc[0])

# --- Test calculate_historical_nwc_and_delta ---

def test_calculate_historical_nwc_and_delta_success(calculator, sample_bs_df):
    result_df = calculator.calculate_historical_nwc_and_delta(sample_bs_df.copy())
    assert 'nwc' in result_df.columns
    assert 'delta_nwc' in result_df.columns
    # NWC: [470, 535, 600]
    # Delta: [NaN, 65, 65]
    assert result_df['nwc'].iloc[0] == pytest.approx(Decimal('470'))
    assert result_df['nwc'].iloc[1] == pytest.approx(Decimal('535'))
    assert result_df['nwc'].iloc[2] == pytest.approx(Decimal('600'))
    assert pd.isna(result_df['delta_nwc'].iloc[0])
    assert result_df['delta_nwc'].iloc[1] == pytest.approx(Decimal('65'))
    assert result_df['delta_nwc'].iloc[2] == pytest.approx(Decimal('65'))

def test_calculate_historical_nwc_and_delta_unsorted(calculator, sample_bs_df):
    unsorted_df = sample_bs_df.iloc[::-1].copy() # Reverse order
    result_df = calculator.calculate_historical_nwc_and_delta(unsorted_df)
    # Should be sorted back before calculation
    assert result_df.index.tolist() == [0, 1, 2] # Check if index is sorted back
    assert result_df['nwc'].iloc[0] == pytest.approx(Decimal('470'))
    assert pd.isna(result_df['delta_nwc'].iloc[0])
    assert result_df['delta_nwc'].iloc[1] == pytest.approx(Decimal('65'))

def test_calculate_historical_nwc_and_delta_empty(calculator):
    result_df = calculator.calculate_historical_nwc_and_delta(pd.DataFrame())
    assert result_df.empty

# --- Test calculate_forecast_delta_nwc ---

def test_calculate_forecast_delta_nwc_success(calculator, sample_bs_df):
    # Use sample_bs_df as forecast_df for this test
    last_hist_nwc = Decimal('450') # Assume last historical NWC was 450
    result_df = calculator.calculate_forecast_delta_nwc(sample_bs_df.copy(), last_hist_nwc)

    assert 'nwc' in result_df.columns
    assert 'delta_nwc' in result_df.columns
    # NWC: [470, 535, 600]
    # Delta Yr1: 470 - 450 = 20
    # Delta Yr2: 535 - 470 = 65
    # Delta Yr3: 600 - 535 = 65
    assert result_df['nwc'].iloc[0] == pytest.approx(Decimal('470'))
    assert result_df['delta_nwc'].iloc[0] == pytest.approx(Decimal('20'))
    assert result_df['delta_nwc'].iloc[1] == pytest.approx(Decimal('65'))
    assert result_df['delta_nwc'].iloc[2] == pytest.approx(Decimal('65'))

def test_calculate_forecast_delta_nwc_missing_last_hist(calculator, sample_bs_df, capsys):
    result_df = calculator.calculate_forecast_delta_nwc(sample_bs_df.copy(), None)
    captured = capsys.readouterr()
    # Delta Yr1: 470 - 0 = 470 (Uses 0 as default)
    # Update expected warning message to match the actual output
    assert "警告: 未提供最后一个历史 NWC 值，第一年 ΔNWC 可能不准确 (假设为 0)。" in captured.out
    assert result_df['delta_nwc'].iloc[0] == pytest.approx(Decimal('470'))
    assert result_df['delta_nwc'].iloc[1] == pytest.approx(Decimal('65'))

def test_calculate_forecast_delta_nwc_empty(calculator):
    result_df = calculator.calculate_forecast_delta_nwc(pd.DataFrame(), Decimal('450'))
    assert result_df.empty

def test_calculate_forecast_delta_nwc_unsorted(calculator, sample_bs_df):
    unsorted_df = sample_bs_df.iloc[::-1].copy() # Reverse order
    last_hist_nwc = Decimal('450')
    result_df = calculator.calculate_forecast_delta_nwc(unsorted_df, last_hist_nwc)
    # Should be sorted by 'year' before calculation
    assert result_df.index.tolist() == [0, 1, 2] # Check if index is sorted back based on year
    assert result_df['delta_nwc'].iloc[0] == pytest.approx(Decimal('20'))
    assert result_df['delta_nwc'].iloc[1] == pytest.approx(Decimal('65'))
