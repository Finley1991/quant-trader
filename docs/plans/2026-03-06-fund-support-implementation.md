# 场内基金支持 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 为 quant-trader 项目增加场内基金（ETF、LOF、封闭式基金）的支持，包括自选、策略、回测等功能。

**Architecture:** 采用统一资产类型扩展方案，通过 asset_type 字段区分股票/基金，最大化代码复用。

**Tech Stack:** FastAPI + SQLAlchemy + Vue 3 + Element Plus + Tushare

---

## 前置检查

在开始之前，请先确认：
1. 项目可以正常启动
2. 后端数据库存在（quant_trader.db）
3. Tushare token 配置正确

---

## 阶段一：数据库模型扩展

### Task 1: 扩展 models.py - Watchlist 表

**Files:**
- Modify: `backend/models.py`

**Step 1: 读取现有 models.py**

```python
# 已读取，见 models.py
```

**Step 2: 修改 Watchlist 模型，添加 asset_type 字段**

在 `Watchlist` 类中添加：
```python
asset_type = Column(String, default='stock')  # stock/etf/lof/fund
```

完整修改位置：`backend/models.py:67-74`

**Step 3: 修改 Signal 模型，添加 asset_type 字段**

在 `Signal` 类中添加：
```python
asset_type = Column(String, default='stock')  # stock/etf/lof/fund
```

完整修改位置：`backend/models.py:44-57`

**Step 4: 修改 Backtest 模型，添加 asset_type 字段**

在 `Backtest` 类中添加：
```python
asset_type = Column(String, default='stock')  # stock/etf/lof/fund
```

完整修改位置：`backend/models.py:27-42`

**Step 5: 验证修改**

确保 SQLAlchemy 模型语法正确。

---

### Task 2: 扩展 data_fetcher.py - 基金数据获取

**Files:**
- Modify: `backend/core/data_fetcher.py`

**Step 1: 在 DataFetcher 类中添加 get_fund_list 方法**

```python
def get_fund_list(self, fund_type: str = None) -> pd.DataFrame:
    """获取基金列表
    Args:
        fund_type: 基金类型 (etf/lof/closed_end, None表示全部)
    """
    try:
        fields = 'ts_code,name,fund_type,list_date,market'
        df = self.pro.fund_basic(market='E', status='L', fields=fields)
        if fund_type and not df.empty:
            df = df[df['fund_type'].str.upper() == fund_type.upper()]
        return df
    except Exception:
        return pd.DataFrame()
```

**Step 2: 添加 get_fund_daily 方法**

```python
def get_fund_daily(self, ts_code: str, start_date: str = None, end_date: str = None) -> pd.DataFrame:
    """获取基金日线数据"""
    if end_date is None:
        end_date = datetime.now().strftime('%Y%m%d')
    if start_date is None:
        start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')

    try:
        df = self.pro.fund_daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
        if not df.empty:
            df = df.sort_values('trade_date').reset_index(drop=True)
        return df
    except Exception:
        return pd.DataFrame()
```

**Step 3: 添加 get_fund_search 方法**

```python
def get_fund_search(self, keyword: str) -> pd.DataFrame:
    """搜索基金"""
    df = self.get_fund_list()
    if df.empty:
        return df
    keyword = keyword.upper()
    mask = (df['ts_code'].str.contains(keyword, na=False) |
            df['name'].str.contains(keyword, na=False))
    return df[mask].head(50)
```

**Step 4: 添加 get_daily_data_unified 统一方法**

```python
def get_daily_data_unified(self, ts_code: str, asset_type: str = 'stock',
                           start_date: str = None, end_date: str = None) -> pd.DataFrame:
    """统一获取日线数据（根据资产类型路由）"""
    if asset_type == 'stock':
        return self.get_daily_data(ts_code, start_date, end_date)
    else:
        return self.get_fund_daily(ts_code, start_date, end_date)
```

**Step 5: 添加 get_kline_data_unified 统一方法**

