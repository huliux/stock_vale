import os
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import pandas as pd
from decimal import Decimal
# import configparser # 不再需要

load_dotenv() # 加载 .env 文件中的环境变量

# --- Base Class Definition ---
class BaseDataFetcher(ABC):
    """Abstract base class for data fetchers for different markets."""

    def __init__(self, ts_code: str):
        self.ts_code = ts_code
        self.engine = self._create_engine()

    def _create_engine(self):
        """Creates the database engine using environment variables."""
        db_user = os.getenv('DB_USER', 'default_user')
        db_password = os.getenv('DB_PASSWORD', 'default_password')
        db_host = os.getenv('DB_HOST', 'localhost')
        db_port = os.getenv('DB_PORT', '5432')
        db_name = os.getenv('DB_NAME', 'postgres')

        if db_user == 'default_user' or db_password == 'default_password':
            print("警告：未能从环境变量加载数据库用户名或密码。请确保已创建并正确配置 .env 文件。")
              
        engine = create_engine(f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}')
         
        # 添加连接测试 (整体修正缩进)
        try:
            with engine.connect() as connection:
                print("数据库连接测试成功！")
        except Exception as e:
            print(f"数据库连接测试失败: {e}")
            # 可以在这里决定是否抛出异常，或者仅打印错误让后续逻辑处理
            # raise e # 如果希望连接失败时阻止程序继续

        return engine

    @abstractmethod
    def get_stock_info(self) -> Dict[str, Any]:
        """获取股票基本信息"""
        pass

    @abstractmethod
    def get_latest_price(self) -> float:
        """获取最新收盘价"""
        pass

    @abstractmethod
    def get_total_shares(self) -> float:
        """获取总股本"""
        pass

    @abstractmethod
    def get_financial_data(self) -> pd.DataFrame:
        """获取历年财务数据"""
        pass

    @abstractmethod
    def get_dividend_data(self) -> pd.DataFrame:
        """获取历年分红数据"""
        pass

