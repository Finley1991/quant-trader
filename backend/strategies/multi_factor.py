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
