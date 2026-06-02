<!--
  推理可视化页面

  功能：
  - 选择模型（PT/ONNX）
  - 选择推理设备（CPU/GPU）
  - 配置置信度阈值
  - 选择数据源（数据集/文件/上传）
  - 实时显示推理结果
  - 帧播放控制（播放/暂停/跳转）
  - 显示检测信息和耗时统计
  - 下载结果视频

  使用的技术：
  - Element Plus: Card、Form、Select、Slider、Table、Progress 等组件
  - Vue 3 Composition API: ref、computed、watch、onMounted
  - Pinia: 推理状态管理
  - 轮询机制: 实时加载推理结果帧
-->

<template>
  <div>
    <h2>推理可视化</h2>
    <el-row :gutter="20" style="margin-bottom: 20px;">
      <el-col :span="16">
    <el-card class="inference-form-card">
      <el-form :model="form" label-width="90px">
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
            <el-tab-pane label="数据集" name="dataset">
              <el-row :gutter="10">
                <el-col :span="16">
                  <el-select v-model="form.dataset_id" placeholder="选择数据集" style="width: 100%;"
                             popper-class="dataset-dropdown" @change="onDatasetChange">
                    <el-option v-for="d in managedDatasets" :key="d.id"
                               :label="`${d.name} (${d.image_count}张)`" :value="d.id" />
                  </el-select>
                </el-col>
                <el-col :span="8">
                  <el-select v-model="form.dataset_split" placeholder="子集" style="width: 100%;">
                    <el-option v-for="s in datasetSplits" :key="s.name"
                               :label="`${s.name} (${s.image_count})`" :value="s.name" />
                  </el-select>
                </el-col>
              </el-row>
            </el-tab-pane>
            <el-tab-pane label="数据源文件" name="existing">
              <el-select v-model="form.dataset_path" placeholder="选择数据源" style="width: 100%;"
                         popper-class="dataset-dropdown">
                <el-option v-for="d in dataSources" :key="d.id"
                           :label="`${d.name} (${d.type}, ${d.size_mb}MB)`" :value="d.path" />
              </el-select>
            </el-tab-pane>
            <el-tab-pane label="上传文件" name="upload">
              <FileUploader accept=".jpg,.jpeg,.png,.mp4,.avi" @file-change="(f) => uploadFile = f" />
            </el-tab-pane>
          </el-tabs>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="infStore.running" :disabled="infStore.running"
                     @click="handleInfer">
            {{ infStore.running ? '推理中...' : '开始推理' }}
          </el-button>
          <el-button v-if="infStore.running" type="danger" @click="handleCancel">终止</el-button>
          <el-button v-if="infStore.taskId && !infStore.running" @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
      </el-col>
      <!-- 右侧：运行日志 -->
      <el-col :span="8">
        <el-card class="log-card">
          <template #header>
            <span>运行日志</span>
            <el-tag v-if="infStore.taskStatus" :type="statusTagType" size="small" style="margin-left: 8px;">
              {{ statusText }}
            </el-tag>
          </template>
          <div ref="logContainer" class="log-container">
            <div v-for="(log, i) in infStore.logs" :key="i" :style="{ color: log.color }">
              {{ log.text }}
            </div>
            <div v-if="!infStore.logs.length" style="color: #ccc;">等待开始...</div>
          </div>
          <div v-if="infStore.taskStatus" style="margin-top: 10px;">
            <el-progress :percentage="infStore.taskStatus.progress || 0"
                         :status="infStore.taskStatus.status === 'completed' ? 'success' : infStore.taskStatus.status === 'failed' ? 'exception' : ''"
                         :stroke-width="16" :text-inside="true" />
            <div style="margin-top: 8px; text-align: center;">
              <el-button v-if="infStore.running" size="small" type="danger" @click="handleCancel">终止推理</el-button>
              <el-button v-if="!infStore.running && infStore.taskId" size="small" @click="handleReset">重置</el-button>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 错误信息 -->
    <el-alert v-if="infStore.errorMsg" :title="infStore.errorMsg" type="error" show-icon closable
              style="margin-bottom: 20px;" @close="infStore.errorMsg = ''" />

    <!-- 推理结果画面 -->
    <template v-if="infStore.frameImages.length > 0">
      <el-row :gutter="20">
        <!-- 左侧：图片/视频帧 -->
        <el-col :span="14">
          <el-card>
            <template #header>
              <div style="display: flex; justify-content: space-between; align-items: center;">
                <span>检测结果</span>
                <el-tag size="small" :type="infStore.running ? 'warning' : 'success'">
                  第 {{ infStore.currentFrame + 1 }} 帧 / 共 {{ infStore.displayedFrames }} 帧
                </el-tag>
              </div>
            </template>

            <ResultImage :imageUrl="currentImageUrl" :width="640" :height="480" />

            <!-- 帧控制 -->
            <div style="margin-top: 15px; text-align: center; min-height: 80px;">
              <el-button-group>
                <el-button size="small" @click="prevFrame" :disabled="infStore.currentFrame <= 0 || !isVideo">上一帧</el-button>
                <el-button size="small" @click="togglePlay" :type="playing ? 'danger' : 'primary'"
                           :disabled="!isVideo">
                  {{ playing ? '暂停' : '播放' }}
                </el-button>
                <el-button size="small" @click="nextFrame"
                           :disabled="infStore.currentFrame >= infStore.displayedFrames - 1 || !isVideo">下一帧</el-button>
                <el-button v-if="infStore.running" size="small" @click="jumpToLatest"
                           :disabled="!isVideo">最新帧</el-button>
              </el-button-group>
              <div v-if="isVideo" style="margin-top: 10px; display: flex; align-items: center; gap: 12px;">
                <el-slider v-model="sliderFrame" :min="0"
                           :max="Math.max(0, infStore.displayedFrames - 1)"
                           :step="1" style="flex: 1;"
                           @input="onSliderDrag" />
                <el-switch v-model="autoFollow" active-text="自动跟随" size="small"
                           :disabled="!infStore.running" />
              </div>
            </div>

            <!-- 视频下载 -->
            <div v-if="videoUrl" style="margin-top: 15px; text-align: center;">
              <el-button type="success" size="small" @click="downloadVideo">
                下载结果视频
              </el-button>
            </div>
          </el-card>
        </el-col>

        <!-- 右侧：检测信息 -->
        <el-col :span="10">
          <el-card style="margin-bottom: 15px; min-height: 220px;">
            <template #header>推理信息</template>
            <el-descriptions :column="1" border size="small">
              <el-descriptions-item label="状态">
                <el-tag :type="statusTagType" size="small">{{ statusText }}</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="模型类型">{{ inferenceResult?.model_type?.toUpperCase() || '-' }}</el-descriptions-item>
              <el-descriptions-item label="设备">{{ inferenceResult?.device || '-' }}</el-descriptions-item>
              <el-descriptions-item label="已处理帧数">{{ infStore.displayedFrames }}</el-descriptions-item>
              <el-descriptions-item label="当前帧检测数">{{ currentDetections.length }}</el-descriptions-item>
            </el-descriptions>
          </el-card>

          <!-- 耗时信息 -->
          <el-card style="margin-bottom: 15px; min-height: 200px;">
            <template #header>
              当前帧耗时
              <el-tag v-if="!currentTimings" size="small" type="info">暂无数据</el-tag>
            </template>
            <el-descriptions v-if="currentTimings" :column="1" border size="small">
              <el-descriptions-item label="预处理">{{ currentTimings.preprocess_ms?.toFixed(1) }} ms</el-descriptions-item>
              <el-descriptions-item label="推理">{{ currentTimings.inference_ms?.toFixed(1) }} ms</el-descriptions-item>
              <el-descriptions-item label="后处理">{{ currentTimings.postprocess_ms?.toFixed(1) }} ms</el-descriptions-item>
              <el-descriptions-item label="总计">{{ totalTiming.toFixed(1) }} ms</el-descriptions-item>
              <el-descriptions-item label="FPS">{{ (1000 / totalTiming).toFixed(1) }}</el-descriptions-item>
            </el-descriptions>
          </el-card>

          <!-- 检测结果表 -->
          <el-card style="height: 400px; display: flex; flex-direction: column;">
            <template #header>
              <span v-if="currentDetections.length">
                检测目标 ({{ currentDetections.length }})
                <el-tag v-for="cls in detectedClasses" :key="cls.id" size="small"
                        :color="cls.color" style="margin-left: 6px; color: #fff;">
                  {{ cls.name }}
                </el-tag>
              </span>
              <span v-else>检测目标</span>
            </template>
            <div style="flex: 1; overflow: auto;">
              <el-table v-if="currentDetections.length" :data="currentDetections" size="small" stripe>
              <el-table-column label="类别" width="90">
                <template #default="{ row }">
                  <span :style="{ color: getClassColor(row.class_id) }">{{ row.class_name }}</span>
                </template>
              </el-table-column>
              <el-table-column label="置信度" width="80">
                <template #default="{ row }">{{ (row.confidence * 100).toFixed(1) }}%</template>
              </el-table-column>
              <el-table-column label="坐标 (x1,y1,x2,y2)">
                <template #default="{ row }">
                  {{ row.bbox.map(v => v.toFixed(0)).join(', ') }}
                </template>
              </el-table-column>
            </el-table>
            <el-empty v-else description="暂无检测结果" :image-size="60" />
            </div>
          </el-card>
        </el-col>
      </el-row>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { useModelStore } from '../stores/models'
