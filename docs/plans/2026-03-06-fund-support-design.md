# 场内基金支持 - 设计文档

**日期**: 2026-03-06
**版本**: v1.0
**基于版本**: quant-trader v1.0

## 1. 功能概述

为 quant-trader 项目增加场内基金（ETF、LOF、封闭式基金）的支持，包括自选、策略、回测等功能。

### 目标
- 支持 ETF、LOF、封闭式基金等场内基金品类
- 统一的资产类型管理（股票/基金）
- 基金数据获取与展示
- 基金策略回测与信号扫描
- 兼容现有股票功能，无需重复代码

### 支持的基金类型
- **ETF**: 交易型开放式指数基金
- **LOF**: 上市型开放式基金
- **封闭式基金**: 封闭式基金

---

## 2. 设计方案

### 核心思路：统一资产类型扩展

将现有的"股票"概念抽象为"资产"，通过 `asset_type` 字段区分不同类型：
- `stock`: 股票
- `etf`: ETF基金
- `lof`: LOF基金
- `fund`: 封闭式基金/其他基金

**优点**:
- 代码复用最大化
- 用户体验统一
- 便于未来扩展其他资产类型

**缺点**:
- 需要修改现有数据表结构
- 需要数据迁移

---

## 3. 数据模型设计

### 3.1 数据库模型变更

#### Watchlist 表扩展
```python
class Watchlist(Base):
    __tablename__ = "watchlist"

    id = Column(Integer, primary_key=True, index=True)
    ts_code = Column(String, unique=True, index=True)
    name = Column(String)
    asset_type = Column(String, default='stock')  # 新增: stock/etf/lof/fund
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

#### Signal 表扩展
```python
class Signal(Base):
    __tablename__ = "signals"

    id = Column(Integer, primary_key=True, index=True)
    ts_code = Column(String, index=True)
    name = Column(String, nullable=True)
    asset_type = Column(String, default='stock')  # 新增
    strategy_id = Column(Integer, index=True)
    strategy_name = Column(String)
    signal_type = Column(String)
    price = Column(Float)
    signal_date = Column(String)
    signal_time = Column(String, nullable=True)
    is_sent = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

#### Backtest 表扩展
```python
class Backtest(Base):
    __tablename__ = "backtests"

    id = Column(Integer, primary_key=True, index=True)
    strategy_id = Column(Integer, index=True)
    strategy_name = Column(String)
    asset_type = Column(String, default='stock')  # 新增
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
```

