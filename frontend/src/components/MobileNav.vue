<template>
  <nav class="mobile-nav">
    <router-link to="/" class="tab-item" :class="{ active: $route.path === '/' }">
      <span class="tab-icon">📊</span>
      <span class="tab-label">仪表盘</span>
    </router-link>
    <router-link to="/materials" class="tab-item" :class="{ active: $route.path === '/materials' }">
      <span class="tab-icon">🧈</span>
      <span class="tab-label">原料</span>
    </router-link>
    <router-link to="/production/new" class="tab-item" :class="{ active: $route.path.includes('/production') }">
      <span class="tab-icon">🏭</span>
      <span class="tab-label">生产</span>
    </router-link>
    <router-link to="/shipments/new" class="tab-item" :class="{ active: $route.path.includes('/shipments') }">
      <span class="tab-icon">🚚</span>
      <span class="tab-label">发货</span>
    </router-link>
  </nav>
</template>

<style scoped>
.mobile-nav {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: 64px;
  background: white;
  display: flex;
  align-items: center;
  justify-content: space-around;
  box-shadow: 0 -2px 10px rgba(0,0,0,0.08);
  z-index: 200;
}

.tab-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  text-decoration: none;
  color: var(--text-light);
  font-size: 12px;
  padding: 8px 16px;
  transition: color 0.2s;
}

.tab-item.active {
  color: var(--primary);
}

.tab-icon {
  font-size: 22px;
}

.tab-label {
  font-size: 12px;
}
</style>
