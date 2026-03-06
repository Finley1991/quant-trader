import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from core.strategy_engine import BaseStrategy, StrategyRegistry, SignalType


class BacktestResult:
    def __init__(self):
        self.initial_capital: float = 0
        self.final_capital: float = 0
        self.total_return: float = 0
        self.max_drawdown: float = 0
        self.win_rate: float = 0
        self.sharpe_ratio: float = 0
        self.equity_curve: List[Dict[str, Any]] = []
        self.trades: List[Dict[str, Any]] = []


class BacktestEngine:
    def __init__(self, initial_capital: float = 100000, commission: float = 0.0003):
        self.initial_capital = initial_capital
        self.commission = commission

    def run(self, strategy: BaseStrategy, df: pd.DataFrame, ts_code: str = "") -> BacktestResult:
        result = BacktestResult()
        result.initial_capital = self.initial_capital

        if df.empty or len(df) < 60:
            result.final_capital = self.initial_capital
            return result

        df = df.copy().sort_values('trade_date').reset_index(drop=True)

        capital = self.initial_capital
        position = 0
        entry_price = 0
        entry_date = ""
        equity_history = []
        trades = []
        wins = 0
        total_trades = 0

        df['ma5'] = df['close'].rolling(5).mean()
        df['ma20'] = df['close'].rolling(20).mean()

        for i in range(30, len(df)):
            slice_df = df.iloc[:i+1].copy()

            signals = strategy.generate_signals(slice_df, ts_code)

            current_price = float(df.loc[i, 'close'])
            current_date = df.loc[i, 'trade_date']

            for signal in signals.signals:
                if signal['signal_type'] == SignalType.BUY.value and position == 0:
                    shares = int(capital / current_price / 100) * 100
                    if shares >= 100:
                        cost = shares * current_price * (1 + self.commission)
                        if cost <= capital:
                            position = shares
                            entry_price = current_price
                            entry_date = current_date
                            capital -= cost

                elif signal['signal_type'] == SignalType.SELL.value and position > 0:
                    proceeds = position * current_price * (1 - self.commission)
                    capital += proceeds

                    pnl = (current_price - entry_price) * position
                    total_trades += 1
                    if pnl > 0:
                        wins += 1

                    trades.append({
                        'ts_code': ts_code,
                        'entry_date': entry_date,
                        'entry_price': entry_price,
                        'exit_date': current_date,
                        'exit_price': current_price,
                        'pnl': pnl,
                        'pnl_pct': (current_price - entry_price) / entry_price
                    })

                    position = 0
                    entry_price = 0

            total_equity = capital + position * current_price
            equity_history.append({
                'date': current_date,
                'equity': total_equity,
                'close': current_price
            })

        if position > 0:
            proceeds = position * float(df.loc[len(df)-1, 'close']) * (1 - self.commission)
            capital += proceeds
            position = 0

        result.final_capital = capital
        result.total_return = (capital - self.initial_capital) / self.initial_capital * 100
        result.equity_curve = equity_history
        result.trades = trades

        if equity_history:
            peak = self.initial_capital
            drawdowns = []
            for point in equity_history:
                equity = point['equity']
                if equity > peak:
                    peak = equity
                drawdown = (peak - equity) / peak * 100
                drawdowns.append(drawdown)
            result.max_drawdown = max(drawdowns) if drawdowns else 0

        if total_trades > 0:
            result.win_rate = wins / total_trades * 100

        if len(equity_history) > 20:
            returns = []
            for i in range(1, len(equity_history)):
                prev = equity_history[i-1]['equity']
                curr = equity_history[i]['equity']
                if prev > 0:
                    returns.append((curr - prev) / prev)

            if returns:
                avg_return = np.mean(returns)
                std_return = np.std(returns)
                if std_return > 0:
                    result.sharpe_ratio = avg_return / std_return * np.sqrt(252)

        return result
