import request from './request'

export const createBenchmarkTask = (data) => request.post('/benchmark', data)
export const getBenchmarkTask = (taskId) => request.get(`/benchmark/${taskId}`)
