from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta

from database import get_db
from models import Backtest as DBBacktest
from core.strategy_engine import StrategyRegistry
from core.backtest_engine import BacktestEngine
from core.data_fetcher import get_data_fetcher

router = APIRouter()

class BacktestRequest(BaseModel):
    strategy_name: str
    ts_code: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    initial_capital: float = 100000
    params: Optional[Dict[str, Any]] = None

@router.post("/")
def run_backtest(request: BacktestRequest, db: Session = Depends(get_db)):
    strategy_class = StrategyRegistry.get_strategy(request.strategy_name)
    if not strategy_class:
        raise HTTPException(status_code=404, detail="Strategy not found")

    strategy = strategy_class(request.params or {})

    fetcher = get_data_fetcher()
    df = fetcher.get_daily_data(request.ts_code, request.start_date, request.end_date)

    if df.empty:
        raise HTTPException(status_code=400, detail="No data available")

    engine = BacktestEngine(initial_capital=request.initial_capital)
    result = engine.run(strategy, df, request.ts_code)

    backtest = DBBacktest(
        strategy_name=request.strategy_name,
        start_date=request.start_date or df['trade_date'].min(),
        end_date=request.end_date or df['trade_date'].max(),
        initial_capital=request.initial_capital,
        final_capital=result.final_capital,
        total_return=result.total_return,
        max_drawdown=result.max_drawdown,
        win_rate=result.win_rate,
        sharpe_ratio=result.sharpe_ratio,
        equity_curve=result.equity_curve
    )
    db.add(backtest)
    db.commit()

    return {
        "backtest_id": backtest.id,
        "initial_capital": result.initial_capital,
        "final_capital": result.final_capital,
        "total_return": result.total_return,
        "max_drawdown": result.max_drawdown,
        "win_rate": result.win_rate,
        "sharpe_ratio": result.sharpe_ratio,
        "equity_curve": result.equity_curve
    }

@router.get("/history")
def get_backtest_history(db: Session = Depends(get_db)):
    backtests = db.query(DBBacktest).order_by(DBBacktest.created_at.desc()).limit(20).all()
    return {"backtests": [
        {
            "id": b.id,
            "strategy_name": b.strategy_name,
            "start_date": b.start_date,
            "end_date": b.end_date,
            "total_return": b.total_return,
            "max_drawdown": b.max_drawdown,
            "win_rate": b.win_rate,
            "created_at": b.created_at
        }
        for b in backtests
    ]}

@router.get("/{backtest_id}")
def get_backtest(backtest_id: int, db: Session = Depends(get_db)):
    backtest = db.query(DBBacktest).filter(DBBacktest.id == backtest_id).first()
    if not backtest:
        raise HTTPException(status_code=404, detail="Backtest not found")
    return {
        "id": backtest.id,
        "strategy_name": backtest.strategy_name,
        "initial_capital": backtest.initial_capital,
        "final_capital": backtest.final_capital,
        "total_return": backtest.total_return,
        "max_drawdown": backtest.max_drawdown,
        "win_rate": backtest.win_rate,
        "sharpe_ratio": backtest.sharpe_ratio,
        "equity_curve": backtest.equity_curve
    }
