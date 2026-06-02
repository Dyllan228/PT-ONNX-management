<!--
  性能对比页面

  功能：
  - 选择对比模式（PT vs ONNX、PT vs PT、ONNX vs ONNX）
  - 选择模型和设备
  - 选择数据集
  - 配置测试次数和评估选项
  - 执行性能测试
  - 显示速度对比图表
  - 显示资源占用图表
  - 显示准确度对比图表
  - 导出对比报告

  使用的技术：
  - Element Plus: Card、Form、Checkbox、Table 等组件
  - ECharts: 数据可视化图表
  - Vue 3 Composition API: ref、computed、watch、onMounted
  - Pinia: 性能对比状态管理
-->

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
          <el-checkbox-group v-model="form.model_ids">
            <el-checkbox v-for="m in availableModels" :key="m.id" :value="m.id">
              {{ m.name }} ({{ m.version }})
              <el-tag v-if="form.mode === 'pt_onnx' && !m.onnx_converted" size="small" type="info">仅PT</el-tag>
              <el-tag v-if="form.mode === 'pt_onnx' && m.onnx_converted" size="small" type="success">PT+ONNX</el-tag>
            </el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        <el-form-item label="硬件">
          <el-checkbox-group v-model="form.devices">
            <el-checkbox value="cpu">CPU</el-checkbox>
            <el-checkbox value="cuda">GPU (CUDA)</el-checkbox>
          </el-checkbox-group>
        </el-form-item>

        <!-- 数据集选择 -->
        <el-form-item label="数据集">
          <el-select v-model="form.dataset_id" placeholder="选择数据集" style="width: 300px;"
                     @change="onDatasetChange" clearable>
            <el-option v-for="d in managedDatasets" :key="d.id"
                       :label="`${d.name} (${d.image_count}张, ${d.class_names?.length || 0}类)`"
                       :value="d.id" />
          </el-select>
          <el-select v-if="form.dataset_id" v-model="form.dataset_split" placeholder="子集"
                     style="width: 140px; margin-left: 10px;">
            <el-option v-for="s in availableSplits" :key="s.name"
                       :label="`${s.name} (${s.image_count}张)`" :value="s.name" />
          </el-select>
        </el-form-item>

        <!-- 评估与测试次数 -->
        <el-form-item label="评估准确度">
          <el-switch v-model="form.evaluate" :disabled="!form.dataset_id" />
          <span style="color: #909399; font-size: 12px; margin-left: 10px;">
            需要数据集包含 YOLO 格式标注文件，计算精确率/召回率/F1/mAP
          </span>
        </el-form-item>
        <el-form-item label="测试次数">
          <el-input-number v-model="form.num_runs" :min="10" :max="500" :step="10" />
          <div class="form-tip">
            每个模型配置的推理重复次数，次数越多结果越稳定但耗时更长。推荐 100 次用于快速对比，300+ 次用于精确评估
          </div>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="running" :disabled="running" @click="handleBenchmark">
            {{ running ? '测试中...' : '开始对比' }}
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 进度 -->
    <el-card v-if="currentTask" style="margin-bottom: 20px;">
      <TaskProgress :task="currentTask" :progress-message="progressMsg" @reset="resetTask" />
    </el-card>

    <!-- 结果 -->
    <template v-if="bmStore.results.length">
      <el-row :gutter="20">
        <el-col :span="12">
          <el-card>
            <template #header>
              <span>推理速度对比</span>
              <el-button size="small" style="float: right;" @click="downloadReport">下载报告</el-button>
            </template>
            <MetricsChart :option="speedChartOption" />
          </el-card>
        </el-col>
        <el-col :span="12">
          <el-card>
            <template #header>资源占用对比</template>
            <MetricsChart :option="resourceChartOption" />
          </el-card>
        </el-col>
      </el-row>

      <el-card v-if="hasMetrics" style="margin-top: 20px;">
        <template #header>检测准确度对比</template>
        <MetricsChart :option="accuracyChartOption" :height="300" />
      </el-card>

      <el-card style="margin-top: 20px;">
        <template #header>综合对比汇总</template>
        <el-table :data="bmStore.results" stripe size="small">
          <el-table-column label="模型" prop="label" min-width="160" />
          <el-table-column label="格式" width="65">
            <template #default="{ row }">
              <el-tag :type="row.model_type === 'pt' ? 'warning' : 'success'" size="small">
                {{ row.model_type.toUpperCase() }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="设备" prop="device" width="70" />
          <el-table-column label="推理(ms)" prop="avg_inference_ms" width="90" />
          <el-table-column label="FPS" prop="fps" width="70" />
          <el-table-column label="内存(MB)" prop="peak_memory_mb" width="90" />
          <el-table-column label="模型(MB)" prop="model_size_mb" width="90" />
          <el-table-column v-if="hasMetrics" label="精确率" width="80">
            <template #default="{ row }">{{ fmtPct(row.precision) }}</template>
          </el-table-column>
          <el-table-column v-if="hasMetrics" label="召回率" width="80">
            <template #default="{ row }">{{ fmtPct(row.recall) }}</template>
          </el-table-column>
          <el-table-column v-if="hasMetrics" label="F1" width="70">
            <template #default="{ row }">{{ fmtPct(row.f1) }}</template>
          </el-table-column>
          <el-table-column v-if="hasMetrics" label="mAP@0.5" width="85">
            <template #default="{ row }">{{ fmtPct(row.mAP) }}</template>
          </el-table-column>
        </el-table>
      </el-card>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useModelStore } from '../stores/models'
