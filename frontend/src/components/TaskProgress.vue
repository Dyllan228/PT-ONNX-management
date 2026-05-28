<template>
  <div v-if="task">
    <el-progress
      :percentage="task.progress"
      :status="progressStatus"
      :stroke-width="20"
      :text-inside="true"
    />
    <div style="margin-top: 10px; color: #666;">
      <span>状态: {{ statusText }}</span>
      <span v-if="task.error_msg" style="color: #f56c6c; margin-left: 10px;">
        错误: {{ task.error_msg }}
      </span>
    </div>
    <el-button
      v-if="task.status === 'completed' || task.status === 'failed'"
      size="small"
      style="margin-top: 10px;"
      @click="$emit('reset')"
    >
      重新执行
    </el-button>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({ task: Object })
defineEmits(['reset'])

const progressStatus = computed(() => {
  if (!props.task) return ''
  if (props.task.status === 'completed') return 'success'
  if (props.task.status === 'failed') return 'exception'
  return ''
})

const statusText = computed(() => {
  if (!props.task) return ''
  const map = { pending: '等待中', running: '执行中', completed: '已完成', failed: '失败' }
  return map[props.task.status] || props.task.status
})
</script>
