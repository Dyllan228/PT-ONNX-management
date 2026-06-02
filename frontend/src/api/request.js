/**
 * HTTP 请求封装模块
 *
 * 本模块封装了 axios 实例，提供统一的请求配置和错误处理
 *
 * 技术栈：
 * - axios: HTTP 客户端库
 * - Element Plus: UI 组件库（用于错误提示）
 *
 * 配置说明：
 * - baseURL: API 基础路径（/api）
 * - timeout: 请求超时时间（300 秒）
 * - 错误拦截器：统一处理错误并显示提示
 */

import axios from 'axios'
import { ElMessage } from 'element-plus'

// 创建 axios 实例
const request = axios.create({
  baseURL: '/api',      // API 基础路径，所有请求会自动添加此前缀
  timeout: 300000,      // 超时时间：300 秒（5 分钟），适用于大文件上传和长时间推理
})

// 响应拦截器：统一处理错误
request.interceptors.response.use(
  (response) => response,  // 成功响应直接返回
  (error) => {
    // 提取错误信息
    const msg = error.response?.data?.detail || error.message || '请求失败'
    // 显示错误提示
    ElMessage.error(msg)
    // 继续抛出错误，让调用方可以捕获
    return Promise.reject(error)
  }
)

export default request
