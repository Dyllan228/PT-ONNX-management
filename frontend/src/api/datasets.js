import request from './request'

export const getDatasets = () => request.get('/datasets')
export const uploadDataset = (formData) => request.post('/datasets/upload', formData, {
  headers: { 'Content-Type': 'multipart/form-data' },
})
