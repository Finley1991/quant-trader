<template>
  <div ref="chartRef" style="height: 400px;"></div>
</template>

<script setup>
import { ref, onMounted, watch, onUnmounted } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  data: {
    type: Array,
    default: () => []
  }
})

const chartRef = ref(null)
let chart = null

const initChart = () => {
  if (!chartRef.value) return
  chart = echarts.init(chartRef.value)

  const dates = props.data.map(d => d.date)
  const equity = props.data.map(d => d.equity)

  const initial = props.data[0]?.equity || 100000

  const option = {
    tooltip: {
      trigger: 'axis',
      formatter: (params) => {
        const p = params[0]
        const ret = ((p.value - initial) / initial * 100).toFixed(2)
        return `${p.axisValue}<br/>资金: ${p.value.toFixed(2)}<br/>收益: ${ret}%`
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: dates
    },
    yAxis: {
      type: 'value'
    },
    series: [
      {
        name: '资金曲线',
        type: 'line',
        smooth: true,
        data: equity,
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(16, 185, 129, 0.3)' },
            { offset: 1, color: 'rgba(16, 185, 129, 0.05)' }
          ])
        },
        lineStyle: {
          color: '#10b981'
        },
        itemStyle: {
          color: '#10b981'
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
  if (props.data.length > 0) {
    initChart()
  }
  window.addEventListener('resize', handleResize)
})

watch(() => props.data, () => {
  if (props.data.length > 0) {
    initChart()
  }
}, { deep: true })

onUnmounted(() => {
  chart?.dispose()
  window.removeEventListener('resize', handleResize)
})
</script>
