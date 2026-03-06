# Watchlist Feature Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build watchlist feature with card-based layout, search, bulk add, detailed stock info, and expandable k-line charts.

**Architecture:** Add Watchlist data model, new API endpoints for watchlist and stocks, enhanced data fetcher with k-line fallbacks, and new Vue components for card display and stock selection.

**Tech Stack:** FastAPI, SQLAlchemy, Vue 3, Element Plus, ECharts, Tushare

---

## Task 1: Add Watchlist Model

**Files:**
- Modify: `backend/models.py`

**Step 1: Add Watchlist model to models.py**

Add at end of `backend/models.py`:

```python
class Watchlist(Base):
    __tablename__ = "watchlist"

    id = Column(Integer, primary_key=True, index=True)
    ts_code = Column(String, unique=True, index=True)
    name = Column(String)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

**Step 2: Commit**

```bash
git add backend/models.py
git commit -m "feat: add Watchlist data model"
```

---

## Task 2: Enhance DataFetcher with Watchlist Methods

**Files:**
- Modify: `backend/core/data_fetcher.py`

**Step 1: Add new methods to DataFetcher class**

Add to `backend/core/data_fetcher.py`, before the `_data_fetcher` singleton:

```python
    def get_realtime_quotes(self, ts_codes: List[str]) -> pd.DataFrame:
        """Get real-time quotes for multiple stocks"""
        if not ts_codes:
            return pd.DataFrame()
        ts_code_str = ','.join(ts_codes)
        try:
            df = ts.realtime_quote(ts_code=ts_code_str)
            return df
        except Exception:
            return pd.DataFrame()

    def get_stock_search(self, keyword: str) -> pd.DataFrame:
        """Search stocks by name or code"""
        df = self.get_stock_list()
        if df.empty:
            return df
        keyword = keyword.upper()
        mask = (df['ts_code'].str.contains(keyword, na=False) |
                df['name'].str.contains(keyword, na=False))
        return df[mask].head(50)

    def get_kline_data(self, ts_code: str, freq: str = 'auto') -> Dict[str, Any]:
        """Get k-line data with fallback strategy: 1min -> 5min -> daily"""
        result = {'freq': 'daily', 'data': pd.DataFrame()}

        # Try 1min first
        if freq in ['auto', '1min']:
            try:
                end_date = datetime.now().strftime('%Y%m%d')
                start_date = (datetime.now() - timedelta(days=7)).strftime('%Y%m%d')
                df = ts.pro_bar(ts_code=ts_code, asset='E', freq='1min',
                                start_date=start_date, end_date=end_date)
                if df is not None and not df.empty:
                    result['freq'] = '1min'
                    result['data'] = df.sort_values('trade_time').reset_index(drop=True)
                    return result
            except Exception:
                pass

        # Try 5min
        if freq in ['auto', '5min']:
            try:
                end_date = datetime.now().strftime('%Y%m%d')
                start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
                df = ts.pro_bar(ts_code=ts_code, asset='E', freq='5min',
                                start_date=start_date, end_date=end_date)
                if df is not None and not df.empty:
                    result['freq'] = '5min'
                    result['data'] = df.sort_values('trade_time').reset_index(drop=True)
                    return result
            except Exception:
                pass

        # Fallback to daily
        df = self.get_daily_data(ts_code)
        if not df.empty:
            result['freq'] = 'daily'
            result['data'] = df
        return result

    def get_daily_basic_single(self, ts_code: str, trade_date: str = None) -> Optional[Dict[str, Any]]:
        """Get daily basic data (PE, PB, turnover) for a single stock"""
        if trade_date is None:
            trade_date = datetime.now().strftime('%Y%m%d')
        try:
            df = self.pro.daily_basic(ts_code=ts_code, trade_date=trade_date)
            if not df.empty:
                return df.iloc[0].to_dict()
        except Exception:
            pass
        return None
