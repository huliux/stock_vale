import pytest
import pandas as pd
import numpy as np
from data_processor import DataProcessor

# --- Fixtures for Mock Data ---

@pytest.fixture
def mock_raw_financial_data():
    """创建包含 NaN 和潜在异常值的模拟财务数据"""
    # 模拟利润表
    income_data = {
        'end_date': pd.to_datetime(['2021-12-31', '2022-12-31', '2023-12-31', '2024-12-31']),
        'total_revenue': [100, 120, np.nan, 160], # 包含 NaN
        'revenue': [90, 110, 130, 150],
        'oper_cost': [60, 70, 80, 95],
        'sell_exp': [10, 12, 13, 1000], # 包含异常值
        'admin_exp': [5, 6, 7, 8],
        'rd_exp': [np.nan, 8, 10, 12], # 包含 NaN
        'income_tax': [3, 4, 5, 6],
        'total_profit': [12, 20, 25, -800] # 包含异常值 (负)
    }
    df_income = pd.DataFrame(income_data)

    # 模拟资产负债表 (增加2020年数据用于计算期初值)
    balance_data = {
        'end_date': pd.to_datetime(['2020-12-31', '2021-12-31', '2022-12-31', '2023-12-31', '2024-12-31']), 
        'accounts_receiv_bill': [18, 20, 25, 30, 35],
        'inventories': [25, 30, 35, np.nan, 45], # 包含 NaN
        'accounts_pay': [12, 15, 18, 20, 22],
        'prepayment': [1, 2, 3, 4, 5],
        'oth_cur_assets': [1, 1, 1, 2, 2],
        'contract_liab': [4, 5, 6, 7, 8],
        'adv_receipts': [np.nan, np.nan, np.nan, np.nan, np.nan], # 全是 NaN
        'payroll_payable': [2, 3, 4, 4, 5],
        'taxes_payable': [1, 1, 1, 2, 2],
        'oth_payable': [1, 2, 3, 3, 4],
        'total_cur_assets': [50, 60, 75, 85, 100], # 简化值，实际计算NWC会用细项
        'total_cur_liab': [25, 30, 35, 40, 45]  # 简化值
    }
    df_balance = pd.DataFrame(balance_data)
    
    # 模拟现金流量表
    cashflow_data = {
         'end_date': pd.to_datetime(['2021-12-31', '2022-12-31', '2023-12-31', '2024-12-31']),
         'depr_fa_coga_dpba': [5, 6, 7, 8],
         'amort_intang_assets': [1, 1, 1, 2],
         'lt_amort_deferred_exp': [0, 0, 1, 1],
         'c_pay_acq_const_fiolta': [-10, -12, -1500, -18], # 包含异常值
         'c_paid_goods_s': [-50, -60, -70, -80]
    }
    df_cashflow = pd.DataFrame(cashflow_data)

    return {
        'income_statement': df_income,
        'balance_sheet': df_balance,
        'cash_flow': df_cashflow
    }

@pytest.fixture
def processed_data_fixture(mock_raw_financial_data):
    """提供已清洗的数据用于测试比率计算"""
    processor = DataProcessor(mock_raw_financial_data)
    # 执行清洗，确保测试基于清洗后的数据
    cleaned_data = processor.clean_data() 
    return cleaned_data

# --- Test Cases ---

def test_clean_data_handles_nans_and_outliers(mock_raw_financial_data):
    """测试 clean_data 是否能处理 NaN 和替换异常值"""
    processor = DataProcessor(mock_raw_financial_data)
    processed_data = processor.clean_data()

    # 1. 检查所有表是否都已处理
    assert 'income_statement' in processed_data
    assert 'balance_sheet' in processed_data
    assert 'cash_flow' in processed_data

    # 2. 检查 NaN 是否已被填充 (插值或填充0) - 不应再有 NaN
    for table_name, df in processed_data.items():
        assert not df.isnull().values.any(), f"表 '{table_name}' 中仍存在 NaN"

    # 3. 检查关键财务项目的插值效果 (示例: total_revenue)
    income_df = processed_data['income_statement']
    assert income_df.loc[income_df['end_date'] == pd.to_datetime('2023-12-31'), 'total_revenue'].iloc[0] == pytest.approx(140)
    balance_df = processed_data['balance_sheet']
    # inventories 在 2023-12-31 是 NaN, 前后是 35, 45 -> 插值为 40
    assert balance_df.loc[balance_df['end_date'] == pd.to_datetime('2023-12-31'), 'inventories'].iloc[0] == pytest.approx(40)

    # 4. 检查异常值是否被处理 (被替换为 NaN 后再填充)
    # sell_exp: [10, 12, 13, 1000] -> 1000 is outlier -> NaN -> ffill -> 13
    assert income_df.loc[income_df['end_date'] == pd.to_datetime('2024-12-31'), 'sell_exp'].iloc[0] == pytest.approx(13)
    # total_profit: [12, 20, 25, -800] -> -800 is outlier -> NaN -> ffill -> 25
    assert income_df.loc[income_df['end_date'] == pd.to_datetime('2024-12-31'), 'total_profit'].iloc[0] == pytest.approx(25)
    # c_pay_acq_const_fiolta: [-10, -12, -1500, -18] -> -1500 is outlier -> NaN -> interpolate -> -15
    cashflow_df = processed_data['cash_flow']
    assert cashflow_df.loc[cashflow_df['end_date'] == pd.to_datetime('2023-12-31'), 'c_pay_acq_const_fiolta'].iloc[0] == pytest.approx(-15)

    # 5. 检查全为 NaN 的列是否被填充为 0
    assert (balance_df['adv_receipts'] == 0).all()

