<template>
  <div class="signals">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>信号历史</span>
        </div>
      </template>
      <SignalList :signals="signals" :loading="loading" />
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { signalsApi } from '@/api'
import SignalList from '@/components/SignalList.vue'

const loading = ref(false)
const signals = ref([])

const loadSignals = async () => {
  loading.value = true
  try {
    const res = await signalsApi.getList(0, 100)
    signals.value = res.data.signals
  } catch (e) {
    ElMessage.error('获取信号失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadSignals()
})
</script>

<style scoped>
.signals {
  max-width: 1200px;
  margin: 0 auto;
}

.card-header {
  font-weight: 600;
}
</style>
