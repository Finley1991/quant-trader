from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from datetime import datetime, timedelta

from database import get_db
from models import Signal as DBSignal, Stock as DBStock, Strategy as DBStrategy
from core.strategy_engine import StrategyRegistry, register_all_strategies
from core.data_fetcher import get_data_fetcher
from core.notifier import get_notifier

router = APIRouter()

register_all_strategies()

@router.get("/")
def get_signals(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    signals = db.query(DBSignal).order_by(DBSignal.created_at.desc()).offset(skip).limit(limit).all()
    return {"signals": [
        {
            "id": s.id,
            "ts_code": s.ts_code,
            "name": s.name,
            "strategy_name": s.strategy_name,
            "signal_type": s.signal_type,
            "price": s.price,
            "signal_date": s.signal_date,
            "is_sent": s.is_sent,
            "created_at": s.created_at
        }
        for s in signals
    ]}

@router.get("/today")
def get_today_signals(db: Session = Depends(get_db)):
    today = datetime.now().strftime('%Y%m%d')
    signals = db.query(DBSignal).filter(DBSignal.signal_date == today).order_by(DBSignal.created_at.desc()).all()
    return {"signals": [
        {
            "id": s.id,
            "ts_code": s.ts_code,
            "name": s.name,
            "strategy_name": s.strategy_name,
            "signal_type": s.signal_type,
            "price": s.price,
            "signal_date": s.signal_date
        }
        for s in signals
    ]}

def scan_all_stocks(db: Session):
    fetcher = get_data_fetcher()
    notifier = get_notifier()

    stock_list = fetcher.get_stock_list()
    if stock_list.empty:
        return {"scanned": 0, "signals": 0}

    strategies = StrategyRegistry.list_strategies()
    today = datetime.now().strftime('%Y%m%d')
    signal_count = 0

    for idx, stock in stock_list.head(100).iterrows():
        ts_code = stock['ts_code']
        name = stock['name']

        df = fetcher.get_daily_data(ts_code)
        if df.empty or len(df) < 30:
            continue

        for strat_info in strategies:
            strategy_class = StrategyRegistry.get_strategy(strat_info['name'])
            if not strategy_class:
                continue

            strategy = strategy_class()
            result = strategy.generate_signals(df, ts_code, name)

            for signal in result.signals:
                existing = db.query(DBSignal).filter(
                    DBSignal.ts_code == ts_code,
                    DBSignal.strategy_name == signal['strategy_name'],
                    DBSignal.signal_date == signal['date']
                ).first()

                if not existing:
                    db_signal = DBSignal(
                        ts_code=signal['ts_code'],
                        name=signal.get('name', ''),
                        strategy_name=signal['strategy_name'],
                        signal_type=signal['signal_type'],
                        price=signal['price'],
                        signal_date=signal['date'],
                        is_sent=False
                    )
                    db.add(db_signal)
                    db.commit()

                    notifier.send_signal_notification(signal)
                    db_signal.is_sent = True
                    db.commit()
                    signal_count += 1

    return {"scanned": len(stock_list.head(100)), "signals": signal_count}

@router.post("/scan")
def trigger_scan(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    result = scan_all_stocks(db)
    return result
