/**
 * 模型转换 API 模块
 *
 * 提供模型转换相关的 API 调用函数
 *
 * API 端点：
 * - POST /api/convert      - 创建转换任务
 * - GET  /api/convert/:id   - 查询转换任务状态
 */

import request from './request'

/**
 * 创建模型转换任务
 * @param {object} data - 转换参数
 * @param {number} data.model_id - 模型 ID
 * @param {number[]} data.input_size - 输入尺寸 [宽, 高]
 * @param {boolean} data.dynamic_batch - 是否支持动态 Batch
 * @param {number} data.opset_version - ONNX Opset 版本
 * @returns {Promise} 任务信息（包含 task_id）
 */
export const createConvertTask = (data) => request.post('/convert', data)

/**
 * 查询转换任务状态
 * @param {string} taskId - 任务 ID
 * @returns {Promise} 任务状态（status、progress、result、error_msg）
 */
export const getConvertTask = (taskId) => request.get(`/convert/${taskId}`)
