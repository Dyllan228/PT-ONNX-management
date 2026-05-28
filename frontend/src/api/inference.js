import request from './request'

export const createInferenceTask = (formData) => request.post('/inference', formData, {
  headers: { 'Content-Type': 'multipart/form-data' },
})
export const getInferenceTask = (taskId) => request.get(`/inference/${taskId}`)
export const getResultImage = (taskId, frameIdx) => `/api/inference/${taskId}/image/${frameIdx}`
