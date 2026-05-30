<template>
  <div v-if="alerts.length" class="alert-bar">
    <div class="alert-title">⚠️ 库存预警</div>
    <div class="alert-list">
      <div v-for="a in alerts" :key="a.id" class="alert-item">
        <span class="alert-name">{{ a.name }}</span>
        <span class="alert-detail">
          当前: {{ a.current_stock }} {{ a.unit }} / 安全线: {{ a.safety_stock }} {{ a.unit }}
        </span>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  alerts: { type: Array, default: () => [] },
})
</script>

<style scoped>
.alert-bar {
  background: #FFF3E0;
  border: 2px solid var(--danger);
  border-radius: 12px;
  padding: 16px;
}

.alert-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--danger);
  margin-bottom: 8px;
}

.alert-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 0;
  border-bottom: 1px dashed #FFCCBC;
}

.alert-item:last-child {
  border-bottom: none;
}

.alert-name {
  font-weight: 600;
  color: var(--primary-dark);
}

.alert-detail {
  color: var(--danger);
  font-size: 14px;
}
</style>
