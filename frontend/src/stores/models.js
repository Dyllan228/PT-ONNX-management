/**
 * 模型状态管理 Store
 *
 * 使用 Pinia 管理模型列表的全局状态
 *
 * 技术栈：
 * - Pinia: Vue 3 状态管理库
 * - Vue 3 Composition API: ref、computed 等响应式 API
 *
 * 状态：
 * - models: 模型列表
 * - loading: 加载状态
 *
 * 方法：
 * - fetchModels: 获取模型列表
 */

import { defineStore } from 'pinia'
import { ref } from 'vue'
import request from '../api/request'

/**
 * 定义模型 Store
 *
 * 使用 Composition API 风格（setup 函数）
 */
export const useModelStore = defineStore('models', () => {
  // ===== 状态 =====
  const models = ref([])      // 模型列表
  const loading = ref(false)  // 加载状态

  // ===== 方法 =====

  /**
   * 获取模型列表
   *
   * 从后端 API 获取所有模型并更新状态
   * 无论成功或失败都会清除 loading 状态
   */
  async function fetchModels() {
    loading.value = true
    try {
      const res = await request.get('/models')
      models.value = res.data
    } finally {
      loading.value = false
    }
  }

  // 返回状态和方法
  return { models, loading, fetchModels }
})
