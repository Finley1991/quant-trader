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
