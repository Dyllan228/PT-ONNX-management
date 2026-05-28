import { defineStore } from 'pinia'
import { ref } from 'vue'
import request from '../api/request'

export const useModelStore = defineStore('models', () => {
  const models = ref([])
  const loading = ref(false)

  async function fetchModels() {
    loading.value = true
    try {
      const res = await request.get('/models')
      models.value = res.data
    } finally {
      loading.value = false
    }
  }

  return { models, loading, fetchModels }
})
