<template>
  <div ref="chartRef" :style="{ width: '100%', height: height + 'px' }"></div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  option: { type: Object, required: true },
  height: { type: Number, default: 400 },
})

const chartRef = ref(null)
let chart = null

onMounted(() => {
  chart = echarts.init(chartRef.value)
  chart.setOption(props.option)
  window.addEventListener('resize', () => chart?.resize())
})

watch(() => props.option, (opt) => {
  chart?.setOption(opt, true)
}, { deep: true })

onUnmounted(() => {
  chart?.dispose()
})
</script>
