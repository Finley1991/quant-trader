# Watchlist Feature Design

**Date:** 2026-03-05
**Feature:** 自选股功能

## Overview

添加自选股功能，允许用户添加、管理自选股，并查看自选股的实时行情。

## Requirements

### User Requirements
- 添加自选股（两种方式：搜索添加 + 从列表选择）
- 查看自选股列表（卡片式布局）
- 手动刷新行情
- 点击股票卡片展开查看K线图
- 删除自选股

### Display Requirements (Detailed Version)
每个股票卡片显示：
- 股票名称 + 代码
- 最新价 + 涨跌幅（红涨绿跌）
- 今日最高/最低
- 成交量、成交额
- PE、PB、换手率

## Data Model

### New Model: Watchlist

```python
class Watchlist(Base):
    __tablename__ = "watchlist"

    id = Column(Integer, primary_key=True, index=True)
    ts_code = Column(String, unique=True, index=True)
    name = Column(String)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

## Backend API

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/watchlist` | 获取自选股列表 |
| POST | `/api/watchlist` | 添加自选股 |
| DELETE | `/api/watchlist/{ts_code}` | 删除自选股 |
| GET | `/api/watchlist/quotes` | 获取自选股实时行情 |
| GET | `/api/stocks/search` | 搜索股票 |
| GET | `/api/stocks/{ts_code}/kline` | 获取K线数据 |

### K-line Data Strategy

Fallback strategy for k-line data:
1. **Priority 1:** 1min data (if available)
2. **Priority 2:** 5min data (if available)
3. **Fallback:** Daily data

## Frontend

### New Route

Add `/watchlist` to router:

```javascript
{
  path: '/watchlist',
  name: 'Watchlist',
  component: () => import('@/views/Watchlist.vue')
}
```

### Navigation Update

Add "自选股" to nav links in App.vue.

### Components

#### Watchlist.vue
- Search input for adding stocks
- "Add from list" button (opens modal)
- Refresh button
- Stock card list
- Expandable k-line chart per stock

#### StockSelectorModal.vue
- Search/filter stocks
- Multi-select checkboxes
- Add selected to watchlist

#### StockCard.vue
- Displays detailed stock info
- Click to expand k-line
- Delete button

#### KlineChart.vue
- ECharts component for k-line display
- Supports multiple data frequencies

## Data Flow

```
User opens Watchlist page
  → GET /api/watchlist (get ts_code list)
  → GET /api/watchlist/quotes (get real-time quotes)
  → Display stock cards

User searches stock
  → GET /api/stocks/search?keyword=xxx
  → Display results

User adds stock
  → POST /api/watchlist
  → Refresh quotes

User clicks card
  → GET /api/stocks/{ts_code}/kline
  → Expand and display chart
```

## Tushare Integration

### New DataFetcher Methods

```python
def get_realtime_quotes(self, ts_codes: List[str]) -> pd.DataFrame
def get_stock_search(self, keyword: str) -> pd.DataFrame
def get_kline_data(self, ts_code: str, freq: str = 'auto') -> pd.DataFrame
```

### Data Sources

- **Real-time quotes:** `ts.realtime_quote()`
- **1min/5min data:** `ts.pro_bar(freq='1min'/'5min')`
- **Daily data:** `pro.daily()` (existing)
- **Daily basics:** `pro.daily_basic()` (for PE, PB, turnover)

## File Changes

### Backend
- `models.py` - Add Watchlist model
- `core/data_fetcher.py` - Add new methods
- `api/watchlist.py` - New API routes
- `api/stocks.py` - New API routes
- `main.py` - Include new routers

### Frontend
- `src/router/index.js` - Add watchlist route
- `src/App.vue` - Add nav link
- `src/views/Watchlist.vue` - New page
- `src/components/StockCard.vue` - New component
- `src/components/KlineChart.vue` - New component
- `src/components/StockSelectorModal.vue` - New component
- `src/api/index.js` - Add watchlist and stocks API methods

## Success Criteria

- User can search and add stocks to watchlist
- User can select multiple stocks from list to add
- Stock cards display all required detailed info
- Clicking card expands to show k-line chart
- Manual refresh works
- User can delete stocks from watchlist
- K-line falls back gracefully through data frequencies
