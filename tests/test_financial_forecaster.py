import pytest
import pandas as pd
import numpy as np
from financial_forecaster import FinancialForecaster

# --- Fixtures ---

@pytest.fixture
def sample_historical_ratios():
    """提供用于测试的模拟历史比率和数据"""
    return {
        'cogs_to_revenue_ratio': 0.6,
        'sga_rd_to_revenue_ratio': 0.15,
        'da_to_revenue_ratio': 0.05,
        'capex_to_revenue_ratio': 0.08, # 注意：ValuationCalculator 中计算的是绝对值比率
        'effective_tax_rate': 0.25,
        'accounts_receivable_days': 75,
        'inventory_days': 180,
        'accounts_payable_days': 90,
        'other_current_assets_to_revenue_ratio': 0.05,
        'other_current_liabilities_to_revenue_ratio': 0.03,
        'last_actual_nwc': 50, # 假设的期初 NWC
        'last_actual_cogs': 600 # 假设的期初 COGS
    }

@pytest.fixture
def sample_forecast_assumptions():
    """提供用于测试的模拟预测假设"""
    return {
        "forecast_years": 5,
        "revenue_growth_stages": [
            {"duration": 3, "growth_rate": 0.15}, # 年份 1, 2, 3
            {"duration": 2, "growth_rate": 0.10}  # 年份 4, 5
        ],
        "effective_tax_rate": 0.25,
        # 可以添加调整项进行更复杂的测试
        # "inventory_days_target": 170, 
    }

@pytest.fixture
def sample_forecaster(sample_historical_ratios, sample_forecast_assumptions):
    """创建 FinancialForecaster 实例"""
    last_actual_revenue = 1000 # 假设的期初收入
    return FinancialForecaster(
        last_actual_revenue=last_actual_revenue,
        historical_ratios=sample_historical_ratios,
        forecast_assumptions=sample_forecast_assumptions
    )

# --- Test Cases ---

def test_predict_revenue(sample_forecaster):
    """测试销售额预测"""
    revenue_forecast_df = sample_forecaster.predict_revenue()
    # 修复：检查返回类型是否为 DataFrame
    assert isinstance(revenue_forecast_df, pd.DataFrame) 
    assert len(revenue_forecast_df) == 5 # 预测 5 年
    assert list(revenue_forecast_df.columns) == ['year', 'revenue'] # 检查列名

    # 检查增长率是否按阶段应用
    expected_revenue = [1150, 1322.5, 1520.875, 1672.9625, 1840.25875]
    # 修复：比较 'revenue' 列 (Series)
    pd.testing.assert_series_equal(
        revenue_forecast_df['revenue'], 
        pd.Series(expected_revenue, name='revenue'), # Name the expected series
        check_index=False, # Index might not match exactly if range(1,6) wasn't used
        check_names=False # Ignore name difference if any
    )

def test_predict_income_statement(sample_forecaster):
    """测试利润表项目预测"""
    # 先调用 predict_revenue 来设置内部状态
    sample_forecaster.predict_revenue() 
    # 修复：移除多余的参数
    income_statement = sample_forecaster.predict_income_statement_items() 
    
    assert isinstance(income_statement, pd.DataFrame)
    assert len(income_statement) == 5
    assert 'year' in income_statement.columns
    assert 'revenue' in income_statement.columns
    assert 'cogs' in income_statement.columns
    assert 'gross_profit' in income_statement.columns # 确认 gross_profit 确实返回了
    assert 'sga_rd' in income_statement.columns # Check for renamed column
    # assert 'ebitda' in income_statement.columns # EBITDA is calculated later
    assert 'depreciation_amortization' not in income_statement.columns # D&A is calculated later
    assert 'ebit' in income_statement.columns
    assert 'nopat' in income_statement.columns # 检查 NOPAT 是否计算 - Re-enable assertion
    
    # 检查基于比率的计算 (例如第一年)
    # Revenue = 1150
    # COGS = Revenue * cogs_ratio = 1150 * 0.6 = 690
    # SGA_RD = Revenue * sga_rd_ratio = 1150 * 0.15 = 172.5
    assert income_statement.loc[0, 'cogs'] == pytest.approx(690)
    assert income_statement.loc[0, 'sga_rd'] == pytest.approx(172.5) # Check renamed column
    # EBIT = Revenue - COGS - SGA_RD = 1150 - 690 - 172.5 = 287.5
    assert income_statement.loc[0, 'ebit'] == pytest.approx(287.5)
    # NOPAT = EBIT * (1 - tax_rate) = 287.5 * (1 - 0.25) = 215.625
    # 修复：使用 .iloc[0] 访问 Series 元素
    assert income_statement['nopat'].iloc[0] == pytest.approx(215.625) 

