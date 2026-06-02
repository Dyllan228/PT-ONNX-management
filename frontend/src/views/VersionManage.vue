<!--
  版本管理页面

  功能：
  - 按模型名称分组展示版本
  - 折叠面板展开/收起
  - 双击编辑描述
  - 显示模型元信息（参数量、大小、类别）
  - 跳转到性能对比
  - 删除模型版本

  使用的技术：
  - Element Plus: Collapse、Table、Tag、Descriptions 等组件
  - Vue 3 Composition API: ref、computed、onMounted
  - Pinia: 模型状态管理
-->

<template>
  <div>
    <h2>版本管理</h2>

    <el-collapse v-model="expandedNames">
      <el-collapse-item
        v-for="(versions, name) in groupedModels"
        :key="name"
        :title="`${name} (${versions.length} 个版本)`"
        :name="name"
      >
        <el-table :data="versions" stripe size="small">
          <el-table-column prop="version" label="版本" width="100" />
          <el-table-column label="状态" width="120">
            <template #default="{ row }">
              <el-tag :type="row.onnx_converted ? 'success' : 'info'" size="small">
                {{ row.onnx_converted ? 'PT + ONNX' : '仅 PT' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="描述 (双击编辑)" min-width="200">
            <template #default="{ row }">
              <div v-if="editingId !== row.id" @dblclick="startEdit(row)"
                   style="cursor: pointer; min-height: 20px;" :title="'双击编辑'">
                {{ row.description || '(双击添加描述)' }}
              </div>
              <div v-else style="display: flex; gap: 6px;">
                <el-input v-model="editDesc" size="small" @keyup.enter="saveDesc(row)"
                          @keyup.escape="cancelEdit" autofocus />
                <el-button size="small" type="primary" @click="saveDesc(row)">保存</el-button>
                <el-button size="small" @click="cancelEdit">取消</el-button>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="参数量" width="100">
            <template #default="{ row }">
              {{ row.param_count ? formatParamCount(row.param_count) : '-' }}
            </template>
          </el-table-column>
          <el-table-column label="PT 大小" width="90">
            <template #default="{ row }">
              {{ row.pt_file_size ? (row.pt_file_size / 1024 / 1024).toFixed(1) + ' MB' : '-' }}
            </template>
          </el-table-column>
          <el-table-column label="ONNX 大小" width="100">
            <template #default="{ row }">
              {{ row.onnx_file_size ? (row.onnx_file_size / 1024 / 1024).toFixed(1) + ' MB' : '-' }}
            </template>
          </el-table-column>
          <el-table-column label="类别" width="150">
            <template #default="{ row }">
              <el-tag v-for="c in (row.class_names || []).slice(0, 3)" :key="c" size="small" style="margin-right: 3px;">
                {{ c }}
              </el-tag>
              <el-tag v-if="row.class_names?.length > 3" size="small" type="info">
                +{{ row.class_names.length - 3 }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="创建时间" width="160">
            <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="160">
            <template #default="{ row }">
              <el-button size="small" @click="goToCompare">对比</el-button>
              <el-popconfirm title="确定删除？" @confirm="handleDelete(row.id)">
                <template #reference>
                  <el-button size="small" type="danger">删除</el-button>
                </template>
              </el-popconfirm>
            </template>
          </el-table-column>
        </el-table>
      </el-collapse-item>
    </el-collapse>

    <el-empty v-if="!Object.keys(groupedModels).length" description="暂无模型" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useModelStore } from '../stores/models'
import { deleteModel, updateModel, getModels } from '../api/models'

const store = useModelStore()
const router = useRouter()
const expandedNames = ref([])
const editingId = ref(null)
const editDesc = ref('')

const groupedModels = computed(() => {
  const groups = {}
  for (const m of store.models) {
    if (!groups[m.name]) groups[m.name] = []
    groups[m.name].push(m)
  }
  return groups
})

onMounted(async () => {
  await store.fetchModels()
  expandedNames.value = Object.keys(groupedModels.value)
})

function formatParamCount(count) {
  if (count > 1_000_000) return (count / 1_000_000).toFixed(1) + 'M'
  return (count / 1_000).toFixed(1) + 'K'
}

function formatDate(dateStr) {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

function startEdit(row) {
  editingId.value = row.id
  editDesc.value = row.description || ''
}

function cancelEdit() {
  editingId.value = null
  editDesc.value = ''
}

async function saveDesc(row) {
  try {
    await updateModel(row.id, { description: editDesc.value })
    row.description = editDesc.value
    ElMessage.success('描述已更新')
  } catch (e) {
    ElMessage.error('更新失败')
  }
  editingId.value = null
}

function goToCompare() {
  router.push('/benchmark')
}

async function handleDelete(id) {
  await deleteModel(id)
  ElMessage.success('删除成功')
  store.fetchModels()
}
</script>
