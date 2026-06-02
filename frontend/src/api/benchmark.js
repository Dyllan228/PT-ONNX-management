/**
 * 性能对比 API 模块
 *
 * 提供性能对比相关的 API 调用函数
 *
 * API 端点：
 * - POST /api/benchmark      - 创建对比任务
 * - GET  /api/benchmark/:id   - 查询对比任务状态
 */

import request from './request'

/**
 * 创建性能对比任务
 * @param {object} data - 对比参数
 * @param {number[]} data.model_ids - 模型 ID 列表
 * @param {string[]} data.model_types - 模型类型列表（pt/onnx）
 * @param {string[]} data.devices - 测试设备列表（cpu/cuda）
 * @param {number} data.dataset_id - 数据集 ID（可选）
 * @param {string} data.dataset_split - 数据集子集（train/test/val）
 * @param {number} data.num_runs - 测试次数
 * @param {boolean} data.evaluate - 是否评估准确度
 * @returns {Promise} 任务信息（包含 task_id）
 */
export const createBenchmarkTask = (data) => request.post('/benchmark', data)

/**
 * 查询性能对比任务状态
 * @param {string} taskId - 任务 ID
 * @returns {Promise} 任务状态（status、progress、result、error_msg）
 */
export const getBenchmarkTask = (taskId) => request.get(`/benchmark/${taskId}`)
