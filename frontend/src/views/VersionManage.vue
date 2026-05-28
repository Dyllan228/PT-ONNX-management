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
        <el-table :data="versions" stripe>
          <el-table-column prop="version" label="版本" width="120" />
          <el-table-column label="状态" width="150">
            <template #default="{ row }">
              <el-tag :type="row.onnx_converted ? 'success' : 'info'" size="small">
                {{ row.onnx_converted ? 'PT + ONNX' : '仅 PT' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="description" label="描述" show-overflow-tooltip />
          <el-table-column label="参数量" width="120">
            <template #default="{ row }">
              {{ row.param_count ? formatParamCount(row.param_count) : '-' }}
            </template>
          </el-table-column>
          <el-table-column label="PT 大小" width="100">
            <template #default="{ row }">
              {{ row.pt_file_size ? (row.pt_file_size / 1024 / 1024).toFixed(1) + ' MB' : '-' }}
            </template>
          </el-table-column>
          <el-table-column label="ONNX 大小" width="110">
            <template #default="{ row }">
              {{ row.onnx_file_size ? (row.onnx_file_size / 1024 / 1024).toFixed(1) + ' MB' : '-' }}
            </template>
          </el-table-column>
          <el-table-column label="训练轮数" width="100">
            <template #default="{ row }">{{ row.training_epochs || '-' }}</template>
          </el-table-column>
          <el-table-column label="创建时间" width="180">
            <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="200">
            <template #default="{ row }">
              <el-button size="small" @click="goToCompare(name)">对比</el-button>
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
import { deleteModel } from '../api/models'

const store = useModelStore()
const router = useRouter()
const expandedNames = ref([])

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

function goToCompare() {
  router.push('/benchmark')
}

async function handleDelete(id) {
  await deleteModel(id)
  ElMessage.success('删除成功')
  store.fetchModels()
}
</script>
