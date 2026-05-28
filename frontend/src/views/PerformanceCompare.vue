<template>
  <div>
    <h2>性能对比</h2>
    <el-card style="margin-bottom: 20px;">
      <el-form :model="form" label-width="100px">
        <el-form-item label="对比模式">
          <el-radio-group v-model="form.mode" @change="onModeChange">
            <el-radio value="pt_onnx">PT vs ONNX（纵向）</el-radio>
            <el-radio value="pt_pt">PT vs PT（版本横向）</el-radio>
            <el-radio value="onnx_onnx">ONNX vs ONNX（版本横向）</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="选择模型">
          <el-checkbox-group v-model="form.model_ids" :max="form.mode === 'pt_onnx' ? 1 : 5">
            <el-checkbox
              v-for="m in availableModels"
              :key="m.id"
              :value="m.id"
            >
              {{ m.name }} ({{ m.version }}) - {{ getModelTypeLabel(m) }}
            </el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        <el-form-item label="硬件">
          <el-checkbox-group v-model="form.devices">
            <el-checkbox value="cpu">CPU</el-checkbox>
            <el-checkbox value="cuda">GPU (CUDA)</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="running" @click="handleBenchmark">开始对比</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card v-if="currentTask" style="margin-bottom: 20px;">
      <TaskProgress :task="currentTask" @reset="currentTask = null" />
    </el-card>

    <template v-if="benchmarkResults.length">
      <el-row :gutter="20">
        <el-col :span="12">
          <el-card>
            <h3>推理速度对比</h3>
            <MetricsChart :option="speedChartOption" />
          </el-card>
        </el-col>
        <el-col :span="12">
          <el-card>
            <h3>资源占用对比</h3>
            <MetricsChart :option="resourceChartOption" />
          </el-card>
        </el-col>
      </el-row>
      <el-card style="margin-top: 20px;">
        <h3>综合对比汇总</h3>
        <el-table :data="benchmarkResults" stripe>
          <el-table-column label="模型" prop="label" />
          <el-table-column label="设备" prop="device" width="80" />
          <el-table-column label="平均推理(ms)" prop="avg_inference_ms" width="130" />
          <el-table-column label="预处理(ms)" prop="avg_preprocess_ms" width="110" />
          <el-table-column label="后处理(ms)" prop="avg_postprocess_ms" width="110" />
          <el-table-column label="FPS" prop="fps" width="80" />
          <el-table-column label="峰值内存(MB)" prop="peak_memory_mb" width="130" />
          <el-table-column label="模型大小(MB)" prop="model_size_mb" width="130" />
        </el-table>
      </el-card>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useModelStore } from '../stores/models'
import { createBenchmarkTask, getBenchmarkTask } from '../api/benchmark'
import TaskProgress from '../components/TaskProgress.vue'
import MetricsChart from '../components/MetricsChart.vue'

const store = useModelStore()
const form = ref({
  mode: 'pt_onnx',
  model_ids: [],
  devices: ['cpu'],
})
const running = ref(false)
const currentTask = ref(null)
const benchmarkResults = ref([])

const availableModels = computed(() => {
  if (form.value.mode === 'pt_onnx') return store.models.filter(m => m.onnx_converted)
  if (form.value.mode === 'onnx_onnx') return store.models.filter(m => m.onnx_converted)
  return store.models
})

onMounted(() => store.fetchModels())

function getModelTypeLabel(model) {
  if (form.value.mode === 'pt_onnx') return 'PT + ONNX'
  if (form.value.mode === 'onnx_onnx') return 'ONNX'
  return 'PT'
}

function onModeChange() {
  form.value.model_ids = []
}

async function handleBenchmark() {
  if (!form.value.model_ids.length) { ElMessage.warning('请选择模型'); return }
  if (!form.value.devices.length) { ElMessage.warning('请选择硬件'); return }

  running.value = true
  const modelTypes = form.value.model_ids.map(() => {
    if (form.value.mode === 'pt_onnx') return 'pt'
    if (form.value.mode === 'onnx_onnx') return 'onnx'
    return 'pt'
  })

  try {
    const res = await createBenchmarkTask({
      model_ids: form.value.model_ids,
      model_types: modelTypes,
      devices: form.value.devices,
    })
    const taskId = res.data.task_id
    currentTask.value = { task_id: taskId, status: 'running', progress: 0 }

    const timer = setInterval(async () => {
      const statusRes = await getBenchmarkTask(taskId)
      currentTask.value = { ...statusRes.data, task_id: taskId }
      if (statusRes.data.status === 'completed' || statusRes.data.status === 'failed') {
        clearInterval(timer)
        running.value = false
        if (statusRes.data.status === 'completed') {
          benchmarkResults.value = (statusRes.data.result?.benchmarks || []).map(b => ({
            ...b,
            label: `${b.model_name} ${b.model_version} (${b.model_type.toUpperCase()})`,
          }))
          ElMessage.success('对比完成')
        } else {
          ElMessage.error('对比失败: ' + statusRes.data.error_msg)
        }
      }
    }, 2000)
  } catch (e) {
    running.value = false
  }
}

const speedChartOption = computed(() => {
  const labels = benchmarkResults.value.map(r => `${r.label}-${r.device}`)
  return {
    tooltip: { trigger: 'axis' },
    legend: { data: ['预处理', '推理', '后处理'] },
    xAxis: { type: 'category', data: labels, axisLabel: { rotate: 30 } },
    yAxis: { type: 'value', name: '耗时 (ms)' },
    series: [
      { name: '预处理', type: 'bar', stack: 'total', data: benchmarkResults.value.map(r => r.avg_preprocess_ms) },
      { name: '推理', type: 'bar', stack: 'total', data: benchmarkResults.value.map(r => r.avg_inference_ms) },
      { name: '后处理', type: 'bar', stack: 'total', data: benchmarkResults.value.map(r => r.avg_postprocess_ms) },
    ],
  }
})

const resourceChartOption = computed(() => {
  const labels = benchmarkResults.value.map(r => `${r.label}-${r.device}`)
  return {
    tooltip: { trigger: 'axis' },
    legend: { data: ['峰值内存 (MB)', '模型大小 (MB)'] },
    xAxis: { type: 'category', data: labels, axisLabel: { rotate: 30 } },
    yAxis: { type: 'value', name: 'MB' },
    series: [
      { name: '峰值内存 (MB)', type: 'bar', data: benchmarkResults.value.map(r => r.peak_memory_mb) },
      { name: '模型大小 (MB)', type: 'bar', data: benchmarkResults.value.map(r => r.model_size_mb) },
    ],
  }
})
</script>
