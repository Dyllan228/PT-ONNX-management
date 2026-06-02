/**
 * 路由配置模块
 *
 * 本模块定义了前端应用的所有路由规则
 *
 * 技术栈：
 * - Vue Router 4: Vue 3 官方路由管理器
 * - History Mode: 使用 HTML5 History API（无 # 号）
 *
 * 路由列表：
 * - /models     - 模型管理（默认页面）
 * - /convert    - 模型转换
 * - /inference  - 推理可视化
 * - /benchmark  - 性能对比
 * - /datasets   - 数据集管理
 * - /versions   - 版本管理
 *
 * 特性：
 * - 懒加载：使用动态 import() 实现路由懒加载
 * - 代码分割：每个页面独立打包，减小初始加载体积
 */

import { createRouter, createWebHistory } from 'vue-router'

/**
 * 路由配置数组
 *
 * 每个路由对象包含：
 * - path: URL 路径
 * - name: 路由名称（用于编程式导航）
 * - component: 对应的页面组件（懒加载）
 */
const routes = [
  // 根路径重定向到模型管理页面
  { path: '/', redirect: '/models' },

  // 模型管理页面
  {
    path: '/models',
    name: 'ModelManager',
    component: () => import('../views/ModelManager.vue'),
  },

  // 模型转换页面
  {
    path: '/convert',
    name: 'ModelConvert',
    component: () => import('../views/ModelConvert.vue'),
  },

  // 推理可视化页面
  {
    path: '/inference',
    name: 'InferenceVisual',
    component: () => import('../views/InferenceVisual.vue'),
  },

  // 性能对比页面
  {
    path: '/benchmark',
    name: 'PerformanceCompare',
    component: () => import('../views/PerformanceCompare.vue'),
  },

  // 数据集管理页面
  {
    path: '/datasets',
    name: 'DatasetManager',
    component: () => import('../views/DatasetManager.vue'),
  },

  // 版本管理页面
  {
    path: '/versions',
    name: 'VersionManage',
    component: () => import('../views/VersionManage.vue'),
  },
]

/**
 * 创建路由实例
 *
 * history: createWebHistory() - 使用 HTML5 History 模式
 * - URL 格式：http://localhost:5173/models
 * - 需要服务器配置支持（所有路由返回 index.html）
 */
const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
