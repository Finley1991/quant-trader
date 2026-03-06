import tushare as ts
import pandas as pd
import numpy as np
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
        rs = np.where(loss != 0, gain / loss, np.inf)
        rsi = 100 - (100 / (1 + rs))
        return pd.Series(rsi, index=df.index)

    def get_realtime_quotes(self, ts_codes: List[str]) -> pd.DataFrame:
        """Get real-time quotes for multiple stocks"""
        if not ts_codes:
            return pd.DataFrame()
        ts_code_str = ','.join(ts_codes)
        try:
            df = ts.realtime_quote(ts_code=ts_code_str)
            return df
        except Exception:
            return pd.DataFrame()

    def get_stock_search(self, keyword: str) -> pd.DataFrame:
        """Search stocks by name or code"""
        df = self.get_stock_list()
        if df.empty:
            return df
        keyword = keyword.upper()
        mask = (df['ts_code'].str.contains(keyword, na=False) |
                df['name'].str.contains(keyword, na=False))
        return df[mask].head(50)

    def get_kline_data(self, ts_code: str, freq: str = 'auto') -> Dict[str, Any]:
        """Get k-line data with fallback strategy: 1min -> 5min -> daily"""
        result = {'freq': 'daily', 'data': pd.DataFrame()}

        # Try 1min first
        if freq in ['auto', '1min']:
            try:
                end_date = datetime.now().strftime('%Y%m%d')
                start_date = (datetime.now() - timedelta(days=7)).strftime('%Y%m%d')
                df = ts.pro_bar(ts_code=ts_code, asset='E', freq='1min',
                                start_date=start_date, end_date=end_date)
                if df is not None and not df.empty:
                    result['freq'] = '1min'
                    result['data'] = df.sort_values('trade_time').reset_index(drop=True)
                    return result
            except Exception:
                pass

        # Try 5min
        if freq in ['auto', '5min']:
            try:
                end_date = datetime.now().strftime('%Y%m%d')
                start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
                df = ts.pro_bar(ts_code=ts_code, asset='E', freq='5min',
                                start_date=start_date, end_date=end_date)
                if df is not None and not df.empty:
                    result['freq'] = '5min'
                    result['data'] = df.sort_values('trade_time').reset_index(drop=True)
                    return result
            except Exception:
                pass

        # Fallback to daily
        df = self.get_daily_data(ts_code)
        if not df.empty:
            result['freq'] = 'daily'
            result['data'] = df
        return result

    def get_daily_basic_single(self, ts_code: str, trade_date: str = None) -> Optional[Dict[str, Any]]:
        """Get daily basic data (PE, PB, turnover) for a single stock"""
        if trade_date is None:
            trade_date = datetime.now().strftime('%Y%m%d')
        try:
            df = self.pro.daily_basic(ts_code=ts_code, trade_date=trade_date)
            if not df.empty:
                return df.iloc[0].to_dict()
        except Exception:
            pass
        return None


_data_fetcher: Optional[DataFetcher] = None

def get_data_fetcher() -> DataFetcher:
    global _data_fetcher
    if _data_fetcher is None:
        _data_fetcher = DataFetcher()
    return _data_fetcher
