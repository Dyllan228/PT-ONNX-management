<!--
  任务进度组件

  功能：
  - 显示任务进度条
  - 显示任务状态
  - 显示进度消息
  - 显示错误信息
  - 提供终止和重置按钮

  使用示例：
  <TaskProgress :task="taskData" @reset="handleReset" />
  <TaskProgress :task="taskData" show-cancel @cancel="handleCancel" />

  Props：
  - task: 任务对象（包含 status、progress、error_msg）
  - showCancel: 是否显示终止按钮（默认 false）
  - progressMessage: 进度消息

  Events：
  - reset: 点击重新执行时触发
  - cancel: 点击终止时触发
-->

<template>
  <div v-if="task">
    <!-- 进度条 -->
    <el-progress
      :percentage="task.progress"
      :status="progressStatus"
      :stroke-width="20"
      :text-inside="true"
    />

    <!-- 状态信息 -->
    <div style="margin-top: 10px; color: #666;">
      <span>状态: {{ statusText }}</span>
      <span v-if="progressMessage" style="margin-left: 10px; color: #409EFF;">
        {{ progressMessage }}
      </span>
      <span v-if="task.error_msg" style="color: #f56c6c; margin-left: 10px;">
        错误: {{ task.error_msg }}
      </span>
    </div>

    <!-- 操作按钮 -->
    <div style="margin-top: 10px;">
      <el-button
        v-if="showCancel && task.status === 'running'"
        size="small"
        type="danger"
        @click="$emit('cancel')"
      >
        终止
      </el-button>
      <el-button
        v-if="task.status === 'completed' || task.status === 'failed'"
        size="small"
        @click="$emit('reset')"
      >
        重新执行
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

/**
 * Props 定义
 * @property {object} task - 任务对象
 * @property {boolean} showCancel - 是否显示终止按钮
 * @property {string} progressMessage - 进度消息
 */
const props = defineProps({
  task: Object,
  showCancel: { type: Boolean, default: false },
  progressMessage: { type: String, default: '' },
})

/**
 * Events 定义
 * @event reset - 点击重新执行时触发
 * @event cancel - 点击终止时触发
 */
defineEmits(['reset', 'cancel'])

/**
 * 进度条状态
 * 根据任务状态返回对应的进度条状态
 */
const progressStatus = computed(() => {
  if (!props.task) return ''
  if (props.task.status === 'completed') return 'success'
  if (props.task.status === 'failed') return 'exception'
  return ''
})

/**
 * 状态文本
 * 将英文状态转换为中文显示
 */
const statusText = computed(() => {
  if (!props.task) return ''
  const map = { pending: '等待中', running: '执行中', completed: '已完成', failed: '失败' }
  return map[props.task.status] || props.task.status
})
</script>
