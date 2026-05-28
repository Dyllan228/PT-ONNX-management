import request from './request'

export const createConvertTask = (data) => request.post('/convert', data)
export const getConvertTask = (taskId) => request.get(`/convert/${taskId}`)
