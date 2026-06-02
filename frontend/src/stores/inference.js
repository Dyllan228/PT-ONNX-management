/**
 * 推理状态管理 Store
 *
 * 使用 Pinia 管理推理任务的全局状态
 *
 * 技术栈：
 * - Pinia: Vue 3 状态管理库
 * - Vue 3 Composition API: ref、computed 等响应式 API
 *
 * 状态：
 * - taskId: 当前任务 ID
 * - taskStatus: 任务状态
 * - resultData: 推理结果
 * - currentFrame: 当前显示的帧
 * - displayedFrames: 已加载的帧数
 * - frameImages: 帧图片数组
 * - running: 是否正在运行
 * - errorMsg: 错误信息
 * - progressMsg: 进度消息
 * - logs: 运行日志
 *
 * 方法：
 * - startTask: 开始任务
 * - reset: 重置状态
 * - setCurrentFrame: 设置当前帧
 * - stopPolling: 停止轮询
 * - cancelTask: 取消任务
 * - addLog: 添加日志
 */

import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getInferenceTask, cancelInferenceTask, getResultImage } from '../api/inference'

/**
 * 定义推理 Store
 *
 * 使用 Composition API 风格（setup 函数）
 */
export const useInferenceStore = defineStore('inference', () => {
  // ===== 状态 =====
  const taskId = ref('')           // 当前任务 ID
  const taskStatus = ref(null)     // 任务状态 { status, progress, error_msg }
  const resultData = ref(null)     // 推理结果
  const currentFrame = ref(0)      // 当前显示的帧索引
  const displayedFrames = ref(0)   // 已加载的帧数
  const frameImages = ref([])      // 帧图片数组 [{ frame, imageUrl, detections, timings }]
  const running = ref(false)       // 是否正在运行
  const errorMsg = ref('')         // 错误信息
  const progressMsg = ref('')      // 进度消息
  const logs = ref([])             // 运行日志 [{ text, color }]
  let pollTimer = null             // 轮询定时器

  // ===== 方法 =====

  /**
   * 开始推理任务
   * @param {string} id - 任务 ID
   */
  function startTask(id) {
    reset()
    taskId.value = id
    taskStatus.value = { status: 'running', progress: 0 }
    running.value = true
    startPolling()
  }

  /**
   * 开始轮询任务状态
   * 每 800ms 查询一次任务状态，加载新帧
   */
  function startPolling() {
    stopPolling()
    pollTimer = setInterval(async () => {
      if (!taskId.value) return
      try {
        // 查询任务状态
        const res = await getInferenceTask(taskId.value)
        const data = res.data
        taskStatus.value = data

        // 读取进度消息
        if (data.result?._progress_msg) {
          progressMsg.value = data.result._progress_msg
        }

        // 加载新可用的帧
        if (data.result?.total_frames > 0) {
          const total = data.result.total_frames
          if (data.result.detections_summary) {
            resultData.value = data.result
          }
          // 逐帧加载图片
          while (displayedFrames.value < total) {
            const frameIdx = displayedFrames.value
            const summary = data.result.detections_summary?.find(d => d.frame === frameIdx)
            frameImages.value.push({
              frame: frameIdx,
              imageUrl: getResultImage(taskId.value, frameIdx),
              detections: summary?.detections || [],
              timings: summary?.timings || null,
            })
            displayedFrames.value++
          }
        }

        // 检查任务是否完成
        if (data.status === 'completed') {
          stopPolling()
          running.value = false
          resultData.value = data.result
          progressMsg.value = '推理完成'
        } else if (data.status === 'failed') {
          stopPolling()
          running.value = false
          errorMsg.value = data.error_msg || '推理失败'
          progressMsg.value = data.error_msg || '推理失败'
        }
      } catch (e) {
        // 静默重试（网络错误等）
      }
    }, 800)
  }

  /**
   * 停止轮询
   */
  function stopPolling() {
    if (pollTimer) {
      clearInterval(pollTimer)
      pollTimer = null
    }
  }

  /**
   * 取消推理任务
   */
  async function cancelTask() {
    if (!taskId.value || !running.value) return
    try {
      await cancelInferenceTask(taskId.value)
      progressMsg.value = '正在终止...'
    } catch (e) {
      // ignore
    }
  }

  /**
   * 添加运行日志
   * @param {string} msg - 日志消息
   * @param {string} color - 文字颜色（默认 #333）
   */
  function addLog(msg, color = '#333') {
    const time = new Date().toLocaleTimeString('zh-CN', { hour12: false })
    logs.value.push({ text: `[${time}] ${msg}`, color })
    // 限制日志数量，避免内存溢出
    if (logs.value.length > 500) {
      logs.value = logs.value.slice(-300)
    }
  }

  /**
   * 重置所有状态
   */
  function reset() {
    stopPolling()
    taskId.value = ''
    taskStatus.value = null
    resultData.value = null
    currentFrame.value = 0
    displayedFrames.value = 0
    frameImages.value = []
    running.value = false
    errorMsg.value = ''
    progressMsg.value = ''
    logs.value = []
  }

  /**
   * 设置当前显示的帧
   * @param {number} idx - 帧索引
   */
  function setCurrentFrame(idx) {
    currentFrame.value = idx
  }

  // 返回状态和方法
  return {
    taskId, taskStatus, resultData, currentFrame, displayedFrames,
    frameImages, running, errorMsg, progressMsg, logs,
    startTask, reset, setCurrentFrame, stopPolling, cancelTask, addLog,
  }
})