import { useBenchmarkStore } from '../stores/benchmark'
import { createBenchmarkTask, getBenchmarkTask } from '../api/benchmark'
import { getDataSources, getDatasets, getDatasetSplits } from '../api/datasets'
import TaskProgress from '../components/TaskProgress.vue'
import MetricsChart from '../components/MetricsChart.vue'

const store = useModelStore()
const bmStore = useBenchmarkStore()
const managedDatasets = ref([])
const availableSplits = ref([])
const form = ref({
  mode: 'pt_onnx', model_ids: [], devices: ['cpu'],
  dataset_id: null, dataset_split: null, num_runs: 100, evaluate: false,
})
const running = ref(false)
const currentTask = ref(null)
const progressMsg = ref('')
let pollTimer = null

const availableModels = computed(() => {
  if (form.value.mode === 'onnx_onnx') return store.models.filter(m => m.onnx_converted)
  return store.models
})

const hasMetrics = computed(() => bmStore.results.some(r => r.precision !== undefined))

onMounted(async () => {
  await store.fetchModels()
  try { managedDatasets.value = (await getDatasets()).data } catch (e) { /* ignore */ }
  if (managedDatasets.value.length && !form.value.dataset_id) {
    form.value.dataset_id = managedDatasets.value[0].id
    onDatasetChange(form.value.dataset_id)
  }
})

function onModeChange() { form.value.model_ids = [] }

async function onDatasetChange(id) {
  form.value.dataset_split = null
  availableSplits.value = []
  if (!id) return
  try {
    const res = await getDatasetSplits(id)
    availableSplits.value = res.data
    if (res.data.length) form.value.dataset_split = res.data[0].name
  } catch (e) { /* ignore */ }
}

function fmtPct(v) {
  if (v === undefined || v === null) return '-'
  return (v * 100).toFixed(1) + '%'
}