import { useInferenceStore } from '../stores/inference'
import { createInferenceTask, getResultImage } from '../api/inference'
import { getDataSources, getDatasets, getDatasetSplits } from '../api/datasets'
import TaskProgress from '../components/TaskProgress.vue'
import ResultImage from '../components/ResultImage.vue'
import FileUploader from '../components/FileUploader.vue'

const CLASS_COLORS = [
  '#00ff00', '#ff8c00', '#ff0000', '#0000ff',
  '#00ffff', '#ffff00', '#ff00ff', '#800080',
  '#ff8000', '#808000',
]

const store = useModelStore()
const infStore = useInferenceStore()
const dataSources = ref([])
const managedDatasets = ref([])
const datasetSplits = ref([])
const dataSourceType = ref('dataset')
const uploadFile = ref(null)
const logContainer = ref(null)
const form = ref({
  model_id: null, model_type: 'pt', device: 'cpu',
  confidence_threshold: 0.5, dataset_path: null,
  dataset_id: null, dataset_split: null,
})
const playing = ref(false)
const autoFollow = ref(true)
let playTimer = null

const selectedModel = computed(() => store.models.find(m => m.id === form.value.model_id))
const isVideo = computed(() => infStore.displayedFrames > 1)

const currentFrameData = computed(() => {
  if (!infStore.frameImages.length) return null
  return infStore.frameImages[infStore.currentFrame] || null
})
const currentImageUrl = computed(() => currentFrameData.value?.imageUrl || '')
const currentDetections = computed(() => currentFrameData.value?.detections || [])
const currentTimings = computed(() => currentFrameData.value?.timings || null)
const totalTiming = computed(() => {
  if (!currentTimings.value) return 0
  return (currentTimings.value.preprocess_ms || 0) +
         (currentTimings.value.inference_ms || 0) +
         (currentTimings.value.postprocess_ms || 0)
})

