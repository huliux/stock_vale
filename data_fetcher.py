from sqlalchemy import create_engine, text
import pandas as pd
from decimal import Decimal

class DataFetcher:
    def __init__(self, ts_code):
        self.ts_code = ts_code
        # 数据库连接
        user = 'matt'
        password = 'wq3395469'
        host = 'dasen.fun'
        port = '15432'
        database = 'postgres'
        self.engine = create_engine(f'postgresql://{user}:{password}@{host}:{port}/{database}')
    
    def get_stock_info(self):
        """获取股票基本信息"""
        with self.engine.connect() as conn:
            query = text(f"SELECT * FROM stock_basic WHERE ts_code = '{self.ts_code}'")
            result = conn.execute(query)
            row = result.fetchone()
            if row is not None:
                return row._asdict()
            else:
                raise ValueError(f"No stock info found for ts_code: {self.ts_code}")
    
    def get_latest_price(self):
        """获取最新收盘价"""
        with self.engine.connect() as conn:
            query = text(f"SELECT close FROM daily_quotes WHERE ts_code = '{self.ts_code}' ORDER BY trade_date DESC LIMIT 1")
            result = conn.execute(query)
            return float(result.fetchone()[0])
    
    def get_total_shares(self):
        """获取总股本"""
        with self.engine.connect() as conn:
            query = text(f"SELECT total_share FROM balance_sheet WHERE ts_code = '{self.ts_code}' ORDER BY end_date DESC LIMIT 1")
            result = conn.execute(query)
            return float(result.fetchone()[0])
    
    def get_financial_data(self):
        """获取历年财务数据"""
        # 获取年报数据
        with self.engine.connect() as conn:
            query = text(f"""
                SELECT 
                    i.end_date, 
                    EXTRACT(YEAR FROM i.end_date::timestamp) as year,
                    i.n_income, i.revenue, i.total_revenue, c.finan_exp,
                    i.oper_cost, i.operate_profit, i.non_oper_income, i.non_oper_exp,
                    f.eps, f.bps, f.roe, f.netprofit_margin, f.debt_to_assets,
                    c.n_cashflow_act, c.stot_out_inv_act, c.stot_cash_in_fnc_act, c.stot_cashout_fnc_act,
                    c.c_pay_acq_const_fiolta, c.c_paid_invest, c.decr_inventories,
                    c.incr_oper_payable, c.decr_oper_payable, c.c_recp_borrow, c.c_prepay_amt_borr,
                    c.depr_fa_coga_dpba, c.amort_intang_assets,
                    b.total_assets, b.total_liab, b.total_hldr_eqy_exc_min_int
                FROM income_statement i
                JOIN financial_indicators f ON i.ts_code = f.ts_code AND i.end_date = f.end_date
                JOIN cash_flow c ON i.ts_code = c.ts_code AND i.end_date = c.end_date
                JOIN balance_sheet b ON i.ts_code = b.ts_code AND i.end_date = b.end_date
                WHERE i.ts_code = '{self.ts_code}' 
                AND EXTRACT(MONTH FROM i.end_date::timestamp) = 12
                ORDER BY i.end_date DESC
            """)
            result = conn.execute(query)
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
            query = text(f"""
                SELECT 
                    end_date,
                    EXTRACT(YEAR FROM end_date::timestamp) as year,
                    cash_div_tax,
                    ann_date,
                    div_proc
                FROM dividend
                WHERE ts_code = '{self.ts_code}'
                ORDER BY end_date DESC
            """)
            result = conn.execute(query)
            
            data = []
            for row in result:
                data.append(row._asdict())
            
            df = pd.DataFrame(data)
            if not df.empty:
                # 将现金分红转为浮点数
                df['cash_div_tax'] = df['cash_div_tax'].astype(float)
            return df
