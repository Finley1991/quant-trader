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
import { ref, computed, watch } from 'vue'
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