const videoUrl = computed(() => {
  if (!infStore.resultData?.video_path || !infStore.taskId) return null
  return `/api/inference/${infStore.taskId}/video`
})

const detectedClasses = computed(() => {
  const seen = new Map()
  for (const img of infStore.frameImages) {
    for (const d of img.detections) {
      if (!seen.has(d.class_id)) {
        seen.set(d.class_id, {
          id: d.class_id,
          name: d.class_name,
          color: CLASS_COLORS[d.class_id % CLASS_COLORS.length],
        })
      }
    }
  }
  return [...seen.values()]
})

function getClassColor(classId) {
  return CLASS_COLORS[classId % CLASS_COLORS.length]
}

const inferenceResult = computed(() => {
  if (currentFrameData.value) {
    return infStore.resultData || { model_type: form.value.model_type, device: form.value.device }
  }
  return infStore.resultData
})

const statusText = computed(() => {
  if (!infStore.taskStatus) return '-'
  const map = { pending: '等待中', running: '执行中', completed: '已完成', failed: '失败' }
  return map[infStore.taskStatus.status] || infStore.taskStatus.status
})
const statusTagType = computed(() => {
  if (!infStore.taskStatus) return 'info'
  if (infStore.taskStatus.status === 'completed') return 'success'
  if (infStore.taskStatus.status === 'failed') return 'danger'
  if (infStore.taskStatus.status === 'running') return 'warning'
  return 'info'
})

const sliderFrame = computed({
  get: () => infStore.currentFrame,
  set: (val) => infStore.setCurrentFrame(val),
})

onMounted(async () => {
  await store.fetchModels()
  try {
    dataSources.value = (await getDataSources()).data
    managedDatasets.value = (await getDatasets()).data
  } catch (e) { /* ignore */ }
  if (store.models.length && !form.value.model_id) form.value.model_id = store.models[0].id
  if (dataSources.value.length && !form.value.dataset_path) form.value.dataset_path = dataSources.value[0].path
  if (managedDatasets.value.length) {
    form.value.dataset_id = managedDatasets.value[0].id
    onDatasetChange(form.value.dataset_id)
  }
})

onUnmounted(() => { stopPlay() })

function onModelChange(id) {
  const m = store.models.find(m => m.id === id)
  if (m) form.value.model_type = m.onnx_converted ? 'onnx' : 'pt'
}

async function onDatasetChange(id) {
  form.value.dataset_split = null
  datasetSplits.value = []
  if (!id) return
  try {
    const res = await getDatasetSplits(id)
    datasetSplits.value = res.data
    if (res.data.length) form.value.dataset_split = res.data[0].name
  } catch (e) { /* ignore */ }
}

