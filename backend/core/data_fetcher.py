import tushare as ts
import pandas as pd
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from config import settings

class DataFetcher:
    def __init__(self):
        if settings.TUSHARE_TOKEN:
            ts.set_token(settings.TUSHARE_TOKEN)
        self.pro = ts.pro_api()

    def get_stock_list(self) -> pd.DataFrame:
        df = self.pro.stock_basic(exchange='', list_status='L', fields='ts_code,name,industry,list_date')
        return df

    def get_daily_data(self, ts_code: str, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        if end_date is None:
            end_date = datetime.now().strftime('%Y%m%d')
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')

        df = self.pro.daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
        if not df.empty:
            df = df.sort_values('trade_date').reset_index(drop=True)
        return df

    def get_daily_basic(self, ts_code: str, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        if end_date is None:
            end_date = datetime.now().strftime('%Y%m%d')
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')

        df = self.pro.daily_basic(ts_code=ts_code, start_date=start_date, end_date=end_date)
        if not df.empty:
            df = df.sort_values('trade_date').reset_index(drop=True)
        return df

    def get_moneyflow(self, ts_code: str, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        if end_date is None:
            end_date = datetime.now().strftime('%Y%m%d')
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')

        df = self.pro.moneyflow(ts_code=ts_code, start_date=start_date, end_date=end_date)
        if not df.empty:
            df = df.sort_values('trade_date').reset_index(drop=True)
        return df

    def get_indicator(self, ts_code: str, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        if end_date is None:
            end_date = datetime.now().strftime('%Y%m%d')
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')

        df = self.pro.query('daily_basic', ts_code=ts_code, start_date=start_date, end_date=end_date)
        return df

    def get_financial_indicator(self, ts_code: str, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        df = self.pro.fina_indicator(ts_code=ts_code, start_date=start_date, end_date=end_date)
        if not df.empty:
            df = df.sort_values('end_date').reset_index(drop=True)
        return df

    def calculate_ma(self, df: pd.DataFrame, period: int) -> pd.Series:
        if df.empty or 'close' not in df.columns:
            return pd.Series()
        return df['close'].rolling(window=period).mean()

    def calculate_macd(self, df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, pd.Series]:
        if df.empty or 'close' not in df.columns:
            return {'dif': pd.Series(), 'dea': pd.Series(), 'macd': pd.Series()}

        exp1 = df['close'].ewm(span=fast, adjust=False).mean()
        exp2 = df['close'].ewm(span=slow, adjust=False).mean()
        dif = exp1 - exp2
        dea = dif.ewm(span=signal, adjust=False).mean()
        macd = (dif - dea) * 2

        return {'dif': dif, 'dea': dea, 'macd': macd}

    def calculate_rsi(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        if df.empty or 'close' not in df.columns:
            return pd.Series()

        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi


_data_fetcher: Optional[DataFetcher] = None

def get_data_fetcher() -> DataFetcher:
    global _data_fetcher
    if _data_fetcher is None:
        _data_fetcher = DataFetcher()
    return _data_fetcher
