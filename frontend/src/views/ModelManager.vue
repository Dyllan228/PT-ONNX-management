<!--
  模型管理页面

  功能：
  - 模型列表展示（分页）
  - 上传 PT 模型
  - 编辑模型信息
  - 删除模型（单个/批量）
  - 扫描并注册新模型

  使用的技术：
  - Element Plus: Table、Dialog、Form、Pagination 等组件
  - Vue 3 Composition API: ref、computed、onMounted
  - Pinia: 状态管理（通过 API 直接调用）
-->

<template>
  <div>
    <!-- 页面标题和操作按钮 -->
    <el-row :gutter="20" style="margin-bottom: 20px;">
      <el-col :span="12"><h2 style="margin: 0;">模型管理</h2></el-col>
      <el-col :span="12" style="text-align: right;">
        <el-button type="primary" @click="showUploadDialog = true">
          <el-icon><Plus /></el-icon> 上传模型
        </el-button>
        <el-button @click="handleScan">
          <el-icon><Refresh /></el-icon> 重新扫描
        </el-button>
        <el-popconfirm v-if="selectedIds.length" :title="`确定删除选中的 ${selectedIds.length} 个模型？`"
                       @confirm="handleBatchDelete">
          <template #reference>
            <el-button type="danger">批量删除 ({{ selectedIds.length }})</el-button>
          </template>
        </el-popconfirm>
      </el-col>
    </el-row>

    <!-- 模型列表表格 -->
    <el-table :data="pagedData" v-loading="loading" stripe @selection-change="onSelectionChange">
      <el-table-column type="selection" width="45" />
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="name" label="模型名称" />
      <el-table-column prop="version" label="版本" width="100" />
      <el-table-column label="状态" width="120">
        <template #default="{ row }">
          <el-tag :type="row.onnx_converted ? 'success' : 'info'" size="small">
            {{ row.onnx_converted ? '已转换 ONNX' : '仅 PT' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="description" label="描述" show-overflow-tooltip />
      <el-table-column label="PT 大小" width="100">
        <template #default="{ row }">
          {{ row.pt_file_size ? (row.pt_file_size / 1024 / 1024).toFixed(1) + ' MB' : '-' }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="160">
        <template #default="{ row }">
          <el-button size="small" @click="handleEdit(row)">编辑</el-button>
          <el-popconfirm title="确定删除？" @confirm="handleDelete(row.id)">
            <template #reference>
              <el-button size="small" type="danger">删除</el-button>
            </template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页器 -->
    <el-pagination v-if="tableData.length > pageSize"
                   style="margin-top: 16px; justify-content: center;"
                   layout="total, prev, pager, next, sizes"
                   :total="tableData.length"
                   v-model:current-page="currentPage"
                   v-model:page-size="pageSize"
                   :page-sizes="[10, 20, 50, 100]" />

    <!-- 上传对话框 -->
    <el-dialog v-model="showUploadDialog" title="上传 PT 模型" width="500px">
      <el-form :model="uploadForm" label-width="80px">
        <el-form-item label="模型名称">
          <el-input v-model="uploadForm.name" placeholder="如 helmet-vest" />
        </el-form-item>
        <el-form-item label="版本">
          <el-input v-model="uploadForm.version" placeholder="如 v1" />
        </el-form-item>
        <el-form-item label="模型文件">
          <FileUploader accept=".pt" @file-change="(f) => uploadForm.file = f" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showUploadDialog = false">取消</el-button>
        <el-button type="primary" :loading="uploading" @click="handleUpload">上传</el-button>
      </template>
    </el-dialog>

    <!-- 编辑对话框 -->
    <el-dialog v-model="showEditDialog" title="编辑模型信息" width="500px">
      <el-form :model="editForm" label-width="100px">
        <el-form-item label="模型名称"><el-input v-model="editForm.name" /></el-form-item>
        <el-form-item label="版本"><el-input v-model="editForm.version" /></el-form-item>
        <el-form-item label="训练轮数"><el-input-number v-model="editForm.training_epochs" :min="0" /></el-form-item>
        <el-form-item label="训练数据量"><el-input-number v-model="editForm.training_samples" :min="0" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSaveEdit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
/**
 * 模型管理页面逻辑
 *
 * 功能：
 * - 加载模型列表
 * - 上传模型
 * - 编辑模型信息
 * - 删除模型（单个/批量）
 * - 扫描并注册新模型
 */

import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getModels, uploadModel, updateModel, deleteModel, scanModels } from '../api/models'
import FileUploader from '../components/FileUploader.vue'

// ===== 状态 =====
const tableData = ref([])          // 模型列表数据
const loading = ref(false)         // 加载状态
const selectedIds = ref([])        // 选中的模型 ID
const currentPage = ref(1)         // 当前页码
const pageSize = ref(20)           // 每页数量

// 分页数据
const pagedData = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return tableData.value.slice(start, start + pageSize.value)
})

// 对话框状态
const showUploadDialog = ref(false)  // 上传对话框
const showEditDialog = ref(false)    // 编辑对话框
const uploading = ref(false)         // 上传中状态

// 表单数据
const uploadForm = ref({ name: '', version: 'v1', file: null })
const editForm = ref({ id: null, name: '', version: '', training_epochs: null, training_samples: null })

// ===== 生命周期 =====
onMounted(() => loadData())

// ===== 方法 =====

/**
 * 加载模型列表
 */
async function loadData() {
  loading.value = true
  try { tableData.value = (await getModels()).data } catch (e) { /* ignore */ }
  loading.value = false
}

/**
 * 处理表格选择变化
 * @param {Array} rows - 选中的行
 */
function onSelectionChange(rows) {
  selectedIds.value = rows.map(r => r.id)
}

/**
 * 处理模型上传
 */
async function handleUpload() {
  if (!uploadForm.value.file || !uploadForm.value.name) {
    ElMessage.warning('请填写名称并选择文件')
    return
  }
  uploading.value = true
  try {
    const fd = new FormData()
    fd.append('file', uploadForm.value.file)
    fd.append('name', uploadForm.value.name)
    fd.append('version', uploadForm.value.version)
    await uploadModel(fd)
    ElMessage.success('上传成功')
    showUploadDialog.value = false
    uploadForm.value = { name: '', version: 'v1', file: null }
    await loadData()
  } catch (e) {
    ElMessage.error('上传失败: ' + (e.response?.data?.detail || e.message))
  }
  uploading.value = false
}

/**
 * 打开编辑对话框
 * @param {object} row - 模型数据
 */
function handleEdit(row) {
  editForm.value = { ...row }
  showEditDialog.value = true
}

/**
 * 保存编辑
 */
async function handleSaveEdit() {
  await updateModel(editForm.value.id, editForm.value)
  ElMessage.success('更新成功')
  showEditDialog.value = false
  await loadData()
}

/**
 * 删除单个模型
 * @param {number} id - 模型 ID
 */
async function handleDelete(id) {
  await deleteModel(id)
  ElMessage.success('删除成功')
  await loadData()
}

/**
 * 批量删除模型
 */
async function handleBatchDelete() {
  for (const id of selectedIds.value) {
    try { await deleteModel(id) } catch (e) { /* skip */ }
  }
  ElMessage.success(`已删除 ${selectedIds.value.length} 个模型`)
  selectedIds.value = []
  await loadData()
}

/**
 * 扫描并注册新模型
 */
async function handleScan() {
  const res = await scanModels()
  ElMessage.success(`扫描完成，新增 ${res.data.scanned} 个模型`)
  await loadData()
}
</script>
