<template>
  <div class="kpi-card" :style="{ borderTop: `4px solid ${color}` }" @click="$emit('click')">
    <div class="kpi-header">
      <span class="kpi-label">{{ label }}</span>
      <el-icon class="kpi-icon" :style="{ color }"><component :is="icon" /></el-icon>
    </div>
    <div class="kpi-value" :style="{ color }">{{ value }}</div>
    <slot />
  </div>
</template>

<script setup>
defineProps({
  label: String,
  value: [String, Number],
  icon: { type: [String, Object], default: 'TrendCharts' },
  color: { type: String, default: '#E65100' },
})

defineEmits(['click'])
</script>

<style scoped>
.kpi-card {
  background: linear-gradient(135deg, #FFF3E0 0%, #FFFFFF 100%);
  border-radius: 12px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
  border-top: 4px solid var(--primary);
  box-shadow: var(--shadow-sm);
}

.kpi-card:hover {
  transform: scale(1.05);
  box-shadow: 0 8px 24px rgba(230, 81, 0, 0.15);
}

.kpi-card:active {
  transform: scale(1.02);
  box-shadow: var(--shadow-md);
}

.kpi-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.kpi-label {
  font-family: 'Noto Sans SC', sans-serif;
  font-size: 14px;
  font-weight: 400;
  color: var(--text-secondary);
}

.kpi-icon {
  font-size: 24px;
  opacity: 0.7;
}

.kpi-value {
  font-family: 'Inter', -apple-system, sans-serif;
  font-size: 28px;
  font-weight: 700;
  line-height: 1.2;
  letter-spacing: -0.02em;
}
</style>
