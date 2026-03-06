<template>
  <el-table :data="signals" stripe v-loading="loading">
    <el-table-column prop="signal_date" label="日期" width="100" />
    <el-table-column prop="ts_code" label="代码" width="110" />
    <el-table-column prop="name" label="名称" width="120" />
    <el-table-column prop="strategy_name" label="策略" min-width="140" />
    <el-table-column prop="signal_type" label="信号" width="80">
      <template #default="{ row }">
        <el-tag :type="row.signal_type === 'BUY' ? 'success' : 'danger'">
          {{ row.signal_type === 'BUY' ? '买入' : '卖出' }}
        </el-tag>
      </template>
    </el-table-column>
    <el-table-column prop="price" label="价格" width="100">
      <template #default="{ row }">
        {{ row.price.toFixed(2) }}
      </template>
    </el-table-column>
    <el-table-column prop="is_sent" label="已通知" width="80">
      <template #default="{ row }">
        <el-tag v-if="row.is_sent" type="info" size="small">是</el-tag>
        <el-tag v-else type="info" size="small" effect="plain">否</el-tag>
      </template>
    </el-table-column>
    <el-table-column prop="created_at" label="时间" width="170">
      <template #default="{ row }">
        {{ formatDate(row.created_at) }}
      </template>
    </el-table-column>
  </el-table>
</template>

<script setup>
const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  try {
    const date = new Date(dateStr)
    if (!isNaN(date.getTime())) {
      return date.toLocaleString('zh-CN')
    }
  } catch (e) {
    // ignore
  }
  return String(dateStr)
}

defineProps({
  signals: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  }
})
</script>
