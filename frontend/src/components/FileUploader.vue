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
defineProps({
  accept: { type: String, default: '.pt' },
})
const emit = defineEmits(['file-change'])

function handleFileChange(file) {
  emit('file-change', file.raw)
}
</script>
