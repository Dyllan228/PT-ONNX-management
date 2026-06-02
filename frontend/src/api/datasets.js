/**
 * 数据集管理 API 模块
 *
 * 提供数据集管理相关的 API 调用函数
 *
 * API 端点：
 * - GET    /api/datasets/sources       - 获取数据源列表
 * - POST   /api/datasets/upload        - 上传数据文件
 * - GET    /api/datasets               - 获取数据集列表
 * - GET    /api/datasets/:id           - 获取数据集详情
 * - POST   /api/datasets/import        - 导入数据集（ZIP）
 * - PUT    /api/datasets/:id           - 更新数据集
 * - DELETE /api/datasets/:id           - 删除数据集
 * - GET    /api/datasets/:id/download  - 下载数据集
 * - GET    /api/datasets/:id/splits    - 获取数据集子集
 */

import request from './request'

/**
 * 获取数据源文件列表
 * 扫描项目根目录和上传目录中的图片/视频文件
 * @returns {Promise} 数据源列表
 */
export const getDataSources = () => request.get('/datasets/sources')

/**
 * 上传单个数据文件（图片/视频）
 * @param {FormData} formData - 包含 file 的表单数据
 * @returns {Promise} 上传结果（包含文件路径和类型）
 */
export const uploadDataSource = (formData) => request.post('/datasets/upload', formData, {
  headers: { 'Content-Type': 'multipart/form-data' },
})

/**
 * 获取所有已管理的数据集列表
 * @returns {Promise} 数据集列表
 */
export const getDatasets = () => request.get('/datasets')

/**
 * 获取单个数据集详情
 * @param {number} id - 数据集 ID
 * @returns {Promise} 数据集详情
 */
export const getDataset = (id) => request.get(`/datasets/${id}`)

/**
 * 导入 YOLO 格式数据集
 * @param {FormData} formData - 包含 file、name、description 的表单数据
 * @returns {Promise} 导入结果（包含分析统计）
 */
export const importDataset = (formData) => request.post('/datasets/import', formData, {
  headers: { 'Content-Type': 'multipart/form-data' },
})

/**
 * 更新数据集信息
 * @param {number} id - 数据集 ID
 * @param {object} data - 更新数据（name、description）
 * @returns {Promise} 更新结果
 */
export const updateDataset = (id, data) => request.put(`/datasets/${id}`, data)

/**
 * 删除数据集
 * @param {number} id - 数据集 ID
 * @returns {Promise} 删除结果
 */
export const deleteDataset = (id) => request.delete(`/datasets/${id}`)

/**
 * 获取数据集子集信息
 * 检测 train/test/val 子目录
 * @param {number} id - 数据集 ID
 * @returns {Promise} 子集列表
 */
export const getDatasetSplits = (id) => request.get(`/datasets/${id}/splits`)

/**
 * 获取数据集下载 URL
 * @param {number} id - 数据集 ID
 * @returns {string} 下载 URL
 */
export const getDatasetDownloadUrl = (id) => `/api/datasets/${id}/download`
