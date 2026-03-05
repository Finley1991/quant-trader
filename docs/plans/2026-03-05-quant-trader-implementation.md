# Quant Trader Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a quantitative trading strategy tool with preset strategies, backtesting, and real-time signals with DingTalk notifications.

**Architecture:** FastAPI backend with SQLite, Vue 3 frontend, Tushare data source, separated into bite-sized tasks.

**Tech Stack:** FastAPI, SQLAlchemy, Vue 3, Element Plus, ECharts, Tushare, APScheduler

---

## Task 1: Project Setup - Backend

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/config.py`
- Create: `backend/database.py`
- Create: `backend/models.py`
- Create: `backend/main.py`

**Step 1: Create project directories**
```bash
mkdir -p /Users/wyf-mac/Documents/code/claudecode/quant-trader/backend
mkdir -p /Users/wyf-mac/Documents/code/claudecode/quant-trader/backend/api
mkdir -p /Users/wyf-mac/Documents/code/claudecode/quant-trader/backend/core
mkdir -p /Users/wyf-mac/Documents/code/claudecode/quant-trader/backend/strategies
```

**Step 2: Create requirements.txt**
```txt
fastapi==0.109.0
uvicorn[standard]==0.27.0
sqlalchemy==2.0.25
pandas==2.1.4
numpy==1.26.3
tushare==1.4.5
apscheduler==3.10.4
pydantic==2.5.3
pydantic-settings==2.1.0
python-multipart==0.0.6
```

**Step 3: Create config.py**
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Tushare
    TUSHARE_TOKEN: str = ""

    # DingTalk
    DINGTALK_WEBHOOK: str = ""
    DINGTALK_SECRET: str = ""

    # Email (phase 2)
    EMAIL_SMTP_HOST: str = ""
    EMAIL_SMTP_PORT: int = 587
    EMAIL_USER: str = ""
    EMAIL_PASSWORD: str = ""

    # Database
    DATABASE_URL: str = "sqlite:///./quant_trader.db"

    # Application
    APP_NAME: str = "Quant Trader"
    DEBUG: bool = True

    class Config:
        env_file = ".env"

settings = Settings()
```

**Step 4: Create database.py**
```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from config import settings

engine = create_engine(
    settings.DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**Step 5: Create models.py**
```python
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, JSON
from sqlalchemy.sql import func
from database import Base

class Stock(Base):
    __tablename__ = "stocks"

    id = Column(Integer, primary_key=True, index=True)
    ts_code = Column(String, unique=True, index=True)
    name = Column(String)
    industry = Column(String, nullable=True)
    list_date = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Strategy(Base):
    __tablename__ = "strategies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    type = Column(String)
    params = Column(JSON)
    is_active = Column(Boolean, default=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Backtest(Base):
    __tablename__ = "backtests"

    id = Column(Integer, primary_key=True, index=True)
    strategy_id = Column(Integer, index=True)
    strategy_name = Column(String)
    start_date = Column(String)
    end_date = Column(String)
    initial_capital = Column(Float)
    final_capital = Column(Float)
    total_return = Column(Float)
    max_drawdown = Column(Float)
    win_rate = Column(Float, nullable=True)
    sharpe_ratio = Column(Float, nullable=True)
    equity_curve = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Signal(Base):
    __tablename__ = "signals"

    id = Column(Integer, primary_key=True, index=True)
    ts_code = Column(String, index=True)
    name = Column(String, nullable=True)
    strategy_id = Column(Integer, index=True)
    strategy_name = Column(String)
    signal_type = Column(String)
    price = Column(Float)
    signal_date = Column(String)
    signal_time = Column(String, nullable=True)
    is_sent = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Config(Base):
    __tablename__ = "configs"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True)
    value = Column(Text)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

**Step 6: Create main.py**
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from database import engine, Base
from api import strategies, backtest, signals, notify

Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.APP_NAME, debug=settings.DEBUG)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(strategies.router, prefix="/api/strategies", tags=["strategies"])
app.include_router(backtest.router, prefix="/api/backtest", tags=["backtest"])
app.include_router(signals.router, prefix="/api/signals", tags=["signals"])
app.include_router(notify.router, prefix="/api/notify", tags=["notify"])

@app.get("/")
def root():
    return {"message": "Quant Trader API", "version": "1.0.0"}

@app.get("/health")
def health():
    return {"status": "healthy"}
```

**Step 7: Create empty api/__init__.py**
```python
# Empty
```

---

## Task 2: Data Fetcher Module

**Files:**
- Create: `backend/core/data_fetcher.py`

**Step 1: Create data_fetcher.py**
```python
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
```

---

## Task 3: Strategy Engine & Preset Strategies

**Files:**
- Create: `backend/core/strategy_engine.py`
- Create: `backend/strategies/technical.py`
- Create: `backend/strategies/multi_factor.py`
- Create: `backend/strategies/__init__.py`

**Step 1: Create strategy_engine.py**
```python
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum

