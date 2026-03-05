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