```python
def get_kline_data_unified(self, ts_code: str, asset_type: str = 'stock',
                           freq: str = 'auto') -> Dict[str, Any]:
    """统一获取K线数据"""
    # 基金暂时只支持日线
    if asset_type != 'stock':
        df = self.get_fund_daily(ts_code)
        return {'freq': 'daily', 'data': df}
    return self.get_kline_data(ts_code, freq)
```

---

### Task 3: 创建 funds.py API

**Files:**
- Create: `backend/api/funds.py`

**Step 1: 创建 funds.py 文件**

```python
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any

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
        "x_data": df['trade_date'].tolist() if 'trade_date' in df.columns else [],
        "open": df['open'].tolist() if 'open' in df.columns else [],
        "high": df['high'].tolist() if 'high' in df.columns else [],
        "low": df['low'].tolist() if 'low' in df.columns else [],
        "close": df['close'].tolist() if 'close' in df.columns else [],
        "volume": df['vol'].tolist() if 'vol' in df.columns else []
    }
```

---

### Task 4: 注册 funds 路由到 main.py

**Files:**
- Modify: `backend/main.py`

**Step 1: 在 import 语句中添加 funds**

```python
from api import strategies, backtest, signals, notify, watchlist, stocks, funds
```

**Step 2: 在路由注册部分添加**

```python
app.include_router(funds.router, prefix="/api/funds", tags=["funds"])
```

---

### Task 5: 扩展 watchlist.py API

**Files:**
- Modify: `backend/api/watchlist.py`

**Step 1: 修改 WatchlistAdd 模型，添加 asset_type**

```python
class WatchlistAdd(BaseModel):
    ts_code: str
    name: str
    asset_type: str = 'stock'  # 新增
```

**Step 2: 修改 add_to_watchlist 函数，使用 asset_type**

```python
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
```

**Step 3: 修改 get_watchlist 函数，支持按 asset_type 筛选**

```python
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
```

---

### Task 6: 前端 API 层扩展

**Files:**
- Modify: `frontend/src/api/index.js`

**Step 1: 读取现有 API 文件**

先读取看一下现有结构。

**Step 2: 添加 fundsApi**

```javascript
// 基金 API
export const fundsApi = {
  search: (keyword) => axios.get('/api/funds/search', { params: { keyword } }),
  list: (fundType, limit) => axios.get('/api/funds/list', { params: { fund_type: fundType, limit } }),
  getKline: (tsCode) => axios.get(`/api/funds/${tsCode}/kline`),
}
```

**Step 3: 扩展 watchlistApi**

确保 watchlistApi 的 add 方法支持传入 asset_type。

---

### Task 7: 数据库迁移 - 创建新表结构

**Files:**
- Create: `backend/migrate_db.py` (临时迁移脚本)

**Step 1: 创建迁移脚本**

```python
"""
数据库迁移脚本：为现有表添加 asset_type 字段
由于 SQLite 不直接支持 ALTER TABLE ADD COLUMN IF NOT EXISTS，
我们需要手动处理。
"""
import os
import sqlite3
from pathlib import Path

db_path = Path(__file__).parent / "quant_trader.db"

if not db_path.exists():
    print("Database not found, nothing to migrate")
    exit(0)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 检查 watchlist 表是否已有 asset_type 列
cursor.execute("PRAGMA table_info(watchlist)")
columns = [col[1] for col in cursor.fetchall()]

if 'asset_type' not in columns:
    print("Adding asset_type to watchlist...")
    cursor.execute("ALTER TABLE watchlist ADD COLUMN asset_type TEXT DEFAULT 'stock'")
    print("Done")
else:
    print("watchlist.asset_type already exists")

# 检查 signals 表
cursor.execute("PRAGMA table_info(signals)")
columns = [col[1] for col in cursor.fetchall()]

if 'asset_type' not in columns:
    print("Adding asset_type to signals...")
    cursor.execute("ALTER TABLE signals ADD COLUMN asset_type TEXT DEFAULT 'stock'")
    print("Done")
else:
    print("signals.asset_type already exists")

# 检查 backtests 表
cursor.execute("PRAGMA table_info(backtests)")
columns = [col[1] for col in cursor.fetchall()]

if 'asset_type' not in columns:
    print("Adding asset_type to backtests...")
    cursor.execute("ALTER TABLE backtests ADD COLUMN asset_type TEXT DEFAULT 'stock'")
    print("Done")
else:
    print("backtests.asset_type already exists")

conn.commit()
conn.close()
print("Migration complete!")
```