async function handleInfer() {
  if (!form.value.model_id) { ElMessage.warning('请选择模型'); return }
  stopPlay()
  autoFollow.value = true

  try {
    const formData = new FormData()
    formData.append('mid', form.value.model_id)
    formData.append('mtype', form.value.model_type)
    formData.append('device', form.value.device)
    formData.append('confidence_threshold', form.value.confidence_threshold)

    if (dataSourceType.value === 'dataset' && form.value.dataset_id) {
      // 使用数据集：通过 dataset_id + split 找到第一张图片
      const ds = managedDatasets.value.find(d => d.id === form.value.dataset_id)
      if (ds) {
        // 数据集目录下的第一张图片
        const split = form.value.dataset_split || ''
        formData.append('dataset_path', ds.path + (split ? '/' + split : ''))
      }
    } else if (dataSourceType.value === 'upload' && uploadFile.value) {
      formData.append('file', uploadFile.value)
    } else if (form.value.dataset_path) {
      formData.append('dataset_path', form.value.dataset_path)
    } else {
      ElMessage.warning('请选择或上传数据源'); return
    }

    const res = await createInferenceTask(formData)
    infStore.startTask(res.data.task_id)
    ElMessage.info('推理任务已启动')
  } catch (e) {
    ElMessage.error('创建推理任务失败: ' + (e.response?.data?.detail || e.message))
  }
}

function handleReset() { stopPlay(); infStore.reset() }
function handleCancel() { infStore.cancelTask(); infStore.addLog('已发送终止信号...', '#E6A23C') }

function scrollToBottom() {
  nextTick(() => {
    if (logContainer.value) logContainer.value.scrollTop = logContainer.value.scrollHeight
  })
}

function prevFrame() { if (infStore.currentFrame > 0) infStore.setCurrentFrame(infStore.currentFrame - 1) }
function nextFrame() { if (infStore.currentFrame < infStore.displayedFrames - 1) infStore.setCurrentFrame(infStore.currentFrame + 1) }
function jumpToLatest() { infStore.setCurrentFrame(infStore.displayedFrames - 1) }

function onSliderDrag() {
  // 用户拖动进度条时：关闭自动跟随 + 暂停播放
  autoFollow.value = false
  if (playing.value) stopPlay()
}

function togglePlay() {
  if (playing.value) {
    stopPlay()
  } else {
    playing.value = true
    autoFollow.value = false
    playTimer = setInterval(() => {
      if (infStore.currentFrame < infStore.displayedFrames - 1) {
        infStore.setCurrentFrame(infStore.currentFrame + 1)
      } else {
        // 到达最后一帧：推理中则等待，否则停止
        if (!infStore.running) stopPlay()
      }
    }, 150)
  }
}

function stopPlay() {
  playing.value = false
  if (playTimer) { clearInterval(playTimer); playTimer = null }
}

function downloadVideo() {
  if (!videoUrl.value) return
  const a = document.createElement('a')
  a.href = videoUrl.value
  a.download = 'result.mp4'
  a.click()
}

// 实时推理中：仅在自动跟随 + 未播放 + 未拖动时跳到最新帧
watch(() => infStore.displayedFrames, (newVal, oldVal) => {
  if (infStore.running && autoFollow.value && !playing.value && newVal > 0) {
    infStore.setCurrentFrame(newVal - 1)
  }
  if (newVal > oldVal && infStore.running) {
    infStore.addLog(`已处理第 ${newVal} 帧`, '#67C23A')
    scrollToBottom()
  }
})

// 进度消息变化 → 写入日志
let lastProgressMsg = ''
watch(() => infStore.progressMsg, (msg) => {
  if (msg && msg !== lastProgressMsg) {
    lastProgressMsg = msg
    infStore.addLog(msg)
    scrollToBottom()
  }
})

// 推理状态变化 → 写入日志
watch(() => infStore.taskStatus?.status, (status) => {
  if (status === 'running') { infStore.addLog('推理任务已启动', '#409EFF'); scrollToBottom() }
  else if (status === 'completed') { infStore.addLog('推理任务已完成', '#67C23A'); scrollToBottom() }
  else if (status === 'failed') { infStore.addLog('推理任务失败: ' + (infStore.errorMsg || ''), '#F56C6C'); scrollToBottom() }
})
</script>

<style scoped>
.inference-form-card {
  height: 480px;
  overflow: auto;
}

.log-card {
  height: 480px;
  display: flex;
  flex-direction: column;
}

.log-card :deep(.el-card__body) {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.log-container {
  flex: 1;
  overflow-y: auto;
  font-family: monospace;
  font-size: 12px;
  line-height: 1.6;
  color: #333;
  background: #fafafa;
  padding: 8px;
  border-radius: 4px;
  min-height: 320px;
}
</style>

<style>
/* 全局样式：数据集下拉框宽度 */
.dataset-dropdown {
  min-width: 400px !important;
  max-width: 600px !important;
}

.dataset-dropdown .el-select-dropdown__item {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
