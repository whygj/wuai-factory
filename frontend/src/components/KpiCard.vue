<template>
  <el-card class="kpi-card" :style="{ borderTop: `4px solid ${color}` }">
    <div class="kpi-value" :style="{ color }">{{ value }}</div>
    <div class="kpi-label">{{ label }}</div>
    <div class="kpi-icon">{{ icon }}</div>
  </el-card>
</template>

<script setup>
defineProps({
  label: String,
  value: [String, Number],
  icon: { type: String, default: '' },
  color: { type: String, default: '#E65100' },
})
</script>

<style scoped>
.kpi-card {
  position: relative;
  overflow: hidden;
}

.kpi-value {
  font-size: 32px;
  font-weight: 800;
  line-height: 1.2;
}

.kpi-label {
  font-size: 14px;
  color: var(--text-light);
  margin-top: 4px;
}

.kpi-icon {
  position: absolute;
  right: 16px;
  top: 16px;
  font-size: 36px;
  opacity: 0.3;
}
</style>
