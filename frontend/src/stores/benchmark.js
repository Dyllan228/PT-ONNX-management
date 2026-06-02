/**
 * 性能对比状态管理 Store
 *
 * 使用 Pinia 管理性能对比结果的全局状态
 *
 * 技术栈：
 * - Pinia: Vue 3 状态管理库
 * - Vue 3 Composition API: ref 等响应式 API
 *
 * 状态：
 * - results: 对比结果列表
 * - taskInfo: 任务信息
 *
 * 方法：
 * - setResults: 设置对比结果
 * - setTaskInfo: 设置任务信息
 * - reset: 重置状态
 */

import { defineStore } from 'pinia'
import { ref } from 'vue'

/**
 * 定义性能对比 Store
 *
 * 使用 Composition API 风格（setup 函数）
 */
export const useBenchmarkStore = defineStore('benchmark', () => {
  // ===== 状态 =====
  const results = ref([])      // 对比结果列表
  const taskInfo = ref(null)   // 任务信息

  // ===== 方法 =====

  /**
   * 设置对比结果
   * @param {Array} data - 对比结果数组
   */
  function setResults(data) {
    results.value = data
  }

  /**
   * 设置任务信息
   * @param {object} info - 任务信息
   */
  function setTaskInfo(info) {
    taskInfo.value = info
  }

  /**
   * 重置所有状态
   */
  function reset() {
    results.value = []
    taskInfo.value = null
  }

  // 返回状态和方法
  return { results, taskInfo, setResults, setTaskInfo, reset }
})