#### 新增 Fund 表（可选）
```python
class Fund(Base):
    __tablename__ = "funds"

    id = Column(Integer, primary_key=True, index=True)
    ts_code = Column(String, unique=True, index=True)
    name = Column(String)
    fund_type = Column(String)  # etf/lof/closed_end
    market = Column(String)      # SSE/SZSE
    list_date = Column(String)
    delist_date = Column(String, nullable=True)
    management_fee = Column(Float, nullable=True)
    custodian_fee = Column(Float, nullable=True)
    benchmark = Column(String, nullable=True)      # 跟踪指数
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

### 3.2 数据迁移
- 现有 Watchlist 数据默认 `asset_type = 'stock'`
- 现有 Signal 数据默认 `asset_type = 'stock'`
- 现有 Backtest 数据默认 `asset_type = 'stock'`

---

## 4. 后端数据获取层设计

### 4.1 DataFetcher 类扩展

#### 新增方法
```python
class DataFetcher:
    # ... 现有方法 ...

    def get_fund_list(self, fund_type: str = None) -> pd.DataFrame:
        """获取基金列表
        Args:
            fund_type: 基金类型 (etf/lof/closed_end, None表示全部)
        """
        fields = 'ts_code,name,fund_type,list_date,market'
        df = self.pro.fund_basic(market='E', status='L', fields=fields)
        if fund_type and not df.empty:
            df = df[df['fund_type'].str.upper() == fund_type.upper()]
        return df

    def get_fund_daily(self, ts_code: str, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """获取基金日线数据"""
        if end_date is None:
            end_date = datetime.now().strftime('%Y%m%d')
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')

        df = self.pro.fund_daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
        if not df.empty:
            df = df.sort_values('trade_date').reset_index(drop=True)
        return df

    def get_etf_nav(self, ts_code: str, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """获取ETF净值数据（溢价率计算用）"""
        df = self.pro.fund_etf_nav(ts_code=ts_code, start_date=start_date, end_date=end_date)
        if not df.empty:
            df = df.sort_values('trade_date').reset_index(drop=True)
        return df

    def get_fund_realtime_quotes(self, ts_codes: List[str]) -> pd.DataFrame:
        """获取基金实时行情"""
        if not ts_codes:
            return pd.DataFrame()
        ts_code_str = ','.join(ts_codes)
        try:
            df = ts.realtime_quote(ts_code=ts_code_str)
            return df
        except Exception:
            return pd.DataFrame()

    def get_fund_search(self, keyword: str) -> pd.DataFrame:
        """搜索基金"""
        df = self.get_fund_list()
        if df.empty:
            return df
        keyword = keyword.upper()
        mask = (df['ts_code'].str.contains(keyword, na=False) |
                df['name'].str.contains(keyword, na=False))
        return df[mask].head(50)

    # 统一数据获取方法
    def get_daily_data_unified(self, ts_code: str, asset_type: str = 'stock',
                               start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """统一获取日线数据（根据资产类型路由）"""
        if asset_type == 'stock':
            return self.get_daily_data(ts_code, start_date, end_date)
        else:
            return self.get_fund_daily(ts_code, start_date, end_date)

    def get_kline_data_unified(self, ts_code: str, asset_type: str = 'stock',
                               freq: str = 'auto') -> Dict[str, Any]:
        """统一获取K线数据"""
        # 基金暂时只支持日线，未来可扩展
        if asset_type != 'stock':
            df = self.get_fund_daily(ts_code)
            return {'freq': 'daily', 'data': df}
        return self.get_kline_data(ts_code, freq)
```

---

## 5. API 层设计

### 5.1 新增 /api/funds 路由

```python
# backend/api/funds.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional

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
        "x_data": df['trade_date'].tolist(),
        "open": df['open'].tolist() if 'open' in df.columns else [],
        "high": df['high'].tolist() if 'high' in df.columns else [],
        "low": df['low'].tolist() if 'low' in df.columns else [],
        "close": df['close'].tolist() if 'close' in df.columns else [],
        "volume": df['vol'].tolist() if 'vol' in df.columns else []
    }
```

### 5.2 现有 API 扩展

#### Watchlist API 扩展
- `POST /api/watchlist/` - 支持传入 `asset_type` 参数
- `GET /api/watchlist/` - 支持按 `asset_type` 筛选
- `GET /api/watchlist/quotes` - 统一获取股票/基金行情

#### Signals API 扩展
- `GET /api/signals/` - 支持按 `asset_type` 筛选

#### Backtest API 扩展
- `POST /api/backtest/run` - 支持传入 `asset_type` 参数

### 5.3 主应用路由注册
```python
# backend/main.py
from api import strategies, backtest, signals, notify, watchlist, stocks, funds

app.include_router(funds.router, prefix="/api/funds", tags=["funds"])
```

---

## 6. 前端设计

### 6.1 组件复用与扩展

#### 统一自选列表页面 (Watchlist.vue)
- 增加资产类型筛选标签（全部/股票/ETF/LOF/基金）
- 支持切换搜索类型（股票/基金）
- StockCard 组件更名为 AssetCard

#### 策略与回测页面扩展
- 策略回测页面增加资产类型选择
- 信号页面支持按资产类型筛选

#### 新增组件
- `FundSelectorModal.vue` - 基金选择器
- `FundCard.vue` - 基金卡片（如需要特殊展示）

### 6.2 API 层扩展
```javascript
// frontend/src/api/index.js
// 新增基金 API
export const fundsApi = {
  search: (keyword) => axios.get('/api/funds/search', { params: { keyword } }),
  list: (fundType, limit) => axios.get('/api/funds/list', { params: { fund_type: fundType, limit } }),
  getKline: (tsCode) => axios.get(`/api/funds/${tsCode}/kline`),
}

// 扩展 watchlistApi
export const watchlistApi = {
  getList: (assetType) => axios.get('/api/watchlist', { params: { asset_type: assetType } }),
  add: (data) => axios.post('/api/watchlist', data), // data 包含 asset_type
  remove: (tsCode) => axios.delete(`/api/watchlist/${tsCode}`),
  getQuotes: () => axios.get('/api/watchlist/quotes'),
}
```

### 6.3 基金特有信息展示
- 基金类型标签（ETF/LOF/封闭式）
- 跟踪指数（如适用）
- 溢价率/折价率（ETF特有）
- 净值信息

---

## 7. 策略引擎兼容

- 现有策略（均线双金叉、RSI等）默认兼容基金数据
- 可新增基金特有策略（如ETF折溢价套利策略）
- 回测引擎无需改动，兼容基金数据

---

## 8. 实施步骤

### 阶段一：数据模型 & 后端基础
1. 扩展数据库模型（添加 asset_type 字段）
2. 创建数据迁移脚本
3. 扩展 DataFetcher 类（基金数据获取）
4. 新增 Funds API

### 阶段二：API 扩展 & 兼容
1. 扩展现有 API（Watchlist/Signals/Backtest）
2. 测试 API 兼容性

### 阶段三：前端改造
1. 扩展自选列表页面（资产类型筛选）
2. 重命名/扩展组件（StockCard -> AssetCard）
3. 新增基金选择器组件
4. 扩展策略回测页面

### 阶段四：测试 & 优化
1. 端到端测试
2. 性能优化
3. 用户体验优化

---

## 9. 注意事项

1. **数据兼容性**: 现有数据默认 asset_type = 'stock'，确保迁移不丢失数据
2. **API 兼容性**: 现有 API 在不传 asset_type 时默认行为不变
3. **Tushare 积分**: fund_basic、fund_daily 等接口可能需要更高积分权限
4. **基金代码格式**: 注意基金代码与股票代码的区别（如 510300.SH）