```

**Step 2: Commit**

```bash
git add backend/core/data_fetcher.py
git commit -m "feat: add watchlist-related methods to DataFetcher"
```

---

## Task 3: Create Watchlist API Endpoints

**Files:**
- Create: `backend/api/watchlist.py`

**Step 1: Create watchlist.py**

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from pydantic import BaseModel

from database import get_db
from models import Watchlist
from core.data_fetcher import get_data_fetcher

router = APIRouter()

class WatchlistAdd(BaseModel):
    ts_code: str
    name: str

@router.get("/")
def get_watchlist(db: Session = Depends(get_db)):
    items = db.query(Watchlist).order_by(Watchlist.sort_order, Watchlist.created_at).all()
    return {"watchlist": [
        {
            "id": w.id,
            "ts_code": w.ts_code,
            "name": w.name,
            "sort_order": w.sort_order,
            "created_at": w.created_at
        }
        for w in items
    ]}

@router.post("/")
def add_to_watchlist(data: WatchlistAdd, db: Session = Depends(get_db)):
    existing = db.query(Watchlist).filter(Watchlist.ts_code == data.ts_code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Stock already in watchlist")
    item = Watchlist(ts_code=data.ts_code, name=data.name)
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"id": item.id, "ts_code": item.ts_code, "name": item.name}

@router.delete("/{ts_code}")
def remove_from_watchlist(ts_code: str, db: Session = Depends(get_db)):
    item = db.query(Watchlist).filter(Watchlist.ts_code == ts_code).first()
    if not item:
        raise HTTPException(status_code=404, detail="Stock not in watchlist")
    db.delete(item)
    db.commit()
    return {"success": True}

@router.get("/quotes")
def get_watchlist_quotes(db: Session = Depends(get_db)):
    items = db.query(Watchlist).all()
    if not items:
        return {"quotes": []}

    ts_codes = [w.ts_code for w in items]
    fetcher = get_data_fetcher()

    # Get real-time quotes
    quotes_df = fetcher.get_realtime_quotes(ts_codes)
    quotes_dict = {}
    if not quotes_df.empty:
        for _, row in quotes_df.iterrows():
            quotes_dict[row['TS_CODE']] = row.to_dict()

    # Get daily data for basics
    result = []
    for item in items:
        quote = quotes_dict.get(item.ts_code, {})
        daily_df = fetcher.get_daily_data(item.ts_code)
        daily_basic = fetcher.get_daily_basic_single(item.ts_code)

        quote_data = {
            "ts_code": item.ts_code,
            "name": item.name,
            "price": float(quote.get('PRICE', 0)) if quote.get('PRICE') else None,
            "change_pct": None,
            "high": None,
            "low": None,
            "open": None,
            "close": None,
            "volume": None,
            "amount": None,
            "pe": None,
            "pb": None,
            "turnover": None
        }

        if not daily_df.empty:
            latest = daily_df.iloc[-1]
            prev = daily_df.iloc[-2] if len(daily_df) >= 2 else None
            quote_data.update({
                "close": float(latest['close']),
                "high": float(latest['high']),
                "low": float(latest['low']),
                "open": float(latest['open']),
                "volume": float(latest['vol']) if 'vol' in latest else None,
                "amount": float(latest['amount']) if 'amount' in latest else None
            })
            if prev is not None:
                quote_data["change_pct"] = (latest['close'] - prev['close']) / prev['close'] * 100

        if daily_basic:
            quote_data.update({
                "pe": daily_basic.get('pe'),
                "pb": daily_basic.get('pb'),
                "turnover": daily_basic.get('turnover_rate')
            })

        if quote_data['price'] is None:
            quote_data['price'] = quote_data['close']

        result.append(quote_data)

    return {"quotes": result}
```

**Step 2: Commit**

```bash
git add backend/api/watchlist.py
git commit -m "feat: add watchlist API endpoints"
```

---

## Task 4: Create Stocks API Endpoints

**Files:**
- Create: `backend/api/stocks.py`

**Step 1: Create stocks.py**

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional

from core.data_fetcher import get_data_fetcher

router = APIRouter()

