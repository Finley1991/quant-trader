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