class SignalType(Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"

class StrategyResult:
    def __init__(self):
        self.signals: List[Dict[str, Any]] = []

    def add_signal(self, ts_code: str, name: Optional[str], signal_type: SignalType,
                   price: float, date: str, strategy_name: str, strategy_id: Optional[int] = None):
        self.signals.append({
            'ts_code': ts_code,
            'name': name or '',
            'signal_type': signal_type.value,
            'price': price,
            'date': date,
            'strategy_name': strategy_name,
            'strategy_id': strategy_id
        })

class BaseStrategy:
    name: str = ""
    type: str = ""
    description: str = ""
    default_params: Dict[str, Any] = {}

    def __init__(self, params: Optional[Dict[str, Any]] = None):
        self.params = {**self.default_params, **(params or {})}

    def generate_signals(self, df: pd.DataFrame, ts_code: str, name: Optional[str] = None) -> StrategyResult:
        raise NotImplementedError()

    def get_param(self, key: str, default: Any = None):
        return self.params.get(key, default)


class StrategyRegistry:
    _strategies: Dict[str, type] = {}

    @classmethod
    def register(cls, strategy_class: type):
        cls._strategies[strategy_class.name] = strategy_class
        return strategy_class

    @classmethod
    def get_strategy(cls, name: str) -> Optional[type]:
        return cls._strategies.get(name)

    @classmethod
    def list_strategies(cls) -> List[Dict[str, Any]]:
        return [
            {
                'name': s.name,
                'type': s.type,
                'description': s.description,
                'default_params': s.default_params
            }
            for s in cls._strategies.values()
        ]


def register_all_strategies():
    from strategies.technical import (
        MovingAverageCrossover,
        RSIStrategy,
        MomentumBreakout
    )
    from strategies.multi_factor import (
        MultiFactorStrategy,
        MoneyFlowStrategy
    )
```

**Step 2: Create strategies/__init__.py**
```python
from .technical import MovingAverageCrossover, RSIStrategy, MomentumBreakout
from .multi_factor import MultiFactorStrategy, MoneyFlowStrategy

__all__ = [
    'MovingAverageCrossover',
    'RSIStrategy',
    'MomentumBreakout',
    'MultiFactorStrategy',
    'MoneyFlowStrategy'
]
```

**Step 3: Create strategies/technical.py**
```python
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from core.strategy_engine import (
    BaseStrategy, StrategyRegistry, StrategyResult, SignalType
)
from core.data_fetcher import get_data_fetcher


@StrategyRegistry.register
class MovingAverageCrossover(BaseStrategy):
    name = "均线双金叉"
    type = "technical"
    description = "MA5上穿MA20 + MACD金叉"
    default_params = {
        'ma_fast': 5,
        'ma_slow': 20,
        'macd_fast': 12,
        'macd_slow': 26,
        'macd_signal': 9
    }

    def generate_signals(self, df: pd.DataFrame, ts_code: str, name: Optional[str] = None) -> StrategyResult:
        result = StrategyResult()
        if df.empty or len(df) < 30:
            return result

        fetcher = get_data_fetcher()

        ma_fast = self.get_param('ma_fast', 5)
        ma_slow = self.get_param('ma_slow', 20)

        df = df.copy().sort_values('trade_date').reset_index(drop=True)
        df['ma_fast'] = df['close'].rolling(ma_fast).mean()
        df['ma_slow'] = df['close'].rolling(ma_slow).mean()

        macd_data = fetcher.calculate_macd(df)
        df['dif'] = macd_data['dif']
        df['dea'] = macd_data['dea']

        if len(df) < 2:
            return result

        i = len(df) - 1
        prev = i - 1

        ma_cross_up = (df.loc[prev, 'ma_fast'] <= df.loc[prev, 'ma_slow'] and
                       df.loc[i, 'ma_fast'] > df.loc[i, 'ma_slow'])

        macd_cross_up = (df.loc[prev, 'dif'] <= df.loc[prev, 'dea'] and
                         df.loc[i, 'dif'] > df.loc[i, 'dea'])

        if ma_cross_up and macd_cross_up:
            result.add_signal(
                ts_code=ts_code,
                name=name,
                signal_type=SignalType.BUY,
                price=float(df.loc[i, 'close']),
                date=df.loc[i, 'trade_date'],
                strategy_name=self.name
            )

        ma_cross_down = (df.loc[prev, 'ma_fast'] >= df.loc[prev, 'ma_slow'] and
                         df.loc[i, 'ma_fast'] < df.loc[i, 'ma_slow'])

        if ma_cross_down:
            result.add_signal(
                ts_code=ts_code,
                name=name,
                signal_type=SignalType.SELL,
                price=float(df.loc[i, 'close']),
                date=df.loc[i, 'trade_date'],
                strategy_name=self.name
            )

        return result


@StrategyRegistry.register
class RSIStrategy(BaseStrategy):
    name = "RSI超跌反弹"
    type = "technical"
    description = "RSI < 30 后拐头向上"
    default_params = {
        'rsi_period': 14,
        'oversold_threshold': 30,
        'overbought_threshold': 70
    }

    def generate_signals(self, df: pd.DataFrame, ts_code: str, name: Optional[str] = None) -> StrategyResult:
        result = StrategyResult()
        if df.empty or len(df) < 30:
            return result

        fetcher = get_data_fetcher()
        df = df.copy().sort_values('trade_date').reset_index(drop=True)
        df['rsi'] = fetcher.calculate_rsi(df, self.get_param('rsi_period', 14))

        oversold = self.get_param('oversold_threshold', 30)
        overbought = self.get_param('overbought_threshold', 70)

        if len(df) < 3:
            return result

        i = len(df) - 1
        prev = i - 1
        prev2 = i - 2

        if (df.loc[prev2, 'rsi'] < oversold and
            df.loc[prev, 'rsi'] < oversold and
            df.loc[i, 'rsi'] > df.loc[prev, 'rsi']):
            result.add_signal(
                ts_code=ts_code,
                name=name,
                signal_type=SignalType.BUY,
                price=float(df.loc[i, 'close']),
                date=df.loc[i, 'trade_date'],
                strategy_name=self.name
            )

        if df.loc[prev, 'rsi'] > overbought and df.loc[i, 'rsi'] < overbought:
            result.add_signal(
                ts_code=ts_code,
                name=name,
                signal_type=SignalType.SELL,
                price=float(df.loc[i, 'close']),
                date=df.loc[i, 'trade_date'],
                strategy_name=self.name
            )

        return result


@StrategyRegistry.register
class MomentumBreakout(BaseStrategy):
    name = "动量突破"
    type = "technical"
    description = "价格突破20日新高 + 成交量放大"
    default_params = {
        'lookback_period': 20,
        'volume_ratio': 1.5
    }

    def generate_signals(self, df: pd.DataFrame, ts_code: str, name: Optional[str] = None) -> StrategyResult:
        result = StrategyResult()
        lookback = self.get_param('lookback_period', 20)
        volume_ratio = self.get_param('volume_ratio', 1.5)

        if df.empty or len(df) < lookback + 5:
            return result

        df = df.copy().sort_values('trade_date').reset_index(drop=True)

        i = len(df) - 1
        if i < lookback:
            return result

        recent_high = df.loc[i-lookback:i-1, 'high'].max()
        avg_volume = df.loc[i-10:i-1, 'vol'].mean()

        if df.loc[i, 'close'] > recent_high and df.loc[i, 'vol'] > avg_volume * volume_ratio:
            result.add_signal(
                ts_code=ts_code,
                name=name,
                signal_type=SignalType.BUY,
                price=float(df.loc[i, 'close']),
                date=df.loc[i, 'trade_date'],
                strategy_name=self.name
            )

        return result
```

**Step 4: Create strategies/multi_factor.py**
```python
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from core.strategy_engine import (
    BaseStrategy, StrategyRegistry, StrategyResult, SignalType
)
from core.data_fetcher import get_data_fetcher


@StrategyRegistry.register
class MultiFactorStrategy(BaseStrategy):
    name = "基本面+技术面"
    type = "multi_factor"
    description = "PE/PB合理 + ROE > 15% + 均线多头"
    default_params = {
        'min_roe': 15,
        'max_pe': 50,
        'min_pe': 5,
        'max_pb': 5,
        'min_pb': 0.5
    }

    def generate_signals(self, df: pd.DataFrame, ts_code: str, name: Optional[str] = None) -> StrategyResult:
        result = StrategyResult()
        if df.empty or len(df) < 30:
            return result

        fetcher = get_data_fetcher()
        df = df.copy().sort_values('trade_date').reset_index(drop=True)

        df['ma5'] = df['close'].rolling(5).mean()
        df['ma10'] = df['close'].rolling(10).mean()
        df['ma20'] = df['close'].rolling(20).mean()

        min_roe = self.get_param('min_roe', 15)
        max_pe = self.get_param('max_pe', 50)
        min_pe = self.get_param('min_pe', 5)
        max_pb = self.get_param('max_pb', 5)
        min_pb = self.get_param('min_pb', 0.5)

        i = len(df) - 1
        if i < 20:
            return result

        ma_trend = (df.loc[i, 'ma5'] > df.loc[i, 'ma10'] and
                    df.loc[i, 'ma10'] > df.loc[i, 'ma20'] and
                    df.loc[i, 'close'] > df.loc[i, 'ma5'])

        if 'pe' in df.columns and 'pb' in df.columns:
            pe_ok = min_pe <= df.loc[i, 'pe'] <= max_pe
            pb_ok = min_pb <= df.loc[i, 'pb'] <= max_pb
        else:
            pe_ok = True
            pb_ok = True

        if ma_trend and pe_ok and pb_ok:
            result.add_signal(
                ts_code=ts_code,
                name=name,
                signal_type=SignalType.BUY,
                price=float(df.loc[i, 'close']),
                date=df.loc[i, 'trade_date'],
                strategy_name=self.name
            )

        return result


@StrategyRegistry.register
class MoneyFlowStrategy(BaseStrategy):
    name = "量价齐升"
    type = "multi_factor"
    description = "主力连续3天净流入 + 价格站上MA20"
    default_params = {
        'consecutive_days': 3,
        'ma_period': 20
    }

    def generate_signals(self, df: pd.DataFrame, ts_code: str, name: Optional[str] = None) -> StrategyResult:
        result = StrategyResult()
        consecutive_days = self.get_param('consecutive_days', 3)
        ma_period = self.get_param('ma_period', 20)

        if df.empty or len(df) < ma_period + consecutive_days:
            return result

        df = df.copy().sort_values('trade_date').reset_index(drop=True)
        df['ma'] = df['close'].rolling(ma_period).mean()

        i = len(df) - 1
        if i < ma_period + consecutive_days:
            return result

        above_ma = df.loc[i, 'close'] > df.loc[i, 'ma']

        volume_increasing = True
        for j in range(consecutive_days):
            idx = i - j
            if idx < 1:
                volume_increasing = False
                break
            if df.loc[idx, 'vol'] < df.loc[idx - 1, 'vol']:
                volume_increasing = False
                break

        if above_ma and volume_increasing:
            result.add_signal(
                ts_code=ts_code,
                name=name,
                signal_type=SignalType.BUY,
                price=float(df.loc[i, 'close']),
                date=df.loc[i, 'trade_date'],
                strategy_name=self.name
            )

        return result
```

---

## Task 4: Backtest Engine

**Files:**
- Create: `backend/core/backtest_engine.py`

**Step 1: Create backtest_engine.py**
```python
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from core.strategy_engine import BaseStrategy, StrategyRegistry, SignalType
from core.data_fetcher import get_data_fetcher


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
```

---

## Task 5: Notifier Module

**Files:**
- Create: `backend/core/notifier.py`

**Step 1: Create notifier.py**
```python
import requests
import hashlib
import base64
import hmac
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional
from datetime import datetime

from config import settings


class Notifier:
    def __init__(self):
        self.dingtalk_webhook = settings.DINGTALK_WEBHOOK
        self.dingtalk_secret = settings.DINGTALK_SECRET

    def _generate_dingtalk_sign(self, timestamp: str) -> str:
        secret_enc = self.dingtalk_secret.encode('utf-8')
        string_to_sign = f'{timestamp}\n{self.dingtalk_secret}'
        string_to_sign_enc = string_to_sign.encode('utf-8')
        hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
        sign = base64.b64encode(hmac_code).decode('utf-8')
        return sign

    def send_dingtalk(self, title: str, text: str) -> bool:
        if not self.dingtalk_webhook:
            return False

        timestamp = str(round(time.time() * 1000))
        sign = ""

        if self.dingtalk_secret:
            sign = self._generate_dingtalk_sign(timestamp)

        url = self.dingtalk_webhook
        if sign:
            url += f"&timestamp={timestamp}&sign={sign}"

        headers = {'Content-Type': 'application/json'}
        data = {
            "msgtype": "markdown",
            "markdown": {
                "title": title,
                "text": f"### {title}\n\n{text}"
            }
        }

        try:
            response = requests.post(url, json=data, headers=headers, timeout=10)
            return response.status_code == 200
        except Exception:
            return False

    def send_email(self, to_email: str, subject: str, content: str) -> bool:
        if not settings.EMAIL_SMTP_HOST:
            return False

        try:
            msg = MIMEMultipart()
            msg['From'] = settings.EMAIL_USER
            msg['To'] = to_email
            msg['Subject'] = subject

            msg.attach(MIMEText(content, 'plain', 'utf-8'))

            with smtplib.SMTP(settings.EMAIL_SMTP_HOST, settings.EMAIL_SMTP_PORT) as server:
                server.starttls()
                server.login(settings.EMAIL_USER, settings.EMAIL_PASSWORD)
                server.send_message(msg)

            return True
        except Exception:
            return False

    def send_signal_notification(self, signal: Dict[str, Any]) -> bool:
        title = f"【{signal['signal_type']}】{signal['name'] or signal['ts_code']}"
        text = f"""
**股票代码**: {signal['ts_code']}
**股票名称**: {signal.get('name', '-')}
**策略**: {signal['strategy_name']}
**信号类型**: {signal['signal_type']}
**触发价格**: {signal['price']:.2f}
**触发日期**: {signal['date']}
**时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        return self.send_dingtalk(title, text)


_notifier: Optional[Notifier] = None

def get_notifier() -> Notifier:
    global _notifier
    if _notifier is None:
        _notifier = Notifier()
    return _notifier
```

---

## Task 6: API Endpoints

**Files:**
- Create: `backend/api/strategies.py`
- Create: `backend/api/backtest.py`
- Create: `backend/api/signals.py`
- Create: `backend/api/notify.py`

**Step 1: Create api/strategies.py**
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from database import get_db
from models import Strategy as DBStrategy
from core.strategy_engine import StrategyRegistry, register_all_strategies
from pydantic import BaseModel

router = APIRouter()

register_all_strategies()

class StrategyCreate(BaseModel):
    name: str
    type: str
    params: Dict[str, Any]
    description: str = ""

@router.get("/presets")
def get_preset_strategies():
    return {"strategies": StrategyRegistry.list_strategies()}

@router.get("/")
def get_strategies(db: Session = Depends(get_db)):
    strategies = db.query(DBStrategy).all()
    return {"strategies": [
        {
            "id": s.id,
            "name": s.name,
            "type": s.type,
            "params": s.params,
            "is_active": s.is_active,
            "description": s.description
        }
        for s in strategies
    ]}

@router.post("/")
def create_strategy(data: StrategyCreate, db: Session = Depends(get_db)):
    strategy = DBStrategy(
        name=data.name,
        type=data.type,
        params=data.params,
        description=data.description,
        is_active=True
    )
    db.add(strategy)
    db.commit()
    db.refresh(strategy)
    return {"id": strategy.id, "name": strategy.name}

@router.put("/{strategy_id}/toggle")
def toggle_strategy(strategy_id: int, db: Session = Depends(get_db)):
    strategy = db.query(DBStrategy).filter(DBStrategy.id == strategy_id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    strategy.is_active = not strategy.is_active
    db.commit()
    return {"id": strategy.id, "is_active": strategy.is_active}
```

**Step 2: Create api/backtest.py**
```python
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
```

**Step 3: Create api/signals.py**
```python
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
```

**Step 4: Create api/notify.py**
```python
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Dict, Any, Optional

from core.notifier import get_notifier
from config import settings

router = APIRouter()

class NotifyRequest(BaseModel):
    title: str
    text: str

class SettingsUpdate(BaseModel):
    tushare_token: Optional[str] = None
    dingtalk_webhook: Optional[str] = None
    dingtalk_secret: Optional[str] = None

@router.post("/test")
def test_notification(request: NotifyRequest):
    notifier = get_notifier()
    success = notifier.send_dingtalk(request.title, request.text)
    return {"success": success}

@router.get("/settings")
def get_settings():
    return {
        "tushare_token_set": bool(settings.TUSHARE_TOKEN),
        "dingtalk_webhook_set": bool(settings.DINGTALK_WEBHOOK),
        "dingtalk_secret_set": bool(settings.DINGTALK_SECRET)
    }

@router.post("/settings")
def update_settings(data: SettingsUpdate):
    if data.tushare_token:
        settings.TUSHARE_TOKEN = data.tushare_token
    if data.dingtalk_webhook:
        settings.DINGTALK_WEBHOOK = data.dingtalk_webhook
    if data.dingtalk_secret:
        settings.DINGTALK_SECRET = data.dingtalk_secret

    return {"success": True}
```

---

## Task 7: Frontend Setup

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.js`
- Create: `frontend/index.html`
- Create: `frontend/src/main.js`
- Create: `frontend/src/App.vue`
- Create: `frontend/src/api/index.js`
- Create: `frontend/src/router/index.js`

**Step 1: Create package.json**
```json
{
  "name": "quant-trader-frontend",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "vue": "^3.4.15",
    "vue-router": "^4.2.5",
    "pinia": "^2.1.7",
    "axios": "^1.6.7",
    "element-plus": "^2.5.6",
    "echarts": "^5.5.0"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^5.0.3",
    "vite": "^5.0.12"
  }
}
```

**Step 2: Create vite.config.js**
```js
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
})
```

**Step 3: Create index.html**
```html
<!DOCTYPE html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8">
    <link rel="icon" type="image/svg+xml" href="/vite.svg">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Quant Trader</title>
  </head>
  <body>
    <div id="app"></div>
    <script type="module" src="/src/main.js"></script>
  </body>
</html>
```

**Step 4: Create src/main.js**
```js
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import zhCn from 'element-plus/es/locale/lang/zh-cn'

import App from './App.vue'
import router from './router'

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(ElementPlus, { locale: zhCn })

app.mount('#app')
```

**Step 5: Create src/App.vue**
```vue
<template>
  <el-container class="app-container">
    <el-header class="app-header">
      <h1>Quant Trader</h1>
      <div class="nav-links">
        <router-link to="/">仪表盘</router-link>
        <router-link to="/backtest">策略回测</router-link>
        <router-link to="/signals">信号历史</router-link>
        <router-link to="/settings">设置</router-link>
      </div>
    </el-header>
    <el-main class="app-main">
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup>
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

.app-container {
  min-height: 100vh;
}

.app-header {
  background: #1f2937;
  color: white;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
}

.app-header h1 {
  font-size: 20px;
  font-weight: 600;
}

.nav-links a {
  color: #9ca3af;
  text-decoration: none;
  margin-left: 24px;
  transition: color 0.2s;
}

.nav-links a:hover,
.nav-links a.router-link-active {
  color: white;
}

.app-main {
  background: #f3f4f6;
  padding: 24px;
}
</style>
```

**Step 6: Create src/api/index.js**
```js
import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000
})

export const strategiesApi = {
  getPresets: () => api.get('/strategies/presets'),
  getList: () => api.get('/strategies'),
  create: (data) => api.post('/strategies', data),
  toggle: (id) => api.put(`/strategies/${id}/toggle`)
}

export const backtestApi = {
  run: (data) => api.post('/backtest', data),
  getHistory: () => api.get('/backtest/history'),
  get: (id) => api.get(`/backtest/${id}`)
}

export const signalsApi = {
  getList: (skip = 0, limit = 50) => api.get(`/signals?skip=${skip}&limit=${limit}`),
  getToday: () => api.get('/signals/today'),
  scan: () => api.post('/signals/scan')
}

export const notifyApi = {
  test: (data) => api.post('/notify/test', data),
  getSettings: () => api.get('/notify/settings'),
  updateSettings: (data) => api.post('/notify/settings', data)
}

export default api
```

**Step 7: Create src/router/index.js**
```js
import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('@/views/Dashboard.vue')
  },
  {
    path: '/backtest',
    name: 'Backtest',
    component: () => import('@/views/Backtest.vue')
  },
  {
    path: '/signals',
    name: 'Signals',
    component: () => import('@/views/Signals.vue')
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('@/views/Settings.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
```

---

## Task 8: Frontend Views & Components

**Files:**
- Create: `frontend/src/views/Dashboard.vue`
- Create: `frontend/src/views/Backtest.vue`
- Create: `frontend/src/views/Signals.vue`
- Create: `frontend/src/views/Settings.vue`
- Create: `frontend/src/components/BacktestChart.vue`
- Create: `frontend/src/components/SignalList.vue`
- Create: `.env.example`
- Create: `README.md`

**Step 1: Create src/views/Dashboard.vue**
```vue
<template>
  <div class="dashboard">
    <el-card class="header-card">
      <div class="header-content">
        <div>
          <h2>实时信号</h2>
          <p>今日信号概览</p>
        </div>
        <el-button type="primary" @click="refreshSignals">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </el-card>

    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-label">今日买入</div>
          <div class="stat-value buy">{{ buyCount }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-label">今日卖出</div>
          <div class="stat-value sell">{{ sellCount }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-label">总信号</div>
          <div class="stat-value">{{ todaySignals.length }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-label">操作</div>
          <el-button type="primary" @click="triggerScan">手动扫描</el-button>
        </el-card>
      </el-col>
    </el-row>

    <el-card class="signals-card">
      <template #header>
        <div class="card-header">
          <span>今日信号</span>
        </div>
      </template>
      <SignalList :signals="todaySignals" :loading="loading" />
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import { signalsApi } from '@/api'
import SignalList from '@/components/SignalList.vue'

const loading = ref(false)
const todaySignals = ref([])

const buyCount = ref(0)
const sellCount = ref(0)

const refreshSignals = async () => {
  loading.value = true
  try {
    const res = await signalsApi.getToday()
    todaySignals.value = res.data.signals

    buyCount.value = todaySignals.value.filter(s => s.signal_type === 'BUY').length
    sellCount.value = todaySignals.value.filter(s => s.signal_type === 'SELL').length
  } catch (e) {
    ElMessage.error('获取信号失败')
  } finally {
    loading.value = false
  }
}

const triggerScan = async () => {
  try {
    ElMessage.info('开始扫描...')
    const res = await signalsApi.scan()
    ElMessage.success(`扫描完成，发现 ${res.data.signals} 个信号`)
    refreshSignals()
  } catch (e) {
    ElMessage.error('扫描失败')
  }
}

onMounted(() => {
  refreshSignals()
})
</script>

<style scoped>
.dashboard {
  max-width: 1200px;
  margin: 0 auto;
}

.header-card {
  margin-bottom: 20px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-content h2 {
  font-size: 24px;
  margin-bottom: 4px;
}

.header-content p {
  color: #6b7280;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  text-align: center;
}

.stat-label {
  color: #6b7280;
  font-size: 14px;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
}

.stat-value.buy {
  color: #10b981;
}

.stat-value.sell {
  color: #ef4444;
}

.signals-card {
  margin-bottom: 20px;
}

.card-header {
  font-weight: 600;
}
</style>
```

**Step 2: Create src/views/Backtest.vue**
```vue
<template>
  <div class="backtest">
    <el-card class="form-card">
      <template #header>
        <div class="card-header">
          <span>策略回测</span>
        </div>
      </template>

      <el-form :model="form" label-width="120px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="策略">
              <el-select v-model="form.strategy_name" placeholder="选择策略" style="width: 100%">
                <el-option
                  v-for="s in presets"
                  :key="s.name"
                  :label="s.name"
                  :value="s.name"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="股票代码">
              <el-input v-model="form.ts_code" placeholder="如: 000001.SZ" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="开始日期">
              <el-date-picker
                v-model="form.start_date"
                type="date"
                placeholder="开始日期"
                value-format="YYYYMMDD"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="结束日期">
              <el-date-picker
                v-model="form.end_date"
                type="date"
                placeholder="结束日期"
                value-format="YYYYMMDD"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="初始资金">
              <el-input-number v-model="form.initial_capital" :min="10000" :step="10000" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item>
          <el-button type="primary" @click="runBacktest" :loading="running">
            开始回测
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card v-if="result" class="result-card">
      <template #header>
        <div class="card-header">
          <span>回测结果</span>
        </div>
      </template>

      <el-row :gutter="20" class="result-stats">
        <el-col :span="6">
          <div class="stat-item">
            <div class="stat-label">总收益率</div>
            <div class="stat-value" :class="{ positive: result.total_return > 0 }">
              {{ result.total_return.toFixed(2) }}%
            </div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-item">
            <div class="stat-label">最大回撤</div>
            <div class="stat-value negative">{{ result.max_drawdown.toFixed(2) }}%</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-item">
            <div class="stat-label">胜率</div>
            <div class="stat-value">{{ result.win_rate ? result.win_rate.toFixed(2) + '%' : '-' }}</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-item">
            <div class="stat-label">夏普比率</div>
            <div class="stat-value">{{ result.sharpe_ratio ? result.sharpe_ratio.toFixed(2) : '-' }}</div>
          </div>
        </el-col>
      </el-row>

      <BacktestChart :data="result.equity_curve" />
    </el-card>

    <el-card class="history-card">
      <template #header>
        <div class="card-header">
          <span>历史回测</span>
        </div>
      </template>

      <el-table :data="history" stripe>
        <el-table-column prop="strategy_name" label="策略" />
        <el-table-column prop="start_date" label="开始日期" />
        <el-table-column prop="end_date" label="结束日期" />
        <el-table-column prop="total_return" label="收益率">
          <template #default="{ row }">
            <span :class="{ positive: row.total_return > 0, negative: row.total_return < 0 }">
              {{ row.total_return.toFixed(2) }}%
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="max_drawdown" label="最大回撤">
          <template #default="{ row }">
            <span class="negative">{{ row.max_drawdown.toFixed(2) }}%</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间">
          <template #default="{ row }">
            {{ new Date(row.created_at).toLocaleString() }}
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { strategiesApi, backtestApi } from '@/api'
import BacktestChart from '@/components/BacktestChart.vue'

const presets = ref([])
const history = ref([])
const running = ref(false)
const result = ref(null)

const form = ref({
  strategy_name: '',
  ts_code: '',
  start_date: '',
  end_date: '',
  initial_capital: 100000
})

const loadPresets = async () => {
  try {
    const res = await strategiesApi.getPresets()
    presets.value = res.data.strategies
    if (presets.value.length > 0) {
      form.value.strategy_name = presets.value[0].name
    }
  } catch (e) {
    ElMessage.error('加载策略失败')
  }
}

const loadHistory = async () => {
  try {
    const res = await backtestApi.getHistory()
    history.value = res.data.backtests
  } catch (e) {
    ElMessage.error('加载历史失败')
  }
}

const runBacktest = async () => {
  if (!form.value.strategy_name || !form.value.ts_code) {
    ElMessage.warning('请填写策略和股票代码')
    return
  }

  running.value = true
  try {
    const res = await backtestApi.run(form.value)
    result.value = res.data
    ElMessage.success('回测完成')
    loadHistory()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '回测失败')
  } finally {
    running.value = false
  }
}

onMounted(() => {
  loadPresets()
  loadHistory()
})
</script>

<style scoped>
.backtest {
  max-width: 1200px;
  margin: 0 auto;
}

.form-card {
  margin-bottom: 20px;
}

.card-header {
  font-weight: 600;
}

.result-card {
  margin-bottom: 20px;
}

.result-stats {
  margin-bottom: 24px;
}

.stat-item {
  text-align: center;
}

.stat-label {
  color: #6b7280;
  font-size: 14px;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
}

.stat-value.positive {
  color: #10b981;
}

.stat-value.negative {
  color: #ef4444;
}

.history-card {
  margin-bottom: 20px;
}

.positive {
  color: #10b981;
}

.negative {
  color: #ef4444;
}
</style>
```

**Step 3: Create src/views/Signals.vue**
```vue
<template>
  <div class="signals">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>信号历史</span>
        </div>
      </template>
      <SignalList :signals="signals" :loading="loading" />
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { signalsApi } from '@/api'
import SignalList from '@/components/SignalList.vue'

const loading = ref(false)
const signals = ref([])

const loadSignals = async () => {
  loading.value = true
  try {
    const res = await signalsApi.getList(0, 100)
    signals.value = res.data.signals
  } catch (e) {
    ElMessage.error('获取信号失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadSignals()
})
</script>

<style scoped>
.signals {
  max-width: 1200px;
  margin: 0 auto;
}

.card-header {
  font-weight: 600;
}
</style>
```

**Step 4: Create src/views/Settings.vue**
```vue
<template>
  <div class="settings">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>系统设置</span>
        </div>
      </template>

      <el-form :model="form" label-width="160px">
        <el-divider content-position="left">Tushare</el-divider>
        <el-form-item label="Tushare Token">
          <el-input v-model="form.tushare_token" type="password" placeholder="请输入 Tushare Token" />
          <div class="form-tip">获取地址: https://tushare.pro</div>
        </el-form-item>

        <el-divider content-position="left">钉钉通知</el-divider>
        <el-form-item label="Webhook">
          <el-input v-model="form.dingtalk_webhook" placeholder="钉钉机器人 Webhook 地址" />
        </el-form-item>
        <el-form-item label="Secret">
          <el-input v-model="form.dingtalk_secret" type="password" placeholder="加签密钥（可选）" />
        </el-form-item>
        <el-form-item>
          <el-button @click="testNotification">测试通知</el-button>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="saveSettings" :loading="saving">保存设置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { notifyApi } from '@/api'

const saving = ref(false)

const form = ref({
  tushare_token: '',
  dingtalk_webhook: '',
  dingtalk_secret: ''
})

const loadSettings = async () => {
  try {
    const res = await notifyApi.getSettings()
  } catch (e) {
    console.error(e)
  }
}

const saveSettings = async () => {
  saving.value = true
  try {
    await notifyApi.updateSettings(form.value)
    ElMessage.success('设置已保存（请重启后端生效）')
  } catch (e) {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

const testNotification = async () => {
  try {
    await notifyApi.test({
      title: '测试通知',
      text: '这是一条测试消息，来自 Quant Trader'
    })
    ElMessage.success('测试消息已发送')
  } catch (e) {
    ElMessage.error('发送失败，请检查配置')
  }
}

onMounted(() => {
  loadSettings()
})
</script>

<style scoped>
.settings {
  max-width: 800px;
  margin: 0 auto;
}

.card-header {
  font-weight: 600;
}

.form-tip {
  font-size: 12px;
  color: #6b7280;
  margin-top: 4px;
}
</style>
```

**Step 5: Create src/components/BacktestChart.vue**
```vue
<template>
  <div ref="chartRef" style="height: 400px;"></div>
</template>

<script setup>
import { ref, onMounted, watch, onUnmounted } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  data: {
    type: Array,
    default: () => []
  }
})

const chartRef = ref(null)
let chart = null

const initChart = () => {
  if (!chartRef.value) return
  chart = echarts.init(chartRef.value)

  const dates = props.data.map(d => d.date)
  const equity = props.data.map(d => d.equity)

  const initial = props.data[0]?.equity || 100000

  const option = {
    tooltip: {
      trigger: 'axis',
      formatter: (params) => {
        const p = params[0]
        const ret = ((p.value - initial) / initial * 100).toFixed(2)
        return `${p.axisValue}<br/>资金: ${p.value.toFixed(2)}<br/>收益: ${ret}%`
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: dates
    },
    yAxis: {
      type: 'value'
    },
    series: [
      {
        name: '资金曲线',
        type: 'line',
        smooth: true,
        data: equity,
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(16, 185, 129, 0.3)' },
            { offset: 1, color: 'rgba(16, 185, 129, 0.05)' }
          ])
        },
        lineStyle: {
          color: '#10b981'
        },
        itemStyle: {
          color: '#10b981'
        }
      }
    ]
  }

  chart.setOption(option)
}

const handleResize = () => {
  chart?.resize()
}

onMounted(() => {
  if (props.data.length > 0) {
    initChart()
  }
  window.addEventListener('resize', handleResize)
})

watch(() => props.data, () => {
  if (props.data.length > 0) {
    initChart()
  }
}, { deep: true })

onUnmounted(() => {
  chart?.dispose()
  window.removeEventListener('resize', handleResize)
})
</script>
```

**Step 6: Create src/components/SignalList.vue**
```vue
<template>
  <el-table :data="signals" stripe v-loading="loading">
    <el-table-column prop="signal_date" label="日期" width="100" />
    <el-table-column prop="ts_code" label="代码" width="110" />
    <el-table-column prop="name" label="名称" width="120" />
    <el-table-column prop="strategy_name" label="策略" min-width="140" />
    <el-table-column prop="signal_type" label="信号" width="80">
      <template #default="{ row }">
        <el-tag :type="row.signal_type === 'BUY' ? 'success' : 'danger'">
          {{ row.signal_type === 'BUY' ? '买入' : '卖出' }}
        </el-tag>
      </template>
    </el-table-column>
    <el-table-column prop="price" label="价格" width="100">
      <template #default="{ row }">
        {{ row.price.toFixed(2) }}
      </template>
    </el-table-column>
    <el-table-column prop="is_sent" label="已通知" width="80">
      <template #default="{ row }">
        <el-tag v-if="row.is_sent" type="info" size="small">是</el-tag>
        <el-tag v-else type="info" size="small" effect="plain">否</el-tag>
      </template>
    </el-table-column>
    <el-table-column prop="created_at" label="时间">
      <template #default="{ row }">
        {{ new Date(row.created_at).toLocaleString() }}
      </template>
    </el-table-column>
  </el-table>
</template>

<script setup>
defineProps({
  signals: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  }
})
</script>
```

**Step 7: Create .env.example**
```env
# Tushare Token (获取地址: https://tushare.pro)
TUSHARE_TOKEN=your_tushare_token_here

# 钉钉机器人配置
DINGTALK_WEBHOOK=https://oapi.dingtalk.com/robot/send?access_token=xxx
DINGTALK_SECRET=SECxxx

# 邮件配置 (第二阶段)
EMAIL_SMTP_HOST=smtp.qq.com
EMAIL_SMTP_PORT=587
EMAIL_USER=your_email@qq.com
EMAIL_PASSWORD=your_password

# 数据库
DATABASE_URL=sqlite:///./quant_trader.db
```

**Step 8: Create README.md**
```markdown
# Quant Trader

量化交易策略工具 - 按策略选择股票，侧重实时交易信号和策略回测。

## 功能特性

- 预设策略（均线双金叉、RSI超跌反弹、动量突破、多因子选股、量价齐升）
- 策略回测（收益率、最大回撤、胜率、夏普比率）
- 实时信号扫描
- 钉钉通知
- Web 界面

## 技术栈

**后端:**
- FastAPI
- SQLAlchemy + SQLite
- Tushare
- APScheduler

**前端:**
- Vue 3 + Vite
- Element Plus
- ECharts
- Pinia + Vue Router

## 快速开始

### 1. 后端启动

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 复制并配置 .env
cp .env.example .env
# 编辑 .env，填入 Tushare Token 和钉钉 Webhook

# 启动
uvicorn main:app --reload --port 8000
```

### 2. 前端启动

```bash
cd frontend
npm install
npm run dev
```

### 3. 访问

打开浏览器访问 http://localhost:5173

## 项目结构

```
quant-trader/
├── backend/
│   ├── main.py              # FastAPI 入口
│   ├── config.py            # 配置
│   ├── database.py          # 数据库
│   ├── models.py            # 数据模型
│   ├── api/                 # API 路由
│   ├── core/                # 核心模块
│   └── strategies/          # 策略实现
├── frontend/
│   ├── src/
│   │   ├── views/           # 页面
│   │   ├── components/      # 组件
│   │   ├── api/             # API 调用
│   │   └── router/          # 路由
│   └── package.json
└── docs/
    └── plans/               # 设计文档
```

## 注意事项

- 仅供学习研究，不构成投资建议
- Tushare API 有调用频率限制
- 实盘交易请谨慎
```

---

## 执行总结

**Plan complete and saved to `docs/plans/2026-03-05-quant-trader-implementation.md`.**

**Two execution options:**

1. **Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

2. **Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

**Which approach?**
