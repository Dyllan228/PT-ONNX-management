<!--
  应用根组件

  功能：
  - 定义整体布局结构
  - 顶部导航栏
  - 左侧菜单栏
  - 主内容区域

  布局结构：
  ┌─────────────────────────────────┐
  │         顶部导航栏              │
  ├──────────┬──────────────────────┤
  │          │                      │
  │  左侧    │      主内容区        │
  │  菜单    │    (router-view)     │
  │          │                      │
  └──────────┴──────────────────────┘

  技术栈：
  - Element Plus: 布局组件（Container、Header、Aside、Main、Menu）
  - Vue Router: 路由管理
-->

<template>
  <el-container style="height: 100vh">
    <!-- 顶部导航栏 -->
    <el-header style="display: flex; align-items: center; background: #409EFF; color: white; padding: 0 20px;">
      <h2 style="margin: 0; font-size: 18px;">人工智能视觉模型管理平台</h2>
    </el-header>

    <el-container>
      <!-- 左侧菜单栏 -->
      <el-aside width="180px" style="background: #f5f7fa;">
        <!--
          el-menu 组件：
          - :default-active="activeMenu" - 高亮当前菜单项
          - router - 启用路由模式，点击菜单项会导航到对应路由
        -->
        <el-menu :default-active="activeMenu" router style="border-right: none; margin-top: 10px;">
          <el-menu-item index="/models">
            <el-icon><Folder /></el-icon>
            <span>模型管理</span>
          </el-menu-item>
          <el-menu-item index="/datasets">
            <el-icon><Files /></el-icon>
            <span>数据集管理</span>
          </el-menu-item>
          <el-menu-item index="/convert">
            <el-icon><Switch /></el-icon>
            <span>模型转换</span>
          </el-menu-item>
          <el-menu-item index="/inference">
            <el-icon><View /></el-icon>
            <span>推理可视化</span>
          </el-menu-item>
          <el-menu-item index="/benchmark">
            <el-icon><DataAnalysis /></el-icon>
            <span>性能对比</span>
          </el-menu-item>
          <el-menu-item index="/versions">
            <el-icon><List /></el-icon>
            <span>版本管理</span>
          </el-menu-item>
        </el-menu>
      </el-aside>

      <!-- 主内容区域 -->
      <el-main style="padding: 20px;">
        <!-- router-view: 路由出口，显示当前路由对应的组件 -->
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

// 获取当前路由对象
const route = useRoute()

/**
 * 当前激活的菜单项
 * 根据当前路由路径自动高亮对应菜单
 */
const activeMenu = computed(() => route.path)
</script>
