<!--
  ECharts 图表组件

  功能：
  - 封装 ECharts 图表
  - 支持响应式更新
  - 支持自定义高度
  - 自动处理窗口大小变化

  使用示例：
  <MetricsChart :option="chartOption" :height="400" />

  Props：
  - option: ECharts 配置对象（必填）
  - height: 图表高度（默认 400）

  技术栈：
  - ECharts: 数据可视化库
  - Vue 3 Composition API
-->

<template>
  <div ref="chartRef" :style="{ width: '100%', height: height + 'px' }"></div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import * as echarts from 'echarts'

/**
 * Props 定义
 * @property {object} option - ECharts 配置对象
 * @property {number} height - 图表高度
 */
const props = defineProps({
  option: { type: Object, required: true },
  height: { type: Number, default: 400 },
})

// 图表 DOM 引用
const chartRef = ref(null)
// ECharts 实例
let chart = null

/**
 * 组件挂载时初始化图表
 */
onMounted(() => {
  // 初始化 ECharts 实例
  chart = echarts.init(chartRef.value)
  // 设置图表配置
  chart.setOption(props.option)
  // 监听窗口大小变化，自动调整图表尺寸
  window.addEventListener('resize', () => chart?.resize())
})

/**
 * 监听配置变化，更新图表
 * deep: true 表示深度监听对象内部变化
 */
watch(() => props.option, (opt) => {
  chart?.setOption(opt, true)
}, { deep: true })

/**
 * 组件卸载时销毁图表实例，释放资源
 */
onUnmounted(() => {
  chart?.dispose()
})
</script>
