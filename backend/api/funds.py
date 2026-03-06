from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any

from core.data_fetcher import get_data_fetcher

router = APIRouter()

@router.get("/search")
def search_funds(keyword: str):
    """搜索基金"""
    if not keyword or len(keyword) < 1:
        return {"funds": []}
    fetcher = get_data_fetcher()
    df = fetcher.get_fund_search(keyword)
    return {"funds": df.to_dict('records') if not df.empty else []}

@router.get("/list")
def list_funds(fund_type: str = None, limit: int = 100):
    """获取基金列表"""
    fetcher = get_data_fetcher()
    df = fetcher.get_fund_list(fund_type)
    if not df.empty:
        df = df.head(limit)
    return {"funds": df.to_dict('records') if not df.empty else []}

@router.get("/{ts_code}/kline")
def get_fund_kline(ts_code: str):
    """获取基金K线数据"""
    fetcher = get_data_fetcher()
    result = fetcher.get_kline_data_unified(ts_code, asset_type='fund')
    df = result['data']
    if df.empty:
        raise HTTPException(status_code=404, detail="No k-line data available")

    return {
        "ts_code": ts_code,
        "freq": result['freq'],
        "x_data": df['trade_date'].tolist() if 'trade_date' in df.columns else [],
        "open": df['open'].tolist() if 'open' in df.columns else [],
        "high": df['high'].tolist() if 'high' in df.columns else [],
        "low": df['low'].tolist() if 'low' in df.columns else [],
        "close": df['close'].tolist() if 'close' in df.columns else [],
        "volume": df['vol'].tolist() if 'vol' in df.columns else []
    }