@router.get("/search")
def search_stocks(keyword: str):
    if not keyword or len(keyword) < 1:
        return {"stocks": []}
    fetcher = get_data_fetcher()
    df = fetcher.get_stock_search(keyword)
    return {"stocks": df.to_dict('records') if not df.empty else []}

@router.get("/list")
def list_stocks(limit: int = 100):
    fetcher = get_data_fetcher()
    df = fetcher.get_stock_list()
    if not df.empty:
        df = df.head(limit)
    return {"stocks": df.to_dict('records') if not df.empty else []}

@router.get("/{ts_code}/kline")
def get_kline(ts_code: str, freq: str = "auto"):
    fetcher = get_data_fetcher()
    result = fetcher.get_kline_data(ts_code, freq)
    df = result['data']
    if df.empty:
        raise HTTPException(status_code=404, detail="No k-line data available")

    # Prepare chart data
    if result['freq'] == 'daily':
        x_data = df['trade_date'].tolist()
    else:
        x_data = df['trade_time'].tolist() if 'trade_time' in df.columns else df['trade_date'].tolist()

    return {
        "ts_code": ts_code,
        "freq": result['freq'],
        "x_data": x_data,
        "open": df['open'].tolist() if 'open' in df.columns else [],
        "high": df['high'].tolist() if 'high' in df.columns else [],
        "low": df['low'].tolist() if 'low' in df.columns else [],
        "close": df['close'].tolist() if 'close' in df.columns else [],
        "volume": df['vol'].tolist() if 'vol' in df.columns else []
    }
```

**Step 2: Commit**

```bash
git add backend/api/stocks.py
git commit -m "feat: add stocks API endpoints"
```

---

## Task 5: Update main.py to Include New Routers

**Files:**
- Modify: `backend/main.py`

**Step 1: Update imports and include routers**

In `backend/main.py`:

Change:
```python
from api import strategies, backtest, signals, notify
```

To:
```python
from api import strategies, backtest, signals, notify, watchlist, stocks
```

Add these lines after the other `app.include_router` calls:
```python
app.include_router(watchlist.router, prefix="/api/watchlist", tags=["watchlist"])
app.include_router(stocks.router, prefix="/api/stocks", tags=["stocks"])
```

**Step 2: Commit**

```bash
git add backend/main.py
git commit -m "feat: include watchlist and stocks routers in main.py"
```

---

## Task 6: Update Frontend API Methods

**Files:**
- Modify: `frontend/src/api/index.js`

**Step 1: Add new API methods**

Add to `frontend/src/api/index.js`:

```javascript
export const watchlistApi = {
  getList: () => api.get('/watchlist'),
  add: (data) => api.post('/watchlist', data),
  remove: (ts_code) => api.delete(`/watchlist/${ts_code}`),
  getQuotes: () => api.get('/watchlist/quotes')
}

export const stocksApi = {
  search: (keyword) => api.get(`/stocks/search?keyword=${encodeURIComponent(keyword)}`),
  list: (limit = 100) => api.get(`/stocks/list?limit=${limit}`),
  getKline: (ts_code, freq = 'auto') => api.get(`/stocks/${ts_code}/kline?freq=${freq}`)
}
```

Also export them from the file by adding:
```javascript
export { watchlistApi, stocksApi }
```

**Step 2: Commit**

```bash
git add frontend/src/api/index.js
git commit -m "feat: add watchlist and stocks API methods"
```

---

## Task 7: Create Watchlist KlineChart Component

**Files:**
- Create: `frontend/src/components/KlineChart.vue`

**Step 1: Create KlineChart.vue**

```vue
<template>
  <div ref="chartRef" style="height: 350px;"></div>
</template>

<script setup>
import { ref, onMounted, watch, onUnmounted } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  data: {
    type: Object,
    default: () => ({})
  }
})

const chartRef = ref(null)
let chart = null