# --- A-Share Implementation ---
class AshareDataFetcher(BaseDataFetcher):
    """Data fetcher implementation for A-shares using PostgreSQL database."""
    def __init__(self, ts_code: str):
        super().__init__(ts_code)
        # Ashare specific table and field configurations
        self.stock_basic_table = 'stock_basic'
        # Note: get_stock_info needs 'industry' field, ensure it's included or handled separately in query
        self.stock_basic_fields = ['ts_code', 'name', 'industry'] 
        
        self.daily_quotes_table = 'daily_quotes'
        self.daily_quotes_fields = ['ts_code', 'close', 'trade_date']
        
        self.income_statement_table = 'income_statement'
        self.income_statement_fields = ['ts_code', 'end_date', 'n_income', 'revenue', 'total_revenue', 'oper_cost', 'operate_profit', 'non_oper_income', 'non_oper_exp']
        
        self.financial_indicators_table = 'financial_indicators'
        # 添加 ebit, ebitda 用于潜在比较或使用
        self.financial_indicators_fields = [
            'ts_code', 'end_date', 'eps', 'bps', 'roe', 'netprofit_margin', 
            'debt_to_assets', 'ebit', 'ebitda' 
        ]
        
        self.cash_flow_table = 'cash_flow'
        self.cash_flow_fields = ['ts_code', 'end_date', 'n_cashflow_act', 'stot_out_inv_act', 'stot_cash_in_fnc_act', 'stot_cashout_fnc_act', 'c_pay_acq_const_fiolta', 'c_paid_invest', 'decr_inventories', 'incr_oper_payable', 'decr_oper_payable', 'c_recp_borrow', 'c_prepay_amt_borr', 'depr_fa_coga_dpba', 'amort_intang_assets']
        
        self.balance_sheet_table = 'balance_sheet'
        # 添加 money_cap, lt_borr, st_borr, bond_payable 用于 EV 和 WACC 计算
        self.balance_sheet_fields = [
            'ts_code', 'end_date', 'total_share', 'total_assets', 'total_liab', 
            'total_hldr_eqy_exc_min_int', 'total_cur_assets', 'total_cur_liab',
            'money_cap', 'lt_borr', 'st_borr', 'bond_payable' 
        ]
        
        self.dividend_table = 'dividend'
        self.dividend_fields = ['ts_code', 'end_date', 'cash_div_tax', 'ann_date', 'div_proc']
        
        # 移除 valuation_metrics 相关定义，改用 specific 方法
        # self.valuation_metrics_table = 'valuation_metrics' 
        # self.valuation_metrics_fields = [...] 
    
    def get_stock_info(self):
        """获取股票基本信息"""
        with self.engine.connect() as conn:
            # 确保查询包含所有必要字段
            required_fields = ['ts_code', 'name', 'industry']
            fields_str = ', '.join(set(self.stock_basic_fields + required_fields))
            query = text(f"SELECT {fields_str} FROM {self.stock_basic_table} WHERE ts_code = :ts_code")
            result = conn.execute(query, {'ts_code': self.ts_code})
            row = result.fetchone()
            if row is not None:
                info = row._asdict()
                # 确保所有必要字段都有值
                for field in required_fields:
                    if field not in info or info[field] is None:
                        info[field] = '未知' if field == 'industry' else self.ts_code if field == 'ts_code' else '未知名称'
                return info
            else:
                # 返回包含必要字段的默认值
                return {
                    'ts_code': self.ts_code,
                    'name': '未知名称',
                    'industry': '未知'
                }
    
    def get_latest_price(self):
        """获取最新收盘价"""
        with self.engine.connect() as conn:
            fields_str = ', '.join(self.daily_quotes_fields)
            query = text(f"SELECT {fields_str} FROM {self.daily_quotes_table} WHERE ts_code = :ts_code ORDER BY trade_date DESC LIMIT 1")
            result = conn.execute(query, {'ts_code': self.ts_code})
            row = result.fetchone()
            if row is not None:
                return float(row._asdict()['close'])
            else:
                raise ValueError(f"No latest price found for ts_code: {self.ts_code}")
    
    def get_total_shares(self):
        """获取总股本"""
        with self.engine.connect() as conn:
            fields_str = ', '.join(self.balance_sheet_fields)
            query = text(f"SELECT {fields_str} FROM {self.balance_sheet_table} WHERE ts_code = :ts_code ORDER BY end_date DESC LIMIT 1")
            result = conn.execute(query, {'ts_code': self.ts_code})
            row = result.fetchone()
            if row is not None:
                return float(row._asdict()['total_share'])
            else:
                print(f"No total shares found for ts_code: {self.ts_code}, returning default value 1")
                return 1
    
    def get_financial_data(self):
        """获取历年财务数据"""
        # 获取年报数据
        with self.engine.connect() as conn:
            income_fields_str = ', '.join([f'i.{field}' for field in self.income_statement_fields])
            financial_fields_str = ', '.join([f'f.{field}' for field in self.financial_indicators_fields])
            cash_flow_fields_str = ', '.join([f'c.{field}' for field in self.cash_flow_fields])
            balance_sheet_fields_str = ', '.join([f'b.{field}' for field in self.balance_sheet_fields])
            
            query = text(f"""
                SELECT 
                    {income_fields_str}, 
                    EXTRACT(YEAR FROM i.end_date::timestamp) as year,
                    {financial_fields_str},
                    {cash_flow_fields_str},
                    {balance_sheet_fields_str}
                FROM {self.income_statement_table} i
                JOIN {self.financial_indicators_table} f ON i.ts_code = f.ts_code AND i.end_date = f.end_date
                JOIN {self.cash_flow_table} c ON i.ts_code = c.ts_code AND i.end_date = c.end_date
                JOIN {self.balance_sheet_table} b ON i.ts_code = b.ts_code AND i.end_date = b.end_date
                WHERE i.ts_code = :ts_code 
                AND EXTRACT(MONTH FROM i.end_date::timestamp) = 12
                ORDER BY i.end_date DESC
            """)
            result = conn.execute(query, {'ts_code': self.ts_code})
            # 去重，保证每年只有一条数据
            data = []
            years_seen = set()
            for row in result:
                row_dict = row._asdict()
                year = row_dict['year']
                if year not in years_seen:
                    years_seen.add(year)
                    # 将所有数值字段转换为float
                    for key, value in row_dict.items():
                        if isinstance(value, (int, float, Decimal)):
                            row_dict[key] = float(value)
                    data.append(row_dict)
            
            return pd.DataFrame(data)
    
    def get_dividend_data(self):
        """获取历年分红数据"""
        with self.engine.connect() as conn:
            fields_str = ', '.join(self.dividend_fields)
            query = text(f"""
                SELECT 
                    {fields_str},
                    EXTRACT(YEAR FROM end_date::timestamp) as year
                FROM {self.dividend_table}
                WHERE ts_code = :ts_code
                ORDER BY end_date DESC
            """)
            result = conn.execute(query, {'ts_code': self.ts_code})
            
            data = []
            for row in result:
                data.append(row._asdict())
            
            df = pd.DataFrame(data)
            if not df.empty:
                # 将现金分红转为浮点数
                df['cash_div_tax'] = df['cash_div_tax'].astype(float)
            return df

    def get_latest_valuation_metrics(self, valuation_date: Optional[str] = None) -> Optional[pd.DataFrame]:
        """
        获取指定日期或之前的最新估值指标。
        Args:
            valuation_date (Optional[str]): 估值基准日期 (YYYY-MM-DD)。如果为 None，则获取最新日期。
        Returns:
            Optional[pd.DataFrame]: 包含最新估值指标的 DataFrame，如果找不到则返回 None。
        """
        print(f"Fetching latest valuation metrics for {self.ts_code} up to {valuation_date or 'latest'}...")
        with self.engine.connect() as conn:
            fields_str = ', '.join(self.valuation_metrics_fields)
            # 构建查询，如果提供了日期，则筛选该日期或之前的最新数据
            date_condition = ""
            params = {'ts_code': self.ts_code}
            if valuation_date:
                date_condition = "AND trade_date <= :valuation_date"
                params['valuation_date'] = valuation_date
            
            # 假设 valuation_metrics 表存在且包含所需字段
            # 如果没有 valuation_metrics 表，可能需要从 financial_indicators 或 daily_quotes 获取并计算
            # 这里假设 valuation_metrics 表是主要的来源
            query = text(f"""
                SELECT {fields_str} 
                FROM {self.valuation_metrics_table} 
                WHERE ts_code = :ts_code {date_condition}
                ORDER BY trade_date DESC 
                LIMIT 1
            """)
            
            try:
                result = conn.execute(query, params)
                row = result.fetchone()
                if row is not None:
                    df = pd.DataFrame([row._asdict()])
                    # 确保数据类型正确
                    for col in ['close', 'pe', 'pb', 'total_share', 'total_mv', 'circ_mv']:
                        if col in df.columns:
                            df[col] = pd.to_numeric(df[col], errors='coerce')
                    if 'trade_date' in df.columns:
                         df['trade_date'] = pd.to_datetime(df['trade_date'])
                    print(f"  Found latest valuation metrics: {df.iloc[0].to_dict()}")
                    return df
                else:
                    print(f"  No valuation metrics found for {self.ts_code} up to {valuation_date or 'latest'}.")
                    return None
            except Exception as e:
                 # 处理可能的表不存在或字段不存在错误
                 print(f"Error fetching from {self.valuation_metrics_table}: {e}. Trying fallback (e.g., daily_quotes)...")
                 # Fallback: 尝试从 daily_quotes 获取最新价格和日期
                 try:
                     dq_fields = ['ts_code', 'trade_date', 'close']
                     dq_fields_str = ', '.join(dq_fields)
                     dq_query = text(f"""
                         SELECT {dq_fields_str} 
                         FROM {self.daily_quotes_table} 
                         WHERE ts_code = :ts_code {date_condition}
                         ORDER BY trade_date DESC 
                         LIMIT 1
                     """)
                     dq_result = conn.execute(dq_query, params)
                     dq_row = dq_result.fetchone()
                     if dq_row:
                         # 创建一个只包含基本信息的 DataFrame
                         fallback_data = dq_row._asdict()
                         df = pd.DataFrame([fallback_data])
                         df['close'] = pd.to_numeric(df['close'], errors='coerce')
                         df['trade_date'] = pd.to_datetime(df['trade_date'])
                         print(f"  Using fallback data from daily_quotes: {df.iloc[0].to_dict()}")
                         # 其他指标 (pe, pb, total_share等) 将为 None 或需要进一步获取
                         return df
                     else:
                          print(f"  Fallback failed: No data found in daily_quotes either.")
                          return None
                 except Exception as fallback_e:
                      print(f"Error during fallback fetch from daily_quotes: {fallback_e}")
                      return None
                      
    def get_latest_pe_pb(self, valuation_date: Optional[str] = None) -> Dict[str, Optional[float]]:
        """
        (修订) 获取指定日期或之前的最新 PE 和 PB。
        从 valuation_metrics 表获取。
        Args:
            valuation_date (Optional[str]): 估值基准日期 (YYYY-MM-DD)。如果为 None，则获取最新日期。
        Returns:
            Dict[str, Optional[float]]: 包含 'pe' 和 'pb' 的字典。
        """
        print(f"Fetching latest PE/PB for {self.ts_code} up to {valuation_date or 'latest'}...")
        pe_pb_data = {'pe': None, 'pb': None}
        with self.engine.connect() as conn:
            # valuation_metrics 按 trade_date 记录
            date_condition = ""
            params = {'ts_code': self.ts_code}
            if valuation_date:
                date_condition = "AND trade_date <= :valuation_date"
                params['valuation_date'] = valuation_date

            # 从 valuation_metrics 获取 PE 和 PB
            query = text(f"""
                SELECT pe, pb 
                FROM valuation_metrics 
                WHERE ts_code = :ts_code {date_condition}
                ORDER BY trade_date DESC 
                LIMIT 1
            """)
            try:
                result = conn.execute(query, params)
                row = result.fetchone()
                if row is not None:
                    row_dict = row._asdict()
                    pe_pb_data['pe'] = pd.to_numeric(row_dict.get('pe'), errors='coerce')
                    pe_pb_data['pb'] = pd.to_numeric(row_dict.get('pb'), errors='coerce')
                    print(f"  Found latest PE: {pe_pb_data['pe']}, PB: {pe_pb_data['pb']} from valuation_metrics")
                else:
                    print(f"  No PE/PB data found in valuation_metrics for {self.ts_code} up to {valuation_date or 'latest'}.")
            except Exception as e:
                print(f"Error fetching PE/PB from valuation_metrics: {e}")
                # 保留返回 None 的默认行为
        
        # 清理 NaN 值为 None
        if pd.isna(pe_pb_data['pe']): pe_pb_data['pe'] = None
        if pd.isna(pe_pb_data['pb']): pe_pb_data['pb'] = None
            
        return pe_pb_data

    def get_latest_total_shares(self, valuation_date: Optional[str] = None) -> Optional[float]:
        """
        获取指定日期或之前的最新总股本。
        从 valuation_metrics 表获取。
        Args:
            valuation_date (Optional[str]): 估值基准日期 (YYYY-MM-DD)。如果为 None，则获取最新日期。
        Returns:
            Optional[float]: 总股本，如果找不到则返回 None。
        """
        print(f"Fetching latest total shares for {self.ts_code} up to {valuation_date or 'latest'}...")
        total_shares = None
        with self.engine.connect() as conn:
            date_condition = ""
            params = {'ts_code': self.ts_code}
            if valuation_date:
                date_condition = "AND trade_date <= :valuation_date"
                params['valuation_date'] = valuation_date

            # 从 valuation_metrics 获取 total_share
            query = text(f"""
                SELECT total_share 
                FROM valuation_metrics 
                WHERE ts_code = :ts_code {date_condition}
                ORDER BY trade_date DESC 
                LIMIT 1
            """)
            try:
                result = conn.execute(query, params)
                row = result.fetchone()
                if row is not None:
                    total_shares = pd.to_numeric(row._asdict().get('total_share'), errors='coerce')
                    # 确保 total_shares 是正数
                    if total_shares is not None and total_shares <= 0:
                         print(f"Warning: Fetched total_shares ({total_shares}) is not positive. Setting to None.")
                         total_shares = None
                    print(f"  Found latest total shares: {total_shares} from valuation_metrics")
                else:
                    print(f"  No total shares data found in valuation_metrics for {self.ts_code} up to {valuation_date or 'latest'}.")
            except Exception as e:
                print(f"Error fetching total shares from valuation_metrics: {e}")
        
        if pd.isna(total_shares):
            total_shares = None
            
        return total_shares


    def get_raw_financial_data(self, years: int = 5) -> Dict[str, pd.DataFrame]:
        """
        获取指定年限的原始财务报表数据 (年度报告)。
        返回包含 balance_sheet, income_statement, cash_flow DataFrame 的字典。
        """
        raw_data = {}
        current_year = pd.Timestamp.now().year
        start_year = current_year - years

        with self.engine.connect() as conn:
            # 获取资产负债表
            bs_query = text(f"""
                SELECT * FROM {self.balance_sheet_table}
                WHERE ts_code = :ts_code 
                AND EXTRACT(MONTH FROM end_date::timestamp) = 12
                AND EXTRACT(YEAR FROM end_date::timestamp) >= :start_year
                ORDER BY end_date DESC
            """)
            bs_result = conn.execute(bs_query, {'ts_code': self.ts_code, 'start_year': start_year})
            raw_data['balance_sheet'] = pd.DataFrame([row._asdict() for row in bs_result])
            if not raw_data['balance_sheet'].empty:
                 raw_data['balance_sheet']['end_date'] = pd.to_datetime(raw_data['balance_sheet']['end_date'])


            # 获取利润表
            is_query = text(f"""
                SELECT * FROM {self.income_statement_table}
                WHERE ts_code = :ts_code
                AND EXTRACT(MONTH FROM end_date::timestamp) = 12
                AND EXTRACT(YEAR FROM end_date::timestamp) >= :start_year
                ORDER BY end_date DESC
            """)
            is_result = conn.execute(is_query, {'ts_code': self.ts_code, 'start_year': start_year})
            raw_data['income_statement'] = pd.DataFrame([row._asdict() for row in is_result])
            if not raw_data['income_statement'].empty:
                 raw_data['income_statement']['end_date'] = pd.to_datetime(raw_data['income_statement']['end_date'])

            # 获取现金流量表
            cf_query = text(f"""
                SELECT * FROM {self.cash_flow_table}
                WHERE ts_code = :ts_code
                AND EXTRACT(MONTH FROM end_date::timestamp) = 12
                AND EXTRACT(YEAR FROM end_date::timestamp) >= :start_year
                ORDER BY end_date DESC
            """)
            cf_result = conn.execute(cf_query, {'ts_code': self.ts_code, 'start_year': start_year})
            raw_data['cash_flow'] = pd.DataFrame([row._asdict() for row in cf_result])
            if not raw_data['cash_flow'].empty:
                 raw_data['cash_flow']['end_date'] = pd.to_datetime(raw_data['cash_flow']['end_date'])

        print(f"Fetched raw financial data for {self.ts_code} for the last {years} years.")
        return raw_data
