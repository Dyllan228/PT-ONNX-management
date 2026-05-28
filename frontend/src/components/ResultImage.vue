<template>
  <div>
    <div v-if="imageUrl" style="text-align: center;">
      <el-image :src="imageUrl" fit="contain" :max-height="500" />
      <div v-if="detections.length" style="margin-top: 10px;">
        <el-table :data="detections" size="small" max-height="200">
          <el-table-column prop="class_name" label="类别" width="100" />
          <el-table-column label="置信度" width="100">
            <template #default="{ row }">{{ (row.confidence * 100).toFixed(1) }}%</template>
          </el-table-column>
          <el-table-column label="边界框">
            <template #default="{ row }">
              [{{ row.bbox.map(v => v.toFixed(0)).join(', ') }}]
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>
    <el-empty v-else description="暂无结果" />
  </div>
</template>

<script setup>
defineProps({
  imageUrl: String,
  detections: { type: Array, default: () => [] },
})
</script>
