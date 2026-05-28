<template>
  <div>
    <el-row :gutter="20" style="margin-bottom: 20px;">
      <el-col :span="12">
        <h2>模型管理</h2>
      </el-col>
      <el-col :span="12" style="text-align: right;">
        <el-button type="primary" @click="showUploadDialog = true">
          <el-icon><Plus /></el-icon> 上传模型
        </el-button>
        <el-button @click="handleScan">
          <el-icon><Refresh /></el-icon> 重新扫描
        </el-button>
      </el-col>
    </el-row>

    <el-table :data="models" v-loading="loading" stripe>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="name" label="模型名称" />
      <el-table-column prop="version" label="版本" width="100" />
      <el-table-column label="状态" width="120">
        <template #default="{ row }">
          <el-tag :type="row.onnx_converted ? 'success' : 'info'">
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
      <el-table-column label="操作" width="180">
        <template #default="{ row }">
          <el-button size="small" @click="handleEdit(row)">编辑</el-button>
          <el-popconfirm title="确定删除此模型？" @confirm="handleDelete(row.id)">
            <template #reference>
              <el-button size="small" type="danger">删除</el-button>
            </template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <!-- Upload Dialog -->
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

    <!-- Edit Dialog -->
    <el-dialog v-model="showEditDialog" title="编辑模型信息" width="500px">
      <el-form :model="editForm" label-width="100px">
        <el-form-item label="模型名称">
          <el-input v-model="editForm.name" />
        </el-form-item>
        <el-form-item label="版本">
          <el-input v-model="editForm.version" />
        </el-form-item>
        <el-form-item label="训练轮数">
          <el-input-number v-model="editForm.training_epochs" :min="0" />
        </el-form-item>
        <el-form-item label="训练数据量">
          <el-input-number v-model="editForm.training_samples" :min="0" />
        </el-form-item>
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
import { useModelStore } from '../stores/models'
import { uploadModel, updateModel, deleteModel, scanModels } from '../api/models'
import FileUploader from '../components/FileUploader.vue'

const store = useModelStore()
const { models, loading } = store

const showUploadDialog = ref(false)
const showEditDialog = ref(false)
const uploading = ref(false)
const uploadForm = ref({ name: '', version: 'v1', file: null })
const editForm = ref({ id: null, name: '', version: '', training_epochs: null, training_samples: null })

onMounted(() => store.fetchModels())

async function handleUpload() {
  if (!uploadForm.value.file || !uploadForm.value.name) {
    ElMessage.warning('请填写模型名称并选择文件')
    return
  }
  uploading.value = true
  try {
    const formData = new FormData()
    formData.append('file', uploadForm.value.file)
    formData.append('name', uploadForm.value.name)
    formData.append('version', uploadForm.value.version)
    await uploadModel(formData)
    ElMessage.success('上传成功')
    showUploadDialog.value = false
    uploadForm.value = { name: '', version: 'v1', file: null }
    store.fetchModels()
  } catch (e) {
    ElMessage.error('上传失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    uploading.value = false
  }
}

function handleEdit(row) {
  editForm.value = { ...row }
  showEditDialog.value = true
}

async function handleSaveEdit() {
  await updateModel(editForm.value.id, editForm.value)
  ElMessage.success('更新成功')
  showEditDialog.value = false
  store.fetchModels()
}

async function handleDelete(id) {
  await deleteModel(id)
  ElMessage.success('删除成功')
  store.fetchModels()
}

async function handleScan() {
  const res = await scanModels()
  ElMessage.success(`扫描完成，新增 ${res.data.scanned} 个模型`)
  store.fetchModels()
}
</script>