# --- Tests for _get_avg_bs_item ---

@pytest.fixture
def sample_bs_df():
    """创建用于测试 _get_avg_bs_item 的 DataFrame"""
    data = {
        'end_date': pd.to_datetime(['2020-12-31', '2021-12-31', '2022-12-31', '2023-06-30', '2023-12-31', '2024-12-31']),
        'item_a': [10, 12, 15, 18, 20, 22],
        'item_b': [100, 110, np.nan, 130, 140, 150] # Has NaN
    }
    return pd.DataFrame(data)

def test_get_avg_bs_item_finds_both(sample_bs_df):
    """测试找到当期和上一年同期值"""
    processor = DataProcessor({}) # Dummy init
    current, prev = processor._get_avg_bs_item(sample_bs_df, 'item_a', pd.to_datetime('2022-12-31'))
    assert current == 15
    assert prev == 12

def test_get_avg_bs_item_finds_current_only(sample_bs_df):
    """测试只找到当期值 (没有上一年)"""
    processor = DataProcessor({})
    current, prev = processor._get_avg_bs_item(sample_bs_df, 'item_a', pd.to_datetime('2020-12-31'))
    assert current == 10
    assert prev is None

def test_get_avg_bs_item_finds_prev_only(sample_bs_df):
    """测试只找到上一年值 (当期数据缺失)"""
    processor = DataProcessor({})
    # Simulate current date missing by asking for a date not in df, but prev exists
    current, prev = processor._get_avg_bs_item(sample_bs_df, 'item_a', pd.to_datetime('2021-01-15')) 
    assert current is None
    assert prev == 10 # Finds 2020-12-31

def test_get_avg_bs_item_item_missing(sample_bs_df):
    """测试当项目列不存在时"""
    processor = DataProcessor({})
    current, prev = processor._get_avg_bs_item(sample_bs_df, 'item_c', pd.to_datetime('2022-12-31'))
    assert current is None
    assert prev is None

def test_get_avg_bs_item_finds_closest_prev(sample_bs_df):
    """测试当精确上一年日期不存在时，查找最近日期"""
    processor = DataProcessor({})
    # Target date 2023-06-30, previous year target 2022-06-30
    # Closest previous date is 2022-12-31
    current, prev = processor._get_avg_bs_item(sample_bs_df, 'item_a', pd.to_datetime('2023-06-30'))
    assert current == 18
    assert prev == 15 # Found 2022-12-31

def test_get_avg_bs_item_handles_nan(sample_bs_df):
    """测试当找到的值是 NaN 时返回 None"""
    processor = DataProcessor({})
    current, prev = processor._get_avg_bs_item(sample_bs_df, 'item_b', pd.to_datetime('2022-12-31'))
    assert current is None # 2022-12-31 value is NaN
    assert prev == 110 # 2021-12-31 value is 110

# --- Tests for calculate_historical_ratios_and_turnovers ---

