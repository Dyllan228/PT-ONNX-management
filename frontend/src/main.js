/**
 * 前端应用入口文件
 *
 * 本文件负责初始化 Vue 3 应用，包括：
 * 1. 创建 Vue 应用实例
 * 2. 注册全局插件（Pinia、Router、Element Plus）
 * 3. 注册全局图标组件
 * 4. 挂载到 DOM
 *
 * 技术栈：
 * - Vue 3: 渐进式 JavaScript 框架
 * - Pinia: Vue 3 状态管理库
 * - Vue Router 4: 官方路由管理器
 * - Element Plus: Vue 3 UI 组件库
 */

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import App from './App.vue'
import router from './router'

// 创建 Vue 应用实例
const app = createApp(App)

// 创建 Pinia 状态管理实例
const pinia = createPinia()

// 注册所有 Element Plus 图标为全局组件
// 这样可以在任意组件中直接使用 <Folder />、<Files /> 等图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

// 注册插件
app.use(pinia)         // 状态管理
app.use(router)        // 路由
app.use(ElementPlus)   // UI 组件库

// 挂载到 DOM 中 id 为 app 的元素
app.mount('#app')
