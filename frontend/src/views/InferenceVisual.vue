<template>
  <div>
    <h2>推理可视化</h2>
    <el-card style="max-width: 700px; margin-bottom: 20px;">
      <el-form :model="form" label-width="100px">
        <el-form-item label="选择模型">
          <el-select v-model="form.model_id" placeholder="选择模型" style="width: 100%;"
                     @change="onModelChange">
            <el-option
              v-for="m in store.models"
              :key="m.id"
              :label="`${m.name} (${m.version})`"
              :value="m.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="模型类型">
          <el-radio-group v-model="form.model_type">
            <el-radio value="pt" :disabled="!selectedModel">PT</el-radio>
            <el-radio value="onnx" :disabled="!selectedModel?.onnx_converted">ONNX</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="硬件">
          <el-select v-model="form.device" style="width: 200px;">
            <el-option label="CPU" value="cpu" />
            <el-option label="GPU (CUDA)" value="cuda" />
          </el-select>
        </el-form-item>
        <el-form-item label="置信度阈值">
          <el-slider v-model="form.confidence_threshold" :min="0.1" :max="1.0" :step="0.05"
                     :format-tooltip="(v) => (v * 100).toFixed(0) + '%'" style="width: 300px;" />
        </el-form-item>
        <el-form-item label="数据源">
          <el-tabs v-model="dataSourceType">
            <el-tab-pane label="选择已有" name="existing">
              <el-select v-model="form.dataset_path" placeholder="选择数据源" style="width: 100%;">
                <el-option
                  v-for="d in datasets"
                  :key="d.id"
                  :label="`${d.name} (${d.type}, ${d.size_mb}MB)`"
                  :value="d.path"
                />
              </el-select>
            </el-tab-pane>
            <el-tab-pane label="上传新文件" name="upload">
              <FileUploader accept=".jpg,.jpeg,.png,.mp4,.avi" @file-change="(f) => uploadFile = f" />
            </el-tab-pane>
          </el-tabs>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="running" @click="handleInfer">开始推理</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card v-if="currentTask" style="margin-bottom: 20px;">
      <TaskProgress :task="currentTask" @reset="currentTask = null" />
    </el-card>

    <el-row :gutter="20" v-if="resultData">
      <el-col :span="12">
        <el-card>
          <h3>检测结果</h3>
          <ResultImage :imageUrl="currentImageUrl" :detections="currentDetections" />
          <div v-if="isVideo" style="margin-top: 10px;">
            <el-slider v-model="currentFrame" :min="0" :max="resultData.total_frames - 1"
                       @change="onFrameChange" />
            <span>帧 {{ currentFrame }} / {{ resultData.total_frames - 1 }}</span>
          </div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <h3>推理信息</h3>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="模型类型">{{ resultData.model_type?.toUpperCase() }}</el-descriptions-item>
            <el-descriptions-item label="设备">{{ resultData.device }}</el-descriptions-item>
            <el-descriptions-item label="总帧数">{{ resultData.total_frames }}</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useModelStore } from '../stores/models'
import { createInferenceTask, getInferenceTask, getResultImage } from '../api/inference'
import { getDatasets } from '../api/datasets'
import TaskProgress from '../components/TaskProgress.vue'
import ResultImage from '../components/ResultImage.vue'
import FileUploader from '../components/FileUploader.vue'

const store = useModelStore()
const datasets = ref([])
const dataSourceType = ref('existing')
const uploadFile = ref(null)
const form = ref({
  model_id: null, model_type: 'pt', device: 'cpu',
  confidence_threshold: 0.5, dataset_path: null,
})
const running = ref(false)
const currentTask = ref(null)
const resultData = ref(null)
const currentFrame = ref(0)

const selectedModel = computed(() => store.models.find(m => m.id === form.value.model_id))
const isVideo = computed(() => resultData.value?.total_frames > 1)
const currentImageUrl = computed(() => {
  if (!currentTask.value?.task_id) return null
  return getResultImage(currentTask.value.task_id, currentFrame.value)
})
const currentDetections = computed(() => {
  if (!resultData.value?.detections_summary) return []
  const frame = resultData.value.detections_summary.find(d => d.frame === currentFrame.value)
  return frame?.detections || []
})

onMounted(async () => {
  await store.fetchModels()
  try {
    const res = await getDatasets()
    datasets.value = res.data
  } catch (e) { /* ignore */ }
  if (store.models.length) form.value.model_id = store.models[0].id
  if (datasets.value.length) form.value.dataset_path = datasets.value[0].path
})

function onModelChange(id) {
  const m = store.models.find(m => m.id === id)
  if (m) form.value.model_type = m.onnx_converted ? 'onnx' : 'pt'
}

async function handleInfer() {
  if (!form.value.model_id) { ElMessage.warning('请选择模型'); return }

  const hasFile = uploadFile.value
  const hasDataset = form.value.dataset_path
  if (!hasFile && !hasDataset) { ElMessage.warning('请选择或上传数据源'); return }

  running.value = true
  try {
    const formData = new FormData()
    formData.append('model_id', form.value.model_id)
    formData.append('model_type', form.value.model_type)
    formData.append('device', form.value.device)
    formData.append('confidence_threshold', form.value.confidence_threshold)

    if (hasFile) {
      formData.append('file', uploadFile.value)
    } else {
      const blob = await fetch(form.value.dataset_path).then(r => r.blob())
      const ext = form.value.dataset_path.split('.').pop()
      formData.append('file', new File([blob], `data.${ext}`))
    }

    const res = await createInferenceTask(formData)
    const taskId = res.data.task_id
    currentTask.value = { task_id: taskId, status: 'running', progress: 0 }

    const timer = setInterval(async () => {
      const statusRes = await getInferenceTask(taskId)
      currentTask.value = { ...statusRes.data, task_id: taskId }
      if (statusRes.data.status === 'completed' || statusRes.data.status === 'failed') {
        clearInterval(timer)
        running.value = false
        if (statusRes.data.status === 'completed') {
          resultData.value = statusRes.data.result
          currentFrame.value = 0
          ElMessage.success('推理完成')
        } else {
          ElMessage.error('推理失败: ' + statusRes.data.error_msg)
        }
      }
    }, 1500)
  } catch (e) {
    running.value = false
  }
}

function onFrameChange(val) {
  currentFrame.value = val
}
</script>
