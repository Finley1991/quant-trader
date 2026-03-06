<template>
  <div class="watchlist">
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
          <el-button @click="showSelector = true">
            <el-icon><List /></el-icon>
            从列表添加
          </el-button>
          <el-input
            v-model="searchAddKeyword"
            :placeholder="searchMode === 'stock' ? '输入股票代码或名称' : '输入基金代码或名称'"
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

    <el-empty v-if="!loading && watchlist.length === 0" :description="emptyDescription" />

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
import { ref, onMounted, watch, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { List, Plus, Refresh } from '@element-plus/icons-vue'
import { watchlistApi, stocksApi, fundsApi } from '@/api'
import StockCard from '@/components/StockCard.vue'
import StockSelectorModal from '@/components/StockSelectorModal.vue'

const loading = ref(false)
const searching = ref(false)
const watchlist = ref([])
const quotes = ref([])
const searchAddKeyword = ref('')
const showSelector = ref(false)
const currentAssetType = ref('')
const searchMode = ref('stock')

const emptyDescription = computed(() => {
  if (currentAssetType.value === '') {
    return '暂无自选，快去添加吧！'
  } else if (currentAssetType.value === 'stock') {
    return '暂无自选股，快去添加吧！'
  } else {
    return '暂无自选基金，快去添加吧！'
  }
})

const loadWatchlist = async () => {
  try {
    const res = await watchlistApi.getList(currentAssetType.value || undefined)
    watchlist.value = res.data.watchlist
  } catch (e) {
    console.error('Failed to load watchlist:', e)
  }
}

const refreshQuotes = async () => {
  loading.value = true
  try {
    const res = await watchlistApi.getQuotes()
    let allQuotes = res.data.quotes || []
    if (currentAssetType.value) {
      const watchlistMap = {}
      watchlist.value.forEach(w => {
        watchlistMap[w.ts_code] = w.asset_type
      })
      allQuotes = allQuotes.filter(q => watchlistMap[q.ts_code] === currentAssetType.value)
    }
    quotes.value = allQuotes
  } catch (e) {
    ElMessage.error('刷新行情失败')
  } finally {
    loading.value = false
  }
}

const handleSearchAdd = async () => {
  if (!searchAddKeyword.value) {
    ElMessage.warning(searchMode.value === 'stock' ? '请输入股票代码或名称' : '请输入基金代码或名称')
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

const handleBulkAdd = async (stocks) => {
  let added = 0
  for (const stock of stocks) {
    try {
      await watchlistApi.add({ ts_code: stock.ts_code, name: stock.name, asset_type: 'stock' })
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

watch(currentAssetType, () => {
  loadWatchlist()
  refreshQuotes()
})

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

.asset-tabs {
  margin-right: 16px;
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
