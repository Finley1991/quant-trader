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