const initChart = () => {
  if (!chartRef.value || !props.data.x_data) return
  chart = echarts.init(chartRef.value)

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      }
    },
    grid: {
      left: '10%',
      right: '5%',
      bottom: '15%',
      top: '10%'
    },
    xAxis: {
      type: 'category',
      data: props.data.x_data,
      axisLabel: {
        rotate: 45
      }
    },
    yAxis: {
      type: 'value',
      scale: true
    },
    series: [
      {
        type: 'candlestick',
        data: props.data.close ? props.data.close.map((_, i) => [
          props.data.open?.[i] || 0,
          props.data.close?.[i] || 0,
          props.data.low?.[i] || 0,
          props.data.high?.[i] || 0
        ]) : [],
        itemStyle: {
          color: '#ef4444',
          color0: '#10b981',
          borderColor: '#ef4444',
          borderColor0: '#10b981'
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
  if (props.data.x_data?.length > 0) {
    initChart()
  }
  window.addEventListener('resize', handleResize)
})

watch(() => props.data, () => {
  if (props.data.x_data?.length > 0) {
    initChart()
  }
}, { deep: true })

onUnmounted(() => {
  chart?.dispose()
  window.removeEventListener('resize', handleResize)
})
</script>
```

**Step 2: Commit**

```bash
git add frontend/src/components/KlineChart.vue
git commit -m "feat: add KlineChart component"
```

---

## Task 8: Create StockCard Component

**Files:**
- Create: `frontend/src/components/StockCard.vue`

**Step 1: Create StockCard.vue**

```vue
<template>
  <el-card class="stock-card" shadow="hover">
    <div class="card-header">
      <div class="stock-info">
        <h3>{{ quote.name }}</h3>
        <span class="ts-code">{{ quote.ts_code }}</span>
      </div>
      <el-button
        type="danger"
        size="small"
        circle
        @click="$emit('remove', quote.ts_code)"
      >
        <el-icon><Close /></el-icon>
      </el-button>
    </div>

    <div class="price-section" @click="toggleExpand">
      <div class="price-main">
        <span class="price" :class="priceClass">{{ formatPrice(quote.price) }}</span>
        <span class="change-pct" :class="priceClass">
          {{ formatChangePct(quote.change_pct) }}
        </span>
      </div>
      <el-icon class="expand-icon" :class="{ expanded: expanded }">
        <ArrowDown />
      </el-icon>
    </div>

    <el-row :gutter="10" class="stats-row">
      <el-col :span="8">
        <div class="stat-item">
          <span class="stat-label">最高</span>
          <span class="stat-value">{{ formatPrice(quote.high) }}</span>
        </div>
      </el-col>
      <el-col :span="8">
        <div class="stat-item">
          <span class="stat-label">最低</span>
          <span class="stat-value">{{ formatPrice(quote.low) }}</span>
        </div>
      </el-col>
      <el-col :span="8">
        <div class="stat-item">
          <span class="stat-label">开盘</span>
          <span class="stat-value">{{ formatPrice(quote.open) }}</span>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="10" class="stats-row">
      <el-col :span="8">
        <div class="stat-item">
          <span class="stat-label">成交量</span>
          <span class="stat-value">{{ formatVolume(quote.volume) }}</span>
        </div>
      </el-col>
      <el-col :span="8">
        <div class="stat-item">
          <span class="stat-label">PE</span>
          <span class="stat-value">{{ formatNumber(quote.pe) }}</span>
        </div>
      </el-col>
      <el-col :span="8">
        <div class="stat-item">
          <span class="stat-label">PB</span>
          <span class="stat-value">{{ formatNumber(quote.pb) }}</span>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="10" class="stats-row">
      <el-col :span="8">
        <div class="stat-item">
          <span class="stat-label">换手率</span>
          <span class="stat-value">{{ formatPercent(quote.turnover) }}</span>
        </div>
      </el-col>
    </el-row>

    <el-collapse-transition>
      <div v-show="expanded" class="kline-section">
        <el-divider />
        <div class="kline-header">
          <span>K线图 ({{ klineData?.freq || 'daily' }})</span>
          <el-button size="small" :loading="loadingKline" @click="loadKline">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
        <KlineChart v-if="klineData?.x_data" :data="klineData" />
        <el-empty v-else description="暂无K线数据" />
      </div>
    </el-collapse-transition>
  </el-card>
</template>

<script setup>
import { ref, computed } from 'vue'
import { Close, ArrowDown, Refresh } from '@element-plus/icons-vue'
import { stocksApi } from '@/api'
import KlineChart from './KlineChart.vue'

const props = defineProps({
  quote: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['remove'])

const expanded = ref(false)
const loadingKline = ref(false)
const klineData = ref(null)

const priceClass = computed(() => {
  if (!props.quote.change_pct) return ''
  return props.quote.change_pct >= 0 ? 'up' : 'down'
})

const formatPrice = (price) => {
  if (price === null || price === undefined) return '-'
  return price.toFixed(2)
}

const formatNumber = (num) => {
  if (num === null || num === undefined) return '-'
  return num.toFixed(2)
}

const formatPercent = (num) => {
  if (num === null || num === undefined) return '-'
  return num.toFixed(2) + '%'
}

const formatChangePct = (pct) => {
  if (pct === null || pct === undefined) return '-'
  const sign = pct >= 0 ? '+' : ''
  return sign + pct.toFixed(2) + '%'
}

const formatVolume = (vol) => {
  if (vol === null || vol === undefined) return '-'
  if (vol >= 100000000) {
    return (vol / 100000000).toFixed(2) + '亿'
  } else if (vol >= 10000) {
    return (vol / 10000).toFixed(2) + '万'
  }
  return vol.toFixed(0)
}

const toggleExpand = async () => {
  expanded.value = !expanded.value
  if (expanded.value && !klineData.value) {
    await loadKline()
  }
}

const loadKline = async () => {
  loadingKline.value = true
  try {
    const res = await stocksApi.getKline(props.quote.ts_code)
    klineData.value = res.data
  } catch (e) {
    console.error('Failed to load kline:', e)
  } finally {
    loadingKline.value = false
  }
}
</script>

<style scoped>
.stock-card {
  margin-bottom: 16px;
  cursor: pointer;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.stock-info h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.ts-code {
  color: #6b7280;
  font-size: 14px;
}

.price-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.price-main {
  display: flex;
  align-items: baseline;
  gap: 12px;
}

.price {
  font-size: 28px;
  font-weight: 700;
}

.price.up {
  color: #ef4444;
}

.price.down {
  color: #10b981;
}

.change-pct {
  font-size: 16px;
  font-weight: 600;
}

.change-pct.up {
  color: #ef4444;
}

.change-pct.down {
  color: #10b981;
}

.expand-icon {
  font-size: 20px;
  color: #9ca3af;
  transition: transform 0.3s;
}

.expand-icon.expanded {
  transform: rotate(180deg);
}

.stats-row {
  margin-bottom: 12px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat-label {
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 4px;
}

.stat-value {
  font-size: 14px;
  font-weight: 500;
}

.kline-section {
  margin-top: 8px;
}

.kline-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
</style>
```

**Step 2: Commit**

```bash
git add frontend/src/components/StockCard.vue
git commit -m "feat: add StockCard component"
```

---

## Task 9: Create StockSelectorModal Component

**Files:**
- Create: `frontend/src/components/StockSelectorModal.vue`

**Step 1: Create StockSelectorModal.vue**

```vue
<template>
  <el-dialog v-model="visible" title="从列表添加" width="700px" @closed="handleClosed">
    <div class="search-section">
      <el-input
        v-model="searchKeyword"
        placeholder="搜索股票代码或名称"
        clearable
        @input="handleSearch"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
    </div>

    <div class="stock-list">
      <el-table
        :data="displayStocks"
        @selection-change="handleSelectionChange"
        height="400"
        stripe
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="ts_code" label="代码" width="120" />
        <el-table-column prop="name" label="名称" />
        <el-table-column prop="industry" label="行业" />
      </el-table>
    </div>

    <template #footer>
      <div class="modal-footer">
        <span>已选择 {{ selectedStocks.length }} 只</span>
        <div>
          <el-button @click="visible = false">取消</el-button>
          <el-button type="primary" @click="handleAdd" :disabled="selectedStocks.length === 0">
            添加
          </el-button>
        </div>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { Search } from '@element-plus/icons-vue'
import { stocksApi } from '@/api'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  existingTsCodes: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['update:modelValue', 'add'])

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const searchKeyword = ref('')
const allStocks = ref([])
const selectedStocks = ref([])
const loading = ref(false)

const displayStocks = computed(() => {
  if (!searchKeyword.value) {
    return allStocks.value
  }
  const keyword = searchKeyword.value.toUpperCase()
  return allStocks.value.filter(s =>
    s.ts_code.toUpperCase().includes(keyword) ||
    s.name.includes(keyword)
  )
})

const loadStocks = async () => {
  loading.value = true
  try {
    const res = await stocksApi.list(200)
    allStocks.value = res.data.stocks.filter(s =>
      !props.existingTsCodes.includes(s.ts_code)
    )
  } catch (e) {
    console.error('Failed to load stocks:', e)
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  // Filtering happens in computed
}

const handleSelectionChange = (selection) => {
  selectedStocks.value = selection
}

const handleAdd = () => {
  emit('add', selectedStocks.value)
  visible.value = false
}

const handleClosed = () => {
  selectedStocks.value = []
  searchKeyword.value = ''
}

watch(() => props.modelValue, (val) => {
  if (val) {
    loadStocks()
  }
})
</script>

<style scoped>
.search-section {
  margin-bottom: 16px;
}

.stock-list {
  margin-bottom: 8px;
}

.modal-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
```

**Note:** Add the missing import for `computed` in the script setup section.

**Step 2: Fix import and commit**

Add `computed` to the import:
```javascript
import { ref, computed, watch, onMounted } from 'vue'
```

```bash
git add frontend/src/components/StockSelectorModal.vue
git commit -m "feat: add StockSelectorModal component"
```

---

## Task 10: Create Watchlist View

**Files:**
- Create: `frontend/src/views/Watchlist.vue`

**Step 1: Create Watchlist.vue**

```vue
<template>
  <div class="watchlist">
    <el-card class="header-card">
      <div class="header-content">
        <div>
          <h2>我的自选</h2>
          <p>管理和查看自选股行情</p>
        </div>
        <div class="header-actions">
          <el-button @click="showSelector = true">
            <el-icon><List /></el-icon>
            从列表添加
          </el-button>
          <el-input
            v-model="searchAddKeyword"
            placeholder="输入代码或名称添加"
            style="width: 240px"
            clearable
            @keyup.enter="handleSearchAdd"
          >
            <template #append>
              <el-button @click="handleSearchAdd" :loading="searching">
                <el-icon><Plus /></el-icon>
                添加
              </el-button>
            </template>
          </el-input>
          <el-button type="primary" @click="refreshQuotes" :loading="loading">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </div>
    </el-card>

    <el-empty v-if="!loading && watchlist.length === 0" description="暂无自选股，快去添加吧！" />

    <el-row :gutter="16" class="cards-grid" v-else>
      <el-col :xs="24" :sm="12" :md="8" :lg="6" v-for="quote in quotes" :key="quote.ts_code">
        <StockCard :quote="quote" @remove="handleRemove" />
      </el-col>
    </el-row>

    <StockSelectorModal
      v-model="showSelector"
      :existing-ts-codes="watchlist.map(w => w.ts_code)"
      @add="handleBulkAdd"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { List, Plus, Refresh } from '@element-plus/icons-vue'
import { watchlistApi, stocksApi } from '@/api'
import StockCard from '@/components/StockCard.vue'
import StockSelectorModal from '@/components/StockSelectorModal.vue'

const loading = ref(false)
const searching = ref(false)
const watchlist = ref([])
const quotes = ref([])
const searchAddKeyword = ref('')
const showSelector = ref(false)

const loadWatchlist = async () => {
  try {
    const res = await watchlistApi.getList()
    watchlist.value = res.data.watchlist
  } catch (e) {
    console.error('Failed to load watchlist:', e)
  }
}

const refreshQuotes = async () => {
  loading.value = true
  try {
    const res = await watchlistApi.getQuotes()
    quotes.value = res.data.quotes
  } catch (e) {
    ElMessage.error('刷新行情失败')
  } finally {
    loading.value = false
  }
}

const handleSearchAdd = async () => {
  if (!searchAddKeyword.value) {
    ElMessage.warning('请输入股票代码或名称')
    return
  }
  searching.value = true
  try {
    const res = await stocksApi.search(searchAddKeyword.value)
    const stocks = res.data.stocks
    if (stocks.length === 0) {
      ElMessage.warning('未找到匹配的股票')
      return
    }
    const stock = stocks[0]
    await watchlistApi.add({ ts_code: stock.ts_code, name: stock.name })
    ElMessage.success(`已添加 ${stock.name}`)
    searchAddKeyword.value = ''
    await loadWatchlist()
    await refreshQuotes()
  } catch (e) {
    if (e.response?.status === 400) {
      ElMessage.warning('该股票已在自选股中')
    } else {
      ElMessage.error('添加失败')
    }
  } finally {
    searching.value = false
  }
}

const handleBulkAdd = async (stocks) => {
  let added = 0
  for (const stock of stocks) {
    try {
      await watchlistApi.add({ ts_code: stock.ts_code, name: stock.name })
      added++
    } catch (e) {
      console.error(`Failed to add ${stock.ts_code}:`, e)
    }
  }
  ElMessage.success(`成功添加 ${added} 只股票`)
  await loadWatchlist()
  await refreshQuotes()
}

const handleRemove = async (ts_code) => {
  try {
    await watchlistApi.remove(ts_code)
    ElMessage.success('已移除')
    await loadWatchlist()
    await refreshQuotes()
  } catch (e) {
    ElMessage.error('移除失败')
  }
}

onMounted(() => {
  loadWatchlist()
  refreshQuotes()
})
</script>

<style scoped>
.watchlist {
  max-width: 1400px;
  margin: 0 auto;
}

.header-card {
  margin-bottom: 20px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
}

.header-content h2 {
  font-size: 24px;
  margin-bottom: 4px;
}

.header-content p {
  color: #6b7280;
}

.header-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.cards-grid {
  margin-top: 20px;
}
</style>
```

**Step 2: Commit**

```bash
git add frontend/src/views/Watchlist.vue
git commit -m "feat: add Watchlist view"
```

---

## Task 11: Update Router and Navigation

**Files:**
- Modify: `frontend/src/router/index.js`
- Modify: `frontend/src/App.vue`

**Step 1: Update router**

Add to `frontend/src/router/index.js` routes:

```javascript
{
  path: '/watchlist',
  name: 'Watchlist',
  component: () => import('@/views/Watchlist.vue')
}
```

**Step 2: Update App.vue navigation**

Add to `frontend/src/App.vue` nav links:

```html
<router-link to="/watchlist">自选股</router-link>
```

(Insert it after "仪表盘" and before "策略回测")

**Step 3: Commit**

```bash
git add frontend/src/router/index.js frontend/src/App.vue
git commit -m "feat: add watchlist to router and navigation"
```

---

## Task 12: Test and Verify

**Files:**
- Verify all components work together

**Step 1: Run backend (if not already running)**

```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload --port 8000
```

**Step 2: Run frontend (if not already running)**

```bash
cd frontend
npm run dev
```

**Step 3: Manual Test Checklist**

- [ ] Navigate to /watchlist
- [ ] Search and add a stock (e.g., 000001.SZ)
- [ ] Verify stock card displays correctly
- [ ] Click card to expand k-line chart
- [ ] Refresh quotes manually
- [ ] Remove a stock
- [ ] Use "从列表添加" to bulk add multiple stocks
- [ ] Verify all stats display (PE, PB, turnover, etc.)

---

## Execution Summary

Plan complete and saved to `docs/plans/2026-03-05-watchlist-implementation.md`.

**Two execution options:**

1. **Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

2. **Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

**Which approach?**
