<!--
  文件上传组件

  功能：
  - 支持拖拽上传
  - 支持点击上传
  - 限制单文件上传
  - 支持自定义文件类型过滤

  使用示例：
  <FileUploader accept=".pt" @file-change="(f) => file = f" />
  <FileUploader accept=".jpg,.png" @file-change="(f) => file = f" />

  Props：
  - accept: 接受的文件类型（默认 ".pt"）

  Events：
  - file-change: 文件选择变化时触发，参数为 File 对象或 null
-->

<template>
  <el-upload
    ref="uploadRef"
    :auto-upload="false"
    :limit="1"
    :on-change="handleFileChange"
    :on-remove="() => emit('file-change', null)"
    :accept="accept"
    drag
  >
    <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
    <div class="el-upload__text">将文件拖到此处，或<em>点击上传</em></div>
  </el-upload>
</template>

<script setup>
/**
 * Props 定义
 * @property {string} accept - 接受的文件类型
 */
defineProps({
  accept: { type: String, default: '.pt' },
})

/**
 * Events 定义
 * @event file-change - 文件选择变化时触发
 */
const emit = defineEmits(['file-change'])

/**
 * 处理文件选择变化
 * @param {object} file - Element Plus 的文件对象
 */
function handleFileChange(file) {
  emit('file-change', file.raw)
}
</script>
