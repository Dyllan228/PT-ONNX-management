/**
 * 推理可视化 API 模块
 *
 * 提供推理任务相关的 API 调用函数
 *
 * API 端点：
 * - POST   /api/inference              - 创建推理任务
 * - GET    /api/inference/:id           - 查询推理任务状态
 * - DELETE /api/inference/:id           - 取消推理任务
 * - GET    /api/inference/:id/image/:idx - 获取结果图片
 * - GET    /api/inference/:id/video     - 获取结果视频
 */

import request from './request'

/**
 * 创建推理任务
 * @param {FormData} formData - 包含以下字段的表单数据：
 *   - mid: 模型 ID
 *   - mtype: 模型类型（pt/onnx）
 *   - device: 推理设备（cpu/cuda）
 *   - confidence_threshold: 置信度阈值
 *   - dataset_path: 数据集路径（可选）
 *   - file: 上传的文件（可选）
 * @returns {Promise} 任务信息（包含 task_id）
 */
export const createInferenceTask = (formData) => request.post('/inference', formData, {
  headers: { 'Content-Type': 'multipart/form-data' },
})

/**
 * 查询推理任务状态
 * @param {string} taskId - 任务 ID
 * @returns {Promise} 任务状态（status、progress、result、error_msg）
 */
export const getInferenceTask = (taskId) => request.get(`/inference/${taskId}`)

/**
 * 取消推理任务
 * @param {string} taskId - 任务 ID
 * @returns {Promise} 取消结果
 */
export const cancelInferenceTask = (taskId) => request.delete(`/inference/${taskId}`)

/**
 * 获取结果图片 URL
 * @param {string} taskId - 任务 ID
 * @param {number} frameIdx - 帧序号
 * @returns {string} 图片 URL
 */
export const getResultImage = (taskId, frameIdx) => `/api/inference/${taskId}/image/${frameIdx}`
