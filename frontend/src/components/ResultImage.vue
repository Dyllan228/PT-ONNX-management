<template>
  <div ref="wrapper" style="text-align: center; position: relative;">
    <canvas ref="canvas" :width="width" :height="height"
            style="max-width: 100%; border: 1px solid #eee; border-radius: 4px;" />
    <div v-if="!imageUrl" style="padding: 40px; color: #999;">暂无结果</div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  imageUrl: { type: String, default: '' },
  width: { type: Number, default: 640 },
  height: { type: Number, default: 480 },
})

const canvas = ref(null)
const wrapper = ref(null)
let ctx = null
let currentImg = null
let pendingImg = null

function drawImage(img) {
  if (!ctx || !img) return
  const cW = canvas.value.width
  const cH = canvas.value.height
  ctx.clearRect(0, 0, cW, cH)

  // 等比缩放居中绘制
  const scale = Math.min(cW / img.naturalWidth, cH / img.naturalHeight)
  const dw = img.naturalWidth * scale
  const dh = img.naturalHeight * scale
  const dx = (cW - dw) / 2
  const dy = (cH - dh) / 2
  ctx.drawImage(img, dx, dy, dw, dh)
}

function loadImage(url) {
  if (!url) return
  const img = new Image()
  img.crossOrigin = 'anonymous'
  img.onload = () => {
    // 双缓冲：预加载完成后才切换显示
    currentImg = img
    drawImage(img)
  }
  img.src = url
}

// 监听 URL 变化，预加载下一张避免闪烁
watch(() => props.imageUrl, (newUrl) => {
  if (!newUrl) return
  const img = new Image()
  img.crossOrigin = 'anonymous'
  img.onload = () => {
    currentImg = img
    drawImage(img)
  }
  img.src = newUrl
})

onMounted(() => {
  ctx = canvas.value.getContext('2d')
  if (props.imageUrl) loadImage(props.imageUrl)
})

onUnmounted(() => {
  currentImg = null
  pendingImg = null
})
</script>
