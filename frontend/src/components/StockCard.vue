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
