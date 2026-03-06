from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional

from core.data_fetcher import get_data_fetcher

router = APIRouter()

@router.get("/search")
def search_stocks(keyword: str):
    if not keyword or len(keyword) < 1:
        return {"stocks": []}
    fetcher = get_data_fetcher()
    df = fetcher.get_stock_search(keyword)
    return {"stocks": df.to_dict('records') if not df.empty else []}

@router.get("/list")
def list_stocks(limit: int = 100):
    fetcher = get_data_fetcher()
    df = fetcher.get_stock_list()
    if not df.empty:
        df = df.head(limit)
    return {"stocks": df.to_dict('records') if not df.empty else []}

@router.get("/{ts_code}/kline")
def get_kline(ts_code: str, freq: str = "auto"):
    fetcher = get_data_fetcher()
    result = fetcher.get_kline_data(ts_code, freq)
    df = result['data']
    if df.empty:
        raise HTTPException(status_code=404, detail="No k-line data available")

    # Prepare chart data
    if result['freq'] == 'daily':
        x_data = df['trade_date'].tolist()
    else:
        x_data = df['trade_time'].tolist() if 'trade_time' in df.columns else df['trade_date'].tolist()

    return {
        "ts_code": ts_code,
        "freq": result['freq'],
        "x_data": x_data,
        "open": df['open'].tolist() if 'open' in df.columns else [],
        "high": df['high'].tolist() if 'high' in df.columns else [],
        "low": df['low'].tolist() if 'low' in df.columns else [],
        "close": df['close'].tolist() if 'close' in df.columns else [],
        "volume": df['vol'].tolist() if 'vol' in df.columns else []
    }
