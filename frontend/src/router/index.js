import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', redirect: '/models' },
  { path: '/models', name: 'ModelManager', component: () => import('../views/ModelManager.vue') },
  { path: '/convert', name: 'ModelConvert', component: () => import('../views/ModelConvert.vue') },
  { path: '/inference', name: 'InferenceVisual', component: () => import('../views/InferenceVisual.vue') },
  { path: '/benchmark', name: 'PerformanceCompare', component: () => import('../views/PerformanceCompare.vue') },
  { path: '/versions', name: 'VersionManage', component: () => import('../views/VersionManage.vue') },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
