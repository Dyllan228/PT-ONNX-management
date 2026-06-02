<!--
  数据集管理页面

  功能：
  - 数据集列表展示（卡片布局）
  - 导入 YOLO 格式数据集（ZIP）
  - 编辑数据集信息
  - 下载数据集
  - 删除数据集
  - 显示类别分布统计

  使用的技术：
  - Element Plus: Card、Dialog、Form、Table、Progress 等组件
  - Vue 3 Composition API: ref、onMounted
  - 数据集分析: 自动统计图片数、标注数、类别分布
-->

<template>
  <div>
    <el-card shadow="never" style="margin-bottom: 20px;">
      <el-row :gutter="20" align="middle">
        <el-col :span="12"><h2 style="margin: 0;">数据集管理</h2></el-col>
        <el-col :span="12" style="text-align: right;">
          <el-button type="primary" @click="showImportDialog = true">
            <el-icon><UploadFilled /></el-icon> 导入数据集
          </el-button>
        </el-col>
      </el-row>
    </el-card>

    <!-- 数据集卡片列表 -->
    <el-row :gutter="16" v-loading="loading">
      <el-col :span="8" v-for="ds in datasets" :key="ds.id" style="margin-bottom: 16px;">
        <el-card shadow="hover" style="height: 100%;">
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <span style="font-weight: bold; font-size: 15px;">{{ ds.name }}</span>
              <div>
                <el-button size="small" @click="handleEdit(ds)">编辑</el-button>
                <el-button size="small" type="success" @click="handleDownload(ds)">下载</el-button>
                <el-popconfirm title="确定删除？" @confirm="handleDelete(ds.id)">
                  <template #reference><el-button size="small" type="danger">删除</el-button></template>
                </el-popconfirm>
              </div>
            </div>
          </template>
          <div v-if="ds.description" style="color: #666; font-size: 13px; margin-bottom: 12px;">
            {{ ds.description }}
          </div>
          <el-descriptions :column="2" size="small" border>
            <el-descriptions-item label="图片数">{{ ds.image_count }}</el-descriptions-item>
            <el-descriptions-item label="已标注">{{ ds.label_count }}</el-descriptions-item>
            <el-descriptions-item label="目标数">{{ totalObjects(ds) }}</el-descriptions-item>
            <el-descriptions-item label="大小">{{ formatSize(ds.file_size) }}</el-descriptions-item>
          </el-descriptions>
          <div v-if="ds.class_names?.length" style="margin-top: 12px;">
            <span style="color: #909399; font-size: 12px;">类别：</span>
            <el-tag v-for="c in ds.class_names" :key="c" size="small" style="margin: 2px 4px 2px 0;">
              {{ c }}{{ ds.class_distribution?.[c] ? ` (${ds.class_distribution[c]})` : '' }}
            </el-tag>
          </div>
          <div v-if="ds.class_distribution" style="margin-top: 10px;">
            <div v-for="(count, name) in topClasses(ds)" :key="name"
                 style="display: flex; align-items: center; margin-bottom: 4px; font-size: 12px;">
              <span style="width: 80px; color: #666;">{{ name }}</span>
              <el-progress :percentage="pct(count, ds)" :stroke-width="12" :show-text="false" style="flex: 1;" />
              <span style="width: 50px; text-align: right; color: #909399;">{{ count }}</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    <el-empty v-if="!loading && !datasets.length" description="暂无数据集，请导入" />

    <!-- 导入对话框 -->
    <el-dialog v-model="showImportDialog" title="导入数据集" width="550px">
      <el-alert title="支持 YOLO 格式 ZIP 包（images/ + labels/ 目录，含 classes.txt）"
                type="info" :closable="false" style="margin-bottom: 16px;" />
      <el-form :model="importForm" label-width="90px">
        <el-form-item label="名称" required>
          <el-input v-model="importForm.name" placeholder="如 helmet-vest-train" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="importForm.description" type="textarea" :rows="3"
                    placeholder="描述数据集内容、来源、用途等" />
        </el-form-item>
        <el-form-item label="ZIP 文件" required>
          <FileUploader accept=".zip" @file-change="(f) => importForm.file = f" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showImportDialog = false">取消</el-button>
        <el-button type="primary" :loading="importing" @click="handleImport">导入</el-button>
      </template>
    </el-dialog>

    <!-- 编辑对话框 -->
    <el-dialog v-model="showEditDialog" title="编辑数据集" width="500px">
      <el-form :model="editForm" label-width="80px">
        <el-form-item label="名称"><el-input v-model="editForm.name" /></el-form-item>
        <el-form-item label="描述"><el-input v-model="editForm.description" type="textarea" :rows="3" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSaveEdit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getDatasets, importDataset, updateDataset, deleteDataset, getDatasetDownloadUrl } from '../api/datasets'
import FileUploader from '../components/FileUploader.vue'

const datasets = ref([])
const loading = ref(false)
const showImportDialog = ref(false)
const showEditDialog = ref(false)
const importing = ref(false)
const importForm = ref({ name: '', description: '', file: null })
const editForm = ref({ id: null, name: '', description: '' })

onMounted(() => fetchDatasets())

async function fetchDatasets() {
  loading.value = true
  try { datasets.value = (await getDatasets()).data } catch (e) { /* ignore */ }
  loading.value = false
}

function totalObjects(ds) {
  if (ds.class_distribution) return Object.values(ds.class_distribution).reduce((a, b) => a + b, 0)
  return '-'
}

function formatSize(bytes) {
  if (!bytes) return '-'
  return (bytes / 1024 / 1024).toFixed(1) + ' MB'
}

function pct(count, ds) {
  const t = totalObjects(ds)
  return t ? Math.round(count / t * 100) : 0
}

function topClasses(ds) {
  if (!ds.class_distribution) return {}
  return Object.fromEntries(Object.entries(ds.class_distribution).slice(0, 5))
}

async function handleImport() {
  if (!importForm.value.file || !importForm.value.name) { ElMessage.warning('请填写名称并选择文件'); return }
  importing.value = true
  try {
    const fd = new FormData()
    fd.append('file', importForm.value.file)
    fd.append('name', importForm.value.name)
    fd.append('description', importForm.value.description || '')
    await importDataset(fd)
    ElMessage.success('导入成功')
    showImportDialog.value = false
    importForm.value = { name: '', description: '', file: null }
    fetchDatasets()
  } catch (e) { ElMessage.error('导入失败: ' + (e.response?.data?.detail || e.message)) }
  importing.value = false
}

function handleEdit(ds) {
  editForm.value = { id: ds.id, name: ds.name, description: ds.description || '' }
  showEditDialog.value = true
}

async function handleSaveEdit() {
  await updateDataset(editForm.value.id, { name: editForm.value.name, description: editForm.value.description })
  ElMessage.success('更新成功')
  showEditDialog.value = false
  fetchDatasets()
}

function handleDownload(ds) {
  const a = document.createElement('a')
  a.href = getDatasetDownloadUrl(ds.id)
  a.download = ds.name + '.zip'
  a.click()
}

async function handleDelete(id) {
  await deleteDataset(id)
  ElMessage.success('删除成功')
  fetchDatasets()
}
</script>
