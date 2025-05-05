import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import pandas as pd
from decimal import Decimal
# import configparser # 不再需要

load_dotenv() # 加载 .env 文件中的环境变量

class DataFetcher:
    def __init__(self, ts_code):
        self.ts_code = ts_code
        
        # 不再需要读取 config.ini
        # config = configparser.ConfigParser()
        # try: # 添加 try-except 以防 config.ini 不存在
        #     with open('config.ini', encoding='utf-8') as config_file:
        #         config.read_file(config_file)
        # except FileNotFoundError:
        #     print("信息：config.ini 文件未找到，将使用环境变量和硬编码值。")
        #     config = None # 确保 config 为 None 或空对象

        # 从环境变量获取数据库连接信息
        db_user = os.getenv('DB_USER', 'default_user') # 移除 config.get 回退
        db_password = os.getenv('DB_PASSWORD', 'default_password') # 移除 config.get 回退
        db_host = os.getenv('DB_HOST', 'localhost') # 移除 config.get 回退
        db_port = os.getenv('DB_PORT', '5432') # 移除 config.get 回退
        db_name = os.getenv('DB_NAME', 'postgres') # 移除 config.get 回退

        # 检查是否成功获取环境变量，如果仍然是默认值或来自config的回退值，可能需要提示用户设置.env文件
        if db_user == 'default_user' or db_password == 'default_password':
             print("警告：未能从环境变量加载数据库用户名或密码。请确保已创建并正确配置 .env 文件。")

        self.engine = create_engine(f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}')

        # 表和字段配置项 (硬编码) - 从 config.ini.example 获取
        self.stock_basic_table = 'stock_basic'
        # 注意: get_stock_info 需要 'industry' 字段，确保它包含在内或在查询中单独处理
        self.stock_basic_fields = ['ts_code', 'name', 'industry'] 
        
        self.daily_quotes_table = 'daily_quotes'
        self.daily_quotes_fields = ['ts_code', 'close', 'trade_date']
        
        self.income_statement_table = 'income_statement'
        self.income_statement_fields = ['ts_code', 'end_date', 'n_income', 'revenue', 'total_revenue', 'oper_cost', 'operate_profit', 'non_oper_income', 'non_oper_exp']
        
        self.financial_indicators_table = 'financial_indicators'
        self.financial_indicators_fields = ['ts_code', 'end_date', 'eps', 'bps', 'roe', 'netprofit_margin', 'debt_to_assets']
        
        self.cash_flow_table = 'cash_flow'
        self.cash_flow_fields = ['ts_code', 'end_date', 'n_cashflow_act', 'stot_out_inv_act', 'stot_cash_in_fnc_act', 'stot_cashout_fnc_act', 'c_pay_acq_const_fiolta', 'c_paid_invest', 'decr_inventories', 'incr_oper_payable', 'decr_oper_payable', 'c_recp_borrow', 'c_prepay_amt_borr', 'depr_fa_coga_dpba', 'amort_intang_assets']
        
        self.balance_sheet_table = 'balance_sheet'
        self.balance_sheet_fields = ['ts_code', 'end_date', 'total_share', 'total_assets', 'total_liab', 'total_hldr_eqy_exc_min_int', 'total_cur_assets', 'total_cur_liab']
        
        self.dividend_table = 'dividend'
        self.dividend_fields = ['ts_code', 'end_date', 'cash_div_tax', 'ann_date', 'div_proc']
    
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