def test_predict_balance_sheet_and_cf(sample_forecaster):
    """测试资产负债表和现金流量相关项目预测"""
    # 先调用 predict_revenue 和 predict_income_statement_items 设置内部状态
    sample_forecaster.predict_revenue()
    sample_forecaster.predict_income_statement_items() 
    # 修复：移除多余的参数
    fcf_components = sample_forecaster.predict_balance_sheet_and_cf_items() 

    assert isinstance(fcf_components, pd.DataFrame)
    assert len(fcf_components) == 5
    # Check columns from both income statement and bs/cf predictions merged
    assert 'year' in fcf_components.columns
    assert 'revenue' in fcf_components.columns # From income statement merge
    assert 'nopat' in fcf_components.columns   # From income statement merge - Re-enable assertion
    assert 'ebitda' in fcf_components.columns # Calculated in this method
    assert 'depreciation_amortization' in fcf_components.columns
    assert 'capital_expenditures' in fcf_components.columns
    assert 'accounts_receivable' in fcf_components.columns
    assert 'inventories' in fcf_components.columns # 修正拼写错误
    assert 'accounts_payable' in fcf_components.columns
    assert 'other_current_assets' in fcf_components.columns
    assert 'other_current_liabilities' in fcf_components.columns
    assert 'net_working_capital' in fcf_components.columns
    assert 'delta_net_working_capital' in fcf_components.columns

    # 检查基于比率/天数的计算 (例如第一年)
    # Revenue = 1150, COGS = 690, NOPAT = 215.625
    # DA = Revenue * da_ratio = 1150 * 0.05 = 57.5
    assert fcf_components.loc[0, 'depreciation_amortization'] == pytest.approx(57.5)
    # CapEx = Revenue * capex_ratio = 1150 * 0.08 = 92
    assert fcf_components.loc[0, 'capital_expenditures'] == pytest.approx(92)
    # AR = Revenue * (AR_days / 360) = 1150 * (75 / 360) = 239.5833
    assert fcf_components.loc[0, 'accounts_receivable'] == pytest.approx(239.5833, abs=0.01)
    # Inv = COGS * (Inv_days / 360) = 690 * (180 / 360) = 345
    assert fcf_components.loc[0, 'inventories'] == pytest.approx(345) # 修正拼写错误
    # AP = COGS * (AP_days / 360) = 690 * (90 / 360) = 172.5
    assert fcf_components.loc[0, 'accounts_payable'] == pytest.approx(172.5)
    # OthCA = Revenue * oth_ca_ratio = 1150 * 0.05 = 57.5
    assert fcf_components.loc[0, 'other_current_assets'] == pytest.approx(57.5)
    # OthCL = Revenue * oth_cl_ratio = 1150 * 0.03 = 34.5
    assert fcf_components.loc[0, 'other_current_liabilities'] == pytest.approx(34.5)
    # NWC_yr1 = (239.58 + 345 + 57.5) - (172.5 + 34.5) = 642.08 - 207 = 435.08
    assert fcf_components.loc[0, 'net_working_capital'] == pytest.approx(435.08, abs=0.01)
    # Delta NWC = NWC_yr1 - previous_nwc (calculated by forecaster based on ratios)
    # previous_nwc = (1000/360*75 + 600/360*180 + 1000*0.05) - (600/360*90 + 1000*0.03)
    # previous_nwc = (208.33 + 300 + 50) - (150 + 30) = 558.33 - 180 = 378.33
    # Expected Delta NWC = 435.08 - 378.33 = 56.75
    assert fcf_components.loc[0, 'delta_net_working_capital'] == pytest.approx(56.75, abs=0.01) # Adjusted assertion
    # EBITDA = NOPAT / (1-tax) + DA = 215.625 / (1-0.25) + 57.5 = 287.5 + 57.5 = 345
    assert fcf_components.loc[0, 'ebitda'] == pytest.approx(345)


def test_get_full_forecast(sample_forecaster):
    """测试获取完整预测结果"""
    full_forecast = sample_forecaster.get_full_forecast()
    
    assert 'income_statement' in full_forecast # This now only contains intermediate IS items
    assert 'fcf_components' in full_forecast # This contains the final merged data including IS, BS, CF items
    assert isinstance(full_forecast['income_statement'], pd.DataFrame)
    assert isinstance(full_forecast['fcf_components'], pd.DataFrame)
    assert len(full_forecast['income_statement']) == 5
    assert len(full_forecast['fcf_components']) == 5
    # Check a column from the final merged dataframe
    assert 'delta_net_working_capital' in full_forecast['fcf_components'].columns

# TODO: 添加更多测试用例
# - 测试包含调整项 (adjustments) 的情况
# - 测试目标天数 (targets) 的情况
# - 测试边界情况 (例如 forecast_years = 1)
# - 测试当历史比率为 0 或负数时的处理
