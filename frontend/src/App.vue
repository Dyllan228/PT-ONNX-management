<template>
  <el-container style="height: 100vh">
    <el-header style="display: flex; align-items: center; background: #409EFF; color: white; padding: 0 20px;">
      <h2 style="margin: 0; font-size: 18px;">PT-ONNX 可视化对比工具 v2.0</h2>
    </el-header>
    <el-container>
      <el-aside width="180px" style="background: #f5f7fa;">
        <el-menu :default-active="activeMenu" router style="border-right: none; margin-top: 10px;">
          <el-menu-item index="/models">
            <el-icon><Folder /></el-icon>
            <span>模型管理</span>
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
      <el-main style="padding: 20px;">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const activeMenu = computed(() => route.path)
</script>
