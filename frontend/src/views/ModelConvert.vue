<!--
  模型转换页面

  功能：
  - 选择 PT 模型
  - 配置转换参数（输入尺寸、Opset 版本、动态 Batch）
  - 执行 PT → ONNX 转换
  - 显示转换进度
  - 下载 PT/ONNX 模型文件

  使用的技术：
  - Element Plus: Card、Form、Select、Switch、Progress 等组件
  - Vue 3 Composition API: ref、computed、onMounted
  - Pinia: 模型状态管理
  - 轮询机制: 定时查询转换进度
-->

<template>
  <div>
    <h2>模型转换</h2>

    <!-- 转换配置 -->
    <el-card style="margin-bottom: 20px;">
      <el-row :gutter="20">
        <el-col :span="12">
          <el-form :model="form" label-width="100px">
            <el-form-item label="选择模型">
              <el-select v-model="form.model_id" placeholder="选择 PT 模型" style="width: 100%;">
                <el-option v-for="m in store.models" :key="m.id"
                           :label="`${m.name} (${m.version})${m.onnx_converted ? ' [已转换]' : ''}`"
                           :value="m.id" />
              </el-select>
            </el-form-item>
            <el-form-item label="输入尺寸">
              <el-input v-model="form.inputSizeStr" placeholder="640,640" style="width: 200px;" />
              <div class="form-tip">模型输入的宽高，格式为 "宽,高"，需为32的倍数</div>
            </el-form-item>
            <el-form-item label="ONNX Opset">
              <el-input-number v-model="form.opset_version" :min="9" :max="17" />
              <div class="form-tip">
                ONNX 算子集版本，决定导出模型的算子兼容性。推荐 11-13，兼容性好；
                较高版本支持更多优化但要求运行时版本更新
              </div>
            </el-form-item>
            <el-form-item label="动态 Batch">
              <el-switch v-model="form.dynamic_batch" />
              <div class="form-tip">
                开启后 ONNX 模型支持可变 batch_size 输入（如 1, 4, 8），
                关闭则固定 batch_size=1，推理速度更稳定
              </div>
            </el-form-item>
            <el-form-item label="简化模型">
              <el-switch v-model="form.simplify" />
              <div class="form-tip">
                使用 onnxsim 工具优化计算图，移除冗余节点，减小模型体积并提升推理速度。
                需要安装 onnxsim 依赖
              </div>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="converting" @click="handleConvert"
                         :disabled="!form.model_id || converting">
                开始转换
              </el-button>
            </el-form-item>
          </el-form>
        </el-col>
        <el-col :span="12">
          <div v-if="selectedModel" style="padding-top: 10px;">
            <el-descriptions :column="1" border size="small">
              <el-descriptions-item label="模型">{{ selectedModel.name }} {{ selectedModel.version }}</el-descriptions-item>
              <el-descriptions-item label="参数量">
                {{ selectedModel.param_count ? formatParam(selectedModel.param_count) : '-' }}
              </el-descriptions-item>
              <el-descriptions-item label="类别">
                {{ selectedModel.class_names?.join(', ') || '-' }}
              </el-descriptions-item>
              <el-descriptions-item label="PT 大小">
                {{ selectedModel.pt_file_size ? (selectedModel.pt_file_size / 1024 / 1024).toFixed(1) + ' MB' : '-' }}
              </el-descriptions-item>
              <el-descriptions-item label="ONNX 大小">
                {{ selectedModel.onnx_file_size ? (selectedModel.onnx_file_size / 1024 / 1024).toFixed(1) + ' MB' : '-' }}
              </el-descriptions-item>
              <el-descriptions-item label="ONNX 状态">
                <el-tag :type="selectedModel.onnx_converted ? 'success' : 'info'" size="small">
                  {{ selectedModel.onnx_converted ? '已转换' : '未转换' }}
                </el-tag>
              </el-descriptions-item>
            </el-descriptions>
            <div style="margin-top: 12px;">
              <el-button size="small" @click="downloadModel(selectedModel.id, 'pt')">
                下载 PT 模型
              </el-button>
              <el-button size="small" type="success" :disabled="!selectedModel.onnx_converted"
                         @click="downloadModel(selectedModel.id, 'onnx')">
                下载 ONNX 模型
              </el-button>
            </div>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <!-- 转换进度 -->
    <el-card v-if="currentTask" style="margin-bottom: 20px;">
      <template #header>转换进度</template>
      <TaskProgress :task="currentTask" :progress-message="progressMsg" @reset="currentTask = null" />
    </el-card>

    <!-- 模型列表 -->
    <el-card>
      <template #header>全部模型</template>
      <el-table :data="store.models" stripe size="small">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="name" label="名称" />
        <el-table-column prop="version" label="版本" width="80" />
        <el-table-column label="PT 大小" width="90">
          <template #default="{ row }">
            {{ row.pt_file_size ? (row.pt_file_size / 1024 / 1024).toFixed(1) + ' MB' : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="ONNX" width="90">
          <template #default="{ row }">
            <template v-if="row.onnx_converted">
              {{ row.onnx_file_size ? (row.onnx_file_size / 1024 / 1024).toFixed(1) + ' MB' : '-' }}
            </template>
            <span v-else style="color: #909399;">-</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.onnx_converted ? 'success' : 'info'" size="small">
              {{ row.onnx_converted ? '已转换' : '未转换' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button size="small" @click="downloadModel(row.id, 'pt')">下载PT</el-button>
            <el-button size="small" type="success" :disabled="!row.onnx_converted"
                       @click="downloadModel(row.id, 'onnx')">下载ONNX</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useModelStore } from '../stores/models'
import { createConvertTask, getConvertTask } from '../api/convert'
import { getModelDownloadUrl } from '../api/models'
import TaskProgress from '../components/TaskProgress.vue'

const store = useModelStore()
const form = ref({
  model_id: null, inputSizeStr: '640,640', opset_version: 11, dynamic_batch: true, simplify: false,
})
const converting = ref(false)
const currentTask = ref(null)
const progressMsg = ref('')

const selectedModel = computed(() => store.models.find(m => m.id === form.value.model_id))

onMounted(() => store.fetchModels())

function formatParam(count) {
  if (count > 1_000_000) return (count / 1_000_000).toFixed(1) + 'M'
  return (count / 1_000).toFixed(1) + 'K'
}

async function handleConvert() {
  if (!form.value.model_id) { ElMessage.warning('请选择模型'); return }
  converting.value = true
  progressMsg.value = ''
  try {
    const inputSize = form.value.inputSizeStr.split(',').map(Number)
    const res = await createConvertTask({
      model_id: form.value.model_id,
      input_size: inputSize,
      dynamic_batch: form.value.dynamic_batch,
      opset_version: form.value.opset_version,
    })
    currentTask.value = { status: 'running', progress: 0 }

    const timer = setInterval(async () => {
      const statusRes = await getConvertTask(res.data.task_id)
      currentTask.value = statusRes.data
      if (statusRes.data.result?._progress_msg) {
        progressMsg.value = statusRes.data.result._progress_msg
      }
      if (statusRes.data.status === 'completed' || statusRes.data.status === 'failed') {
        clearInterval(timer)
        converting.value = false
        if (statusRes.data.status === 'completed') {
          ElMessage.success('转换完成')
          progressMsg.value = '转换完成'
          store.fetchModels()
        } else {
          ElMessage.error('转换失败: ' + (statusRes.data.error_msg || ''))
          progressMsg.value = statusRes.data.error_msg || '转换失败'
        }
      }
    }, 1500)
  } catch (e) {
    converting.value = false
    ElMessage.error('创建任务失败: ' + (e.response?.data?.detail || e.message))
  }
}

function downloadModel(modelId, type) {
  const a = document.createElement('a')
  a.href = getModelDownloadUrl(modelId, type)
  a.download = ''
  a.click()
}
</script>

<style scoped>
.form-tip {
  color: #909399;
  font-size: 12px;
  line-height: 1.5;
  margin-top: 4px;
}
</style>
