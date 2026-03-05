<template>
  <div class="backtest">
    <el-card class="form-card">
      <template #header>
        <div class="card-header">
          <span>策略回测</span>
        </div>
      </template>

      <el-form :model="form" label-width="120px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="策略">
              <el-select v-model="form.strategy_name" placeholder="选择策略" style="width: 100%">
                <el-option
                  v-for="s in presets"
                  :key="s.name"
                  :label="s.name"
                  :value="s.name"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="股票代码">
              <el-input v-model="form.ts_code" placeholder="如: 000001.SZ" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="开始日期">
              <el-date-picker
                v-model="form.start_date"
                type="date"
                placeholder="开始日期"
                value-format="YYYYMMDD"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="结束日期">
              <el-date-picker
                v-model="form.end_date"
                type="date"
                placeholder="结束日期"
                value-format="YYYYMMDD"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="初始资金">
              <el-input-number v-model="form.initial_capital" :min="10000" :step="10000" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item>
          <el-button type="primary" @click="runBacktest" :loading="running">
            开始回测
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card v-if="result" class="result-card">
      <template #header>
        <div class="card-header">
          <span>回测结果</span>
        </div>
      </template>

      <el-row :gutter="20" class="result-stats">
        <el-col :span="6">
          <div class="stat-item">
            <div class="stat-label">总收益率</div>
            <div class="stat-value" :class="{ positive: result.total_return > 0 }">
              {{ result.total_return.toFixed(2) }}%
            </div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-item">
            <div class="stat-label">最大回撤</div>
            <div class="stat-value negative">{{ result.max_drawdown.toFixed(2) }}%</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-item">
            <div class="stat-label">胜率</div>
            <div class="stat-value">{{ result.win_rate ? result.win_rate.toFixed(2) + '%' : '-' }}</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-item">
            <div class="stat-label">夏普比率</div>
            <div class="stat-value">{{ result.sharpe_ratio ? result.sharpe_ratio.toFixed(2) : '-' }}</div>
          </div>
        </el-col>
      </el-row>

      <BacktestChart :data="result.equity_curve" />
    </el-card>

    <el-card class="history-card">
      <template #header>
        <div class="card-header">
          <span>历史回测</span>
        </div>
      </template>

      <el-table :data="history" stripe>
        <el-table-column prop="strategy_name" label="策略" />
        <el-table-column prop="start_date" label="开始日期" />
        <el-table-column prop="end_date" label="结束日期" />
        <el-table-column prop="total_return" label="收益率">
          <template #default="{ row }">
            <span :class="{ positive: row.total_return > 0, negative: row.total_return < 0 }">
              {{ row.total_return.toFixed(2) }}%
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="max_drawdown" label="最大回撤">
          <template #default="{ row }">
            <span class="negative">{{ row.max_drawdown.toFixed(2) }}%</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间">
          <template #default="{ row }">
            {{ new Date(row.created_at).toLocaleString() }}
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { strategiesApi, backtestApi } from '@/api'
import BacktestChart from '@/components/BacktestChart.vue'

const presets = ref([])
const history = ref([])
const running = ref(false)
const result = ref(null)

const form = ref({
  strategy_name: '',
  ts_code: '',
  start_date: '',
  end_date: '',
  initial_capital: 100000
})

const loadPresets = async () => {
  try {
    const res = await strategiesApi.getPresets()
    presets.value = res.data.strategies
    if (presets.value.length > 0) {
      form.value.strategy_name = presets.value[0].name
    }
  } catch (e) {
    ElMessage.error('加载策略失败')
  }
}

const loadHistory = async () => {
  try {
    const res = await backtestApi.getHistory()
    history.value = res.data.backtests
  } catch (e) {
    ElMessage.error('加载历史失败')
  }
}

const runBacktest = async () => {
  if (!form.value.strategy_name || !form.value.ts_code) {
    ElMessage.warning('请填写策略和股票代码')
    return
  }

  running.value = true
  try {
    const res = await backtestApi.run(form.value)
    result.value = res.data
    ElMessage.success('回测完成')
    loadHistory()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '回测失败')
  } finally {
    running.value = false
  }
}

onMounted(() => {
  loadPresets()
  loadHistory()
})
</script>

<style scoped>
.backtest {
  max-width: 1200px;
  margin: 0 auto;
}

.form-card {
  margin-bottom: 20px;
}

.card-header {
  font-weight: 600;
}

.result-card {
  margin-bottom: 20px;
}

.result-stats {
  margin-bottom: 24px;
}

.stat-item {
  text-align: center;
}

.stat-label {
  color: #6b7280;
  font-size: 14px;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
}

.stat-value.positive {
  color: #10b981;
}

.stat-value.negative {
  color: #ef4444;
}

.history-card {
  margin-bottom: 20px;
}

.positive {
  color: #10b981;
}

.negative {
  color: #ef4444;
}
</style>
