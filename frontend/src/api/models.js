/**
 * 模型管理 API 模块
 *
 * 提供模型管理相关的 API 调用函数
 *
 * API 端点：
 * - GET    /api/models           - 获取模型列表
 * - GET    /api/models/:id       - 获取单个模型详情
 * - POST   /api/models/upload    - 上传模型
 * - PUT    /api/models/:id       - 更新模型信息
 * - DELETE /api/models/:id       - 删除模型
 * - POST   /api/models/scan      - 扫描并注册新模型
 * - GET    /api/models/:id/download/:type - 下载模型文件
 */

import request from './request'

/**
 * 获取所有模型列表
 * @returns {Promise} 模型列表
 */
export const getModels = () => request.get('/models')

/**
 * 获取单个模型详情
 * @param {number} id - 模型 ID
 * @returns {Promise} 模型详情
 */
export const getModel = (id) => request.get(`/models/${id}`)

/**
 * 上传 PT 模型文件
 * @param {FormData} formData - 包含 file、name、version 的表单数据
 * @returns {Promise} 新创建的模型信息
 */
export const uploadModel = (formData) => request.post('/models/upload', formData, {
  headers: { 'Content-Type': 'multipart/form-data' },
})

/**
 * 更新模型信息
 * @param {number} id - 模型 ID
 * @param {object} data - 更新数据（name、version、description 等）
 * @returns {Promise} 更新后的模型信息
 */
export const updateModel = (id, data) => request.put(`/models/${id}`, data)

/**
 * 删除模型
 * @param {number} id - 模型 ID
 * @returns {Promise} 删除结果
 */
export const deleteModel = (id) => request.delete(`/models/${id}`)

/**
 * 扫描并注册新模型
 * 扫描项目目录中的 .pt 文件并自动注册
 * @returns {Promise} 扫描结果（包含新注册数量）
 */
export const scanModels = () => request.post('/models/scan')

/**
 * 获取模型下载 URL
 * @param {number} id - 模型 ID
 * @param {string} type - 模型类型（"pt" 或 "onnx"）
 * @returns {string} 下载 URL
 */
export const getModelDownloadUrl = (id, type) => `/api/models/${id}/download/${type}`