async function handleBenchmark() {
  if (!form.value.model_ids.length) { ElMessage.warning('请选择模型'); return }
  if (!form.value.dataset_id) { ElMessage.warning('请选择数据集'); return }

  running.value = true
  bmStore.reset()
  progressMsg.value = ''

  let finalModelIds = [], finalModelTypes = []
  if (form.value.mode === 'pt_onnx') {
    for (const id of form.value.model_ids) {
      const m = store.models.find(m => m.id === id)
      finalModelIds.push(id); finalModelTypes.push('pt')
      if (m?.onnx_converted) { finalModelIds.push(id); finalModelTypes.push('onnx') }
    }
  } else if (form.value.mode === 'onnx_onnx') {
    finalModelIds = [...form.value.model_ids]; finalModelTypes = form.value.model_ids.map(() => 'onnx')
  } else {
    finalModelIds = [...form.value.model_ids]; finalModelTypes = form.value.model_ids.map(() => 'pt')
  }

  try {
    const res = await createBenchmarkTask({
      model_ids: finalModelIds, model_types: finalModelTypes,
      devices: form.value.devices, num_runs: form.value.num_runs,
      evaluate: form.value.evaluate,
      dataset_id: form.value.dataset_id, dataset_split: form.value.dataset_split,
    })
    const taskId = res.data.task_id
    currentTask.value = { task_id: taskId, status: 'running', progress: 0 }

    pollTimer = setInterval(async () => {
      try {
        const data = (await getBenchmarkTask(taskId)).data
        currentTask.value = { ...data, task_id: taskId }
        if (data.result?._progress_msg) progressMsg.value = data.result._progress_msg
        if (data.status === 'completed' || data.status === 'failed') {
          clearInterval(pollTimer); pollTimer = null; running.value = false
          if (data.status === 'completed') {
            const results = (data.result?.benchmarks || []).map(b => ({
              ...b, label: `${b.model_name} ${b.model_version} (${b.model_type.toUpperCase()})`,
            }))
            bmStore.setResults(results)
            progressMsg.value = '对比完成'
          } else {
            progressMsg.value = data.error_msg || '失败'
            ElMessage.error('对比失败: ' + (data.error_msg || ''))
          }
        }
      } catch (e) { clearInterval(pollTimer); pollTimer = null; running.value = false }
    }, 1500)
  } catch (e) { running.value = false; ElMessage.error('创建任务失败: ' + (e.response?.data?.detail || e.message)) }
}

function resetTask() {
  if (pollTimer) { clearInterval(pollTimer); pollTimer = null }
  currentTask.value = null; progressMsg.value = ''; running.value = false
}

function downloadReport() {
  const data = bmStore.results
  if (!data.length) return
  const lines = ['PT-ONNX 性能对比报告', '='.repeat(50), '']
  lines.push(`模型,格式,设备,推理(ms),预处理(ms),后处理(ms),FPS,内存(MB),模型(MB),精确率,召回率,F1,mAP@0.5`)
  for (const r of data) {
    lines.push([
      r.label, r.model_type.toUpperCase(), r.device,
      r.avg_inference_ms, r.avg_preprocess_ms, r.avg_postprocess_ms,
      r.fps, r.peak_memory_mb, r.model_size_mb,
      r.precision ?? '-', r.recall ?? '-', r.f1 ?? '-', r.mAP ?? '-',
    ].join(','))
  }
  const blob = new Blob([lines.join('\n')], { type: 'text/csv;charset=utf-8' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = `benchmark_report_${new Date().toISOString().slice(0, 10)}.csv`
  a.click()
}

const benchmarkResults = computed(() => bmStore.results)

const speedChartOption = computed(() => {
  const labels = benchmarkResults.value.map(r => `${r.label}-${r.device}`)
  return {
    tooltip: { trigger: 'axis' }, legend: { data: ['预处理', '推理', '后处理'] },
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
    tooltip: { trigger: 'axis' }, legend: { data: ['峰值内存 (MB)', '模型大小 (MB)'] },
    xAxis: { type: 'category', data: labels, axisLabel: { rotate: 30 } },
    yAxis: { type: 'value', name: 'MB' },
    series: [
      { name: '峰值内存 (MB)', type: 'bar', data: benchmarkResults.value.map(r => r.peak_memory_mb) },
      { name: '模型大小 (MB)', type: 'bar', data: benchmarkResults.value.map(r => r.model_size_mb) },
    ],
  }
})

const accuracyChartOption = computed(() => {
  const labels = benchmarkResults.value.map(r => `${r.label}-${r.device}`)
  return {
    tooltip: { trigger: 'axis' }, legend: { data: ['精确率', '召回率', 'F1', 'mAP@0.5'] },
    xAxis: { type: 'category', data: labels, axisLabel: { rotate: 30 } },
    yAxis: { type: 'value', name: '值', min: 0, max: 1 },
    series: [
      { name: '精确率', type: 'bar', data: benchmarkResults.value.map(r => r.precision ?? 0) },
      { name: '召回率', type: 'bar', data: benchmarkResults.value.map(r => r.recall ?? 0) },
      { name: 'F1', type: 'bar', data: benchmarkResults.value.map(r => r.f1 ?? 0) },
      { name: 'mAP@0.5', type: 'bar', data: benchmarkResults.value.map(r => r.mAP ?? 0) },
    ],
  }
})
</script>

<style scoped>
.form-tip {
  color: #909399;
  font-size: 12px;
  line-height: 1.5;
  margin-top: 4px;
}
</style>
