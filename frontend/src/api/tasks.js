import request from './request'

export const getTask = (taskId) => request.get(`/tasks/${taskId}`)
export const deleteTask = (taskId) => request.delete(`/tasks/${taskId}`)