def test_calculate_ratios_basic(processed_data_fixture):
    """测试基本比率计算"""
    processor = DataProcessor({}) # Dummy init
    processor.processed_data = processed_data_fixture # Inject cleaned data
    ratios = processor.calculate_historical_ratios_and_turnovers()

    assert 'cogs_to_revenue_ratio' in ratios
    assert 'effective_tax_rate' in ratios
    assert 'accounts_receivable_days' in ratios
    assert 'inventory_days' in ratios
    assert 'accounts_payable_days' in ratios
    assert 'last_actual_nwc' in ratios
    assert 'last_actual_cogs' in ratios
    
    # 示例：检查销货成本占收比 (基于清洗和插值后的数据)
    # is_df['oper_cost'] = [60, 70, 80, 95]
    # is_df['total_revenue'] = [100, 120, 140, 160]
    # Ratios: 0.6, 0.5833, 0.5714, 0.59375
    expected_cogs_ratio = np.mean([60/100, 70/120, 80/140, 95/160])
    assert ratios['cogs_to_revenue_ratio'] == pytest.approx(expected_cogs_ratio)

    # 示例：检查应收账款周转天数
    # AR: [18, 20, 25, 30, 35] (includes 2020)
    # Revenue: [90, 110, 130, 150] (2021-2024)
    # Avg AR for 2021: (18+20)/2 = 19. Days = 19 / (90/360) = 76
    # Avg AR for 2022: (20+25)/2 = 22.5. Days = 22.5 / (110/360) = 73.6363
    # Avg AR for 2023: (25+30)/2 = 27.5. Days = 27.5 / (130/360) = 76.1538
    # Avg AR for 2024: (30+35)/2 = 32.5. Days = 32.5 / (150/360) = 78
    # Mean Days = mean([76, 73.6363, 76.1538, 78])
    expected_ar_days = np.mean([76, 73.636363, 76.153846, 78])
    assert ratios['accounts_receivable_days'] == pytest.approx(expected_ar_days, abs=0.01)

    # 检查 last_actual_cogs (来自清洗后的利润表最后一行)
    assert ratios['last_actual_cogs'] == 95

    # 检查 last_actual_nwc (基于清洗后的资产负债表最后一行计算)
    # Last BS (2024): AR=35, Inv=45, Prepay=5, OthCA=2, AP=22, ContrLiab=8, Payroll=5, Tax=2, OthPay=4
    # NWC = (AR + Inv + Prepay + OthCA) - (AP + ContrLiab + Payroll + Tax + OthPay)
    # NWC = (35 + 45 + 5 + 2) - (22 + 8 + 5 + 2 + 4) = 87 - 41 = 46
    assert ratios['last_actual_nwc'] == pytest.approx(46)

def test_calculate_ratios_division_by_zero(mock_raw_financial_data):
    """测试当收入或成本为零时的比率计算"""
    # Modify data to include zeros
    mock_raw_financial_data['income_statement'].loc[1, 'total_revenue'] = 0
    mock_raw_financial_data['income_statement'].loc[1, 'revenue'] = 0
    mock_raw_financial_data['income_statement'].loc[2, 'oper_cost'] = 0
    
    processor = DataProcessor(mock_raw_financial_data)
    processed_data = processor.clean_data()
    ratios = processor.calculate_historical_ratios_and_turnovers()

    # Ratios involving division by zero should still be calculated (using mean of valid periods) or have defaults
    assert ratios['cogs_to_revenue_ratio'] is not None 
    assert ratios['accounts_receivable_days'] is not None
    assert ratios['inventory_days'] is not None 
    # Check a specific ratio calculation excluding the zero revenue year
    # COGS Ratio: 60/100, 80/140, 95/160 (excluding year 2 where revenue=0)
    # Cleaned total_revenue: [100, 0, 80, 160]
    # Cleaned oper_cost: [60, 70, 0, 95]
    # Valid ratios: 60/100, 0/80, 95/160 (Year 2 ratio is NaN due to revenue=0, ignored by mean)
    # Mean calculation: np.mean([0.6, 0, 0.59375])
    expected_cogs_ratio_correct = np.mean([0.6, 0, 0.59375])
    assert ratios['cogs_to_revenue_ratio'] == pytest.approx(expected_cogs_ratio_correct)

def test_calculate_ratios_insufficient_data():
    """测试当数据不足（例如只有一年）时的行为"""
    income_data = {'end_date': [pd.to_datetime('2024-12-31')], 'total_revenue': [100], 'revenue': [90], 'oper_cost': [60]}
    balance_data = {'end_date': [pd.to_datetime('2024-12-31')], 'accounts_receiv_bill': [20], 'inventories': [30], 'accounts_pay': [15]}
    cashflow_data = {'end_date': [pd.to_datetime('2024-12-31')], 'c_paid_goods_s': [-50]}
    
    insufficient_data = {
        'income_statement': pd.DataFrame(income_data),
        'balance_sheet': pd.DataFrame(balance_data),
        'cash_flow': pd.DataFrame(cashflow_data)
    }
    
    processor = DataProcessor(insufficient_data)
    processed_data = processor.clean_data()
    ratios = processor.calculate_historical_ratios_and_turnovers()

    # 对于需要多年数据的比率（如周转天数），预期结果应为 0 或默认值
    assert ratios['accounts_receivable_days'] == pytest.approx(80) # 20 / (90/360)
    assert ratios['inventory_days'] == pytest.approx(180) # 30 / (60/360)
    assert ratios['accounts_payable_days'] == pytest.approx(108) # 15 / (50/360)
    # 不需要多年数据的比率应能计算
    assert ratios['cogs_to_revenue_ratio'] == pytest.approx(0.6)
    assert ratios['last_actual_cogs'] == 60
    # NWC 计算需要更多列，这里会得到默认值或基于可用列的计算
    assert 'last_actual_nwc' in ratios
