<template>
  <nav class="mobile-nav">
    <router-link to="/" class="tab-item" :class="{ active: $route.path === '/' }">
      <span class="tab-icon">📊</span>
      <span class="tab-label">总览</span>
    </router-link>
    <router-link to="/production" class="tab-item" :class="{ active: $route.path.includes('/production') }">
      <span class="tab-icon">⚙️</span>
      <span class="tab-label">生产</span>
    </router-link>
    <router-link to="/sales-orders" class="tab-item" :class="{ active: $route.path.includes('/sales') }">
      <span class="tab-icon">🚚</span>
      <span class="tab-label">销售</span>
    </router-link>
    <router-link to="/materials" class="tab-item" :class="{ active: $route.path === '/materials' || $route.path === '/products' }">
      <span class="tab-icon">📦</span>
      <span class="tab-label">库存</span>
    </router-link>
    <div class="tab-item" :class="{ active: showMore }" @click.prevent="toggleMore">
      <span class="tab-icon">☰</span>
      <span class="tab-label">更多</span>
    </div>
  </nav>

  <!-- Full-screen Grid Menu Overlay -->
  <Transition name="slide-up">
    <div v-if="showMore" class="more-overlay" @click="showMore = false">
      <div class="more-grid-panel" @click.stop>
        <div class="grid-header">
          <span>全部功能</span>
          <span class="grid-close" @click="showMore = false">✕</span>
        </div>

        <div class="grid-section">
          <div class="grid-section-title">经营分析</div>
          <div class="grid-items">
            <router-link to="/" class="grid-item" @click="showMore = false">
              <span class="grid-icon">📊</span><span>仪表盘</span>
            </router-link>
            <router-link to="/reports" class="grid-item" @click="showMore = false">
              <span class="grid-icon">📈</span><span>经营报表</span>
            </router-link>
            <router-link to="/cost" class="grid-item" @click="showMore = false">
              <span class="grid-icon">💰</span><span>生产成本</span>
            </router-link>
          </div>
        </div>

        <div class="grid-section">
          <div class="grid-section-title">客户供应商</div>
          <div class="grid-items">
            <router-link to="/customers" class="grid-item" @click="showMore = false">
              <span class="grid-icon">👥</span><span>客户管理</span>
            </router-link>
            <router-link to="/suppliers" class="grid-item" @click="showMore = false">
              <span class="grid-icon">🏭</span><span>供应商</span>
            </router-link>
          </div>
        </div>

        <div class="grid-section">
          <div class="grid-section-title">采购库存</div>
          <div class="grid-items">
            <router-link to="/purchases" class="grid-item" @click="showMore = false">
              <span class="grid-icon">🛒</span><span>采购管理</span>
            </router-link>
            <router-link to="/materials" class="grid-item" @click="showMore = false">
              <span class="grid-icon">🧈</span><span>原料库存</span>
            </router-link>
            <router-link to="/products" class="grid-item" @click="showMore = false">
              <span class="grid-icon">📦</span><span>产品库存</span>
            </router-link>
          </div>
        </div>

        <div class="grid-section">
          <div class="grid-section-title">生产质量</div>
          <div class="grid-items">
            <router-link to="/production/new" class="grid-item" @click="showMore = false">
              <span class="grid-icon">🏭</span><span>生产录入</span>
            </router-link>
            <router-link to="/lab" class="grid-item" @click="showMore = false">
              <span class="grid-icon">🔬</span><span>试验室</span>
            </router-link>
            <router-link to="/batch-trace" class="grid-item" @click="showMore = false">
              <span class="grid-icon">🔍</span><span>批次追溯</span>
            </router-link>
          </div>
        </div>

        <div class="grid-section">
          <div class="grid-section-title">销售财务</div>
          <div class="grid-items">
            <router-link to="/sales-orders" class="grid-item" @click="showMore = false">
              <span class="grid-icon">📋</span><span>销售订单</span>
            </router-link>
            <router-link to="/shipments" class="grid-item" @click="showMore = false">
              <span class="grid-icon">🚚</span><span>发货记录</span>
            </router-link>
            <router-link to="/receivables" class="grid-item" @click="showMore = false">
              <span class="grid-icon">💰</span><span>应收款</span>
            </router-link>
            <router-link to="/payables" class="grid-item" @click="showMore = false">
              <span class="grid-icon">🧾</span><span>应付款</span>
            </router-link>
          </div>
        </div>

        <div class="grid-section" v-if="isBoss">
          <div class="grid-section-title">系统管理</div>
          <div class="grid-items">
            <router-link to="/users" class="grid-item" @click="showMore = false">
              <span class="grid-icon">👤</span><span>用户管理</span>
            </router-link>
          </div>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { logoutApi } from '../api'

const router = useRouter()
const showMore = ref(false)
const currentRole = computed(() => localStorage.getItem('currentRole') || 'clerk')
const isBoss = computed(() => currentRole.value === 'boss')

function toggleMore() {
  showMore.value = !showMore.value
}
</script>

<style scoped>
.mobile-nav {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: 56px;
  background: white;
  display: flex;
  align-items: center;
  justify-content: space-around;
  box-shadow: 0 -2px 10px rgba(0,0,0,0.08);
  z-index: 200;
  border-top: 1px solid #f0f0f0;
}

.tab-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  text-decoration: none;
  color: #999;
  font-size: 12px;
  padding: 6px 12px;
  transition: color 0.2s;
  cursor: pointer;
  -webkit-tap-highlight-color: transparent;
}

.tab-item.active {
  color: var(--primary, #E65100);
}

.tab-icon {
  font-size: 20px;
  line-height: 1;
}

.tab-label {
  font-size: 10px;
  line-height: 1;
}

/* ===== Grid Panel ===== */
.more-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.4);
  z-index: 250;
}

.more-grid-panel {
  position: fixed;
  bottom: 56px;
  left: 0;
  right: 0;
  max-height: 75vh;
  background: #FAFAFA;
  border-top-left-radius: 16px;
  border-top-right-radius: 16px;
  box-shadow: 0 -4px 24px rgba(0,0,0,0.15);
  overflow-y: auto;
  padding-bottom: 16px;
}

.grid-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px 8px;
  font-size: 17px;
  font-weight: 700;
  color: #212121;
  position: sticky;
  top: 0;
  background: #FAFAFA;
  z-index: 1;
}

.grid-close {
  font-size: 20px;
  color: #999;
  padding: 4px 8px;
  cursor: pointer;
}

.grid-section {
  padding: 4px 16px 0;
}

.grid-section-title {
  font-size: 12px;
  color: #999;
  padding: 8px 8px 4px;
  font-weight: 500;
}

.grid-items {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
  padding: 4px 0 8px;
}

.grid-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 12px 4px;
  text-decoration: none;
  color: #333;
  font-size: 12px;
  border-radius: 12px;
  background: white;
  transition: all 0.15s ease;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
  -webkit-tap-highlight-color: transparent;
}

.grid-item:active {
  transform: scale(0.95);
  background: #FFF3E0;
}

.grid-icon {
  font-size: 26px;
  line-height: 1;
}

/* Slide-up animation */
.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.25s ease;
}

.slide-up-enter-from,
.slide-up-leave-to {
  opacity: 0;
  transform: translateY(100%);
}

.slide-up-enter-active .more-grid-panel,
.slide-up-leave-active .more-grid-panel {
  transition: transform 0.25s ease;
}
</style>
