import request from './request'

export const getModels = () => request.get('/models')
export const getModel = (id) => request.get(`/models/${id}`)
export const uploadModel = (formData) => request.post('/models/upload', formData, {
  headers: { 'Content-Type': 'multipart/form-data' },
})
export const updateModel = (id, data) => request.put(`/models/${id}`, data)
export const deleteModel = (id) => request.delete(`/models/${id}`)
export const scanModels = () => request.post('/models/scan')
