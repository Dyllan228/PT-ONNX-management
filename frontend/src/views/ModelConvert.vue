<template>
  <div>
    <h2>模型转换</h2>
    <el-card style="max-width: 600px;">
      <el-form :model="form" label-width="120px">
        <el-form-item label="选择模型">
          <el-select v-model="form.model_id" placeholder="选择 PT 模型" style="width: 100%;">
            <el-option
              v-for="m in ptModels"
              :key="m.id"
              :label="`${m.name} (${m.version})`"
              :value="m.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="输入尺寸">
          <el-input v-model="form.inputSizeStr" placeholder="640,640" />
        </el-form-item>
        <el-form-item label="ONNX Opset">
          <el-input-number v-model="form.opset_version" :min="9" :max="17" />
        </el-form-item>
        <el-form-item label="动态 Batch">
          <el-switch v-model="form.dynamic_batch" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="converting" @click="handleConvert">
            开始转换
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card v-if="currentTask" style="max-width: 600px; margin-top: 20px;">
      <h3>转换进度</h3>
      <TaskProgress :task="currentTask" @reset="currentTask = null" />
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useModelStore } from '../stores/models'
import { createConvertTask, getConvertTask } from '../api/convert'
import TaskProgress from '../components/TaskProgress.vue'

const store = useModelStore()
const ptModels = computed(() => store.models.filter(m => !m.onnx_converted))
const form = ref({ model_id: null, inputSizeStr: '640,640', opset_version: 11, dynamic_batch: true })
const converting = ref(false)
const currentTask = ref(null)

onMounted(() => {
  store.fetchModels()
  if (store.models.length) form.value.model_id = store.models[0].id
})

async function handleConvert() {
  if (!form.value.model_id) {
    ElMessage.warning('请选择模型')
    return
  }
  converting.value = true
  try {
    const inputSize = form.value.inputSizeStr.split(',').map(Number)
    const res = await createConvertTask({
      model_id: form.value.model_id,
      input_size: inputSize,
      dynamic_batch: form.value.dynamic_batch,
      opset_version: form.value.opset_version,
    })
    const taskId = res.data.task_id
    currentTask.value = { status: 'running', progress: 0 }

    const timer = setInterval(async () => {
      const statusRes = await getConvertTask(taskId)
      currentTask.value = statusRes.data
      if (statusRes.data.status === 'completed' || statusRes.data.status === 'failed') {
        clearInterval(timer)
        converting.value = false
        if (statusRes.data.status === 'completed') {
          ElMessage.success('转换完成')
          store.fetchModels()
        } else {
          ElMessage.error('转换失败: ' + statusRes.data.error_msg)
        }
      }
    }, 1500)
  } catch (e) {
    converting.value = false
    ElMessage.error('创建转换任务失败')
  }
}
</script>
