from sqlalchemy import create_engine, text
import pandas as pd
from decimal import Decimal
import configparser

class DataFetcher:
    def __init__(self, ts_code):
        self.ts_code = ts_code
        
        # 读取配置文件
        config = configparser.ConfigParser()
        with open('config.ini', encoding='utf-8') as config_file:
            config.read_file(config_file)
        
        # 数据库连接
        user = config['DATABASE']['user']
        password = config['DATABASE']['password']
        host = config['DATABASE']['host']
        port = config['DATABASE']['port']
        database = config['DATABASE']['database']
        self.engine = create_engine(f'postgresql://{user}:{password}@{host}:{port}/{database}')
        
        # 表和字段配置项
        self.stock_basic_table = config['TABLES_AND_FIELDS']['stock_basic_table']
        self.stock_basic_fields = config['TABLES_AND_FIELDS']['stock_basic_fields'].split(',')
        
        self.daily_quotes_table = config['TABLES_AND_FIELDS']['daily_quotes_table']
        self.daily_quotes_fields = config['TABLES_AND_FIELDS']['daily_quotes_fields'].split(',')
        
        self.income_statement_table = config['TABLES_AND_FIELDS']['income_statement_table']
        self.income_statement_fields = config['TABLES_AND_FIELDS']['income_statement_fields'].split(',')
        
        self.financial_indicators_table = config['TABLES_AND_FIELDS']['financial_indicators_table']
        self.financial_indicators_fields = config['TABLES_AND_FIELDS']['financial_indicators_fields'].split(',')
        
        self.cash_flow_table = config['TABLES_AND_FIELDS']['cash_flow_table']
        self.cash_flow_fields = config['TABLES_AND_FIELDS']['cash_flow_fields'].split(',')
        
        self.balance_sheet_table = config['TABLES_AND_FIELDS']['balance_sheet_table']
        self.balance_sheet_fields = config['TABLES_AND_FIELDS']['balance_sheet_fields'].split(',')
        
        self.dividend_table = config['TABLES_AND_FIELDS']['dividend_table']
        self.dividend_fields = config['TABLES_AND_FIELDS']['dividend_fields'].split(',')
    
    def get_stock_info(self):
        """获取股票基本信息"""
        with self.engine.connect() as conn:
            fields_str = ', '.join(self.stock_basic_fields)
            query = text(f"SELECT {fields_str} FROM {self.stock_basic_table} WHERE ts_code = :ts_code")
            result = conn.execute(query, {'ts_code': self.ts_code})
            row = result.fetchone()
            if row is not None:
                return row._asdict()
            else:
                raise ValueError(f"No stock info found for ts_code: {self.ts_code}")
    
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
                raise ValueError(f"No total shares found for ts_code: {self.ts_code}")
    
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
