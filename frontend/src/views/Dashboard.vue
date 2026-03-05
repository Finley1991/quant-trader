<template>
  <div class="dashboard">
    <el-card class="header-card">
      <div class="header-content">
        <div>
          <h2>实时信号</h2>
          <p>今日信号概览</p>
        </div>
        <el-button type="primary" @click="refreshSignals">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </el-card>

    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-label">今日买入</div>
          <div class="stat-value buy">{{ buyCount }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-label">今日卖出</div>
          <div class="stat-value sell">{{ sellCount }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-label">总信号</div>
          <div class="stat-value">{{ todaySignals.length }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-label">操作</div>
          <el-button type="primary" @click="triggerScan">手动扫描</el-button>
        </el-card>
      </el-col>
    </el-row>

    <el-card class="signals-card">
      <template #header>
        <div class="card-header">
          <span>今日信号</span>
        </div>
      </template>
      <SignalList :signals="todaySignals" :loading="loading" />
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import { signalsApi } from '@/api'
import SignalList from '@/components/SignalList.vue'

const loading = ref(false)
const todaySignals = ref([])

const buyCount = ref(0)
const sellCount = ref(0)

const refreshSignals = async () => {
  loading.value = true
  try {
    const res = await signalsApi.getToday()
    todaySignals.value = res.data.signals

    buyCount.value = todaySignals.value.filter(s => s.signal_type === 'BUY').length
    sellCount.value = todaySignals.value.filter(s => s.signal_type === 'SELL').length
  } catch (e) {
    ElMessage.error('获取信号失败')
  } finally {
    loading.value = false
  }
}

const triggerScan = async () => {
  try {
    ElMessage.info('开始扫描...')
    const res = await signalsApi.scan()
    ElMessage.success(`扫描完成，发现 ${res.data.signals} 个信号`)
    refreshSignals()
  } catch (e) {
    ElMessage.error('扫描失败')
  }
}

onMounted(() => {
  refreshSignals()
})
</script>

<style scoped>
.dashboard {
  max-width: 1200px;
  margin: 0 auto;
}

.header-card {
  margin-bottom: 20px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-content h2 {
  font-size: 24px;
  margin-bottom: 4px;
}

.header-content p {
  color: #6b7280;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  text-align: center;
}

.stat-label {
  color: #6b7280;
  font-size: 14px;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
}

.stat-value.buy {
  color: #10b981;
}

.stat-value.sell {
  color: #ef4444;
}

.signals-card {
  margin-bottom: 20px;
}

.card-header {
  font-weight: 600;
}
</style>
