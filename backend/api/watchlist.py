from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from pydantic import BaseModel

from database import get_db
from models import Watchlist
from core.data_fetcher import get_data_fetcher

router = APIRouter()

class WatchlistAdd(BaseModel):
    ts_code: str
    name: str
    asset_type: str = 'stock'

@router.get("/")
def get_watchlist(asset_type: str = None, db: Session = Depends(get_db)):
    query = db.query(Watchlist)
    if asset_type:
        query = query.filter(Watchlist.asset_type == asset_type)
    items = query.order_by(Watchlist.sort_order, Watchlist.created_at).all()
    return {"watchlist": [
        {
            "id": w.id,
            "ts_code": w.ts_code,
            "name": w.name,
            "asset_type": w.asset_type,
            "sort_order": w.sort_order,
            "created_at": w.created_at
        }
        for w in items
    ]}

@router.post("/")
def add_to_watchlist(data: WatchlistAdd, db: Session = Depends(get_db)):
    existing = db.query(Watchlist).filter(Watchlist.ts_code == data.ts_code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Asset already in watchlist")
    item = Watchlist(ts_code=data.ts_code, name=data.name, asset_type=data.asset_type)
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"id": item.id, "ts_code": item.ts_code, "name": item.name, "asset_type": item.asset_type}

@router.delete("/{ts_code}")
def remove_from_watchlist(ts_code: str, db: Session = Depends(get_db)):
    item = db.query(Watchlist).filter(Watchlist.ts_code == ts_code).first()
    if not item:
        raise HTTPException(status_code=404, detail="Asset not in watchlist")
    db.delete(item)
    db.commit()
    return {"success": True}

@router.get("/quotes")
def get_watchlist_quotes(db: Session = Depends(get_db)):
    items = db.query(Watchlist).all()
    if not items:
        return {"quotes": []}

    ts_codes = [w.ts_code for w in items]
    fetcher = get_data_fetcher()

    # Get real-time quotes
    quotes_df = fetcher.get_realtime_quotes(ts_codes)
    quotes_dict = {}
    if not quotes_df.empty:
        for _, row in quotes_df.iterrows():
            quotes_dict[row['TS_CODE']] = row.to_dict()

    # Get daily data for basics
    result = []
    for item in items:
        quote = quotes_dict.get(item.ts_code, {})
        asset_type = getattr(item, 'asset_type', 'stock')

        # 根据资产类型获取日线数据
        if asset_type == 'stock':
            daily_df = fetcher.get_daily_data(item.ts_code)
            daily_basic = fetcher.get_daily_basic_single(item.ts_code)
        else:
            daily_df = fetcher.get_fund_daily(item.ts_code)
            daily_basic = None  # 基金没有 daily_basic 数据

        quote_data = {
            "ts_code": item.ts_code,
            "name": item.name,
            "asset_type": asset_type,
            "price": float(quote.get('PRICE', 0)) if quote.get('PRICE') else None,
            "change_pct": None,
            "high": None,
            "low": None,
            "open": None,
            "close": None,
            "volume": None,
            "amount": None,
            "pe": None,
            "pb": None,
            "turnover": None
        }

        if not daily_df.empty:
            latest = daily_df.iloc[-1]
            prev = daily_df.iloc[-2] if len(daily_df) >= 2 else None
            quote_data.update({
                "close": float(latest['close']),
                "high": float(latest['high']),
                "low": float(latest['low']),
                "open": float(latest['open']),
                "volume": float(latest['vol']) if 'vol' in latest else None,
                "amount": float(latest['amount']) if 'amount' in latest else None
            })
            if prev is not None:
                quote_data["change_pct"] = (latest['close'] - prev['close']) / prev['close'] * 100

        if daily_basic:
            quote_data.update({
                "pe": daily_basic.get('pe'),
                "pb": daily_basic.get('pb'),
                "turnover": daily_basic.get('turnover_rate')
            })

        if quote_data['price'] is None:
            quote_data['price'] = quote_data['close']

        result.append(quote_data)

    return {"quotes": result}