**Step 2: 运行迁移脚本**

```bash
cd backend
python migrate_db.py
```

---

### Task 8: 前端 Watchlist 页面扩展

**Files:**
- Modify: `frontend/src/views/Watchlist.vue`

**Step 1: 添加资产类型筛选标签**

在模板中添加：
```vue
<el-card class="header-card">
  <div class="header-content">
    <div>
      <h2>我的自选</h2>
      <p>管理和查看自选股/基金行情</p>
    </div>
    <div class="asset-tabs">
      <el-radio-group v-model="currentAssetType" size="small">
        <el-radio-button value="">全部</el-radio-button>
        <el-radio-button value="stock">股票</el-radio-button>
        <el-radio-button value="etf">ETF</el-radio-button>
        <el-radio-button value="lof">LOF</el-radio-button>
        <el-radio-button value="fund">基金</el-radio-button>
      </el-radio-group>
    </div>
    <div class="header-actions">
      <el-radio-group v-model="searchMode" size="small" style="margin-right: 8px">
        <el-radio-button value="stock">搜股票</el-radio-button>
        <el-radio-button value="fund">搜基金</el-radio-button>
      </el-radio-group>
      <!-- ... 其余现有代码 ... -->
    </div>
  </div>
</el-card>
```

**Step 2: 添加相关状态变量**

```javascript
const currentAssetType = ref('')
const searchMode = ref('stock') // 'stock' 或 'fund'
```

**Step 3: 修改 loadWatchlist 支持筛选**

```javascript
const loadWatchlist = async () => {
  try {
    const res = await watchlistApi.getList(currentAssetType.value || undefined)
    watchlist.value = res.data.watchlist
  } catch (e) {
    console.error('Failed to load watchlist:', e)
  }
}
```

**Step 4: 修改 handleSearchAdd 支持搜索基金**

```javascript
const handleSearchAdd = async () => {
  if (!searchAddKeyword.value) {
    ElMessage.warning('请输入代码或名称')
    return
  }
  searching.value = true
  try {
    let res
    if (searchMode.value === 'stock') {
      res = await stocksApi.search(searchAddKeyword.value)
    } else {
      res = await fundsApi.search(searchAddKeyword.value)
    }
    const items = res.data.stocks || res.data.funds || []
    if (items.length === 0) {
      ElMessage.warning('未找到匹配的标的')
      return
    }
    const item = items[0]
    const assetType = searchMode.value === 'stock' ? 'stock' : 'fund'
    await watchlistApi.add({ ts_code: item.ts_code, name: item.name, asset_type: assetType })
    ElMessage.success(`已添加 ${item.name}`)
    searchAddKeyword.value = ''
    await loadWatchlist()
    await refreshQuotes()
  } catch (e) {
    if (e.response?.status === 400) {
      ElMessage.warning('该标的已在自选列表中')
    } else {
      ElMessage.error('添加失败')
    }
  } finally {
    searching.value = false
  }
}
```

**Step 5: 监听 currentAssetType 变化重新加载**

```javascript
import { ref, onMounted, watch } from 'vue'

watch(currentAssetType, () => {
  loadWatchlist()
  refreshQuotes()
})
```

**Step 6: 添加样式**

```css
.asset-tabs {
  margin-right: 16px;
}
```

---

### Task 9: 测试验证

**Step 1: 启动后端服务**

```bash
cd backend
python -m uvicorn main:app --reload
```

**Step 2: 启动前端服务**

```bash
cd frontend
npm run dev
```

**Step 3: 测试基金搜索**

访问 `/api/funds/search?keyword=510300`

**Step 4: 测试添加基金到自选**

**Step 5: 测试资产类型筛选**

---

### Task 10: 清理与文档

**Step 1: 删除临时迁移脚本（可选）**

**Step 2: 更新 README（如需要）**

---

## 总结

以上是完整的实施计划，按照顺序执行即可完成场内基金支持功能。
