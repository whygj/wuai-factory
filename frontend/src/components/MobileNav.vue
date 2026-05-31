<template>
  <nav class="mobile-nav">
    <router-link to="/" class="tab-item" :class="{ active: $route.path === '/' }">
      <span class="tab-icon">📊</span>
      <span class="tab-label">仪表盘</span>
    </router-link>
    <router-link to="/production/new" class="tab-item" :class="{ active: $route.path.includes('/production') }">
      <span class="tab-icon">⚙️</span>
      <span class="tab-label">生产</span>
    </router-link>
    <router-link to="/sales-orders" class="tab-item" :class="{ active: $route.path === '/sales-orders' }">
      <span class="tab-icon">🚚</span>
      <span class="tab-label">销售</span>
    </router-link>
    <router-link to="/materials" class="tab-item" :class="{ active: $route.path === '/materials' || $route.path === '/products' }">
      <span class="tab-icon">📦</span>
      <span class="tab-label">库存</span>
    </router-link>
    <router-link to="/more" class="tab-item" :class="{ active: showMore }" @click.prevent="toggleMore">
      <span class="tab-icon">☰</span>
      <span class="tab-label">更多</span>
    </router-link>
  </nav>

  <!-- More Menu Overlay -->
  <div v-if="showMore" class="more-overlay" @click="showMore = false">
    <div class="more-menu" @click.stop>
      <router-link to="/customers" class="more-item" @click="showMore = false">👥 客户管理</router-link>
      <router-link to="/suppliers" class="more-item" @click="showMore = false">🏭 供应商</router-link>
      <router-link to="/purchases" class="more-item" @click="showMore = false">📦 采购管理</router-link>
      <router-link to="/lab" class="more-item" @click="showMore = false">🔬 试验室</router-link>
      <router-link to="/receivables" class="more-item" @click="showMore = false">💰 应收款</router-link>
      <router-link to="/reports" class="more-item" @click="showMore = false">📊 经营报表</router-link>
      <div class="more-item more-action" v-if="hasMultipleRoles" @click="switchRole">🔄 切换角色</div>
      <div class="more-item more-action" @click="logout">🚪 退出登录</div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { logoutApi } from '../api'

const router = useRouter()
const showMore = ref(false)
const userRoles = computed(() => JSON.parse(localStorage.getItem('userRoles') || '[]'))
const hasMultipleRoles = computed(() => userRoles.value.length > 1)

function toggleMore() {
  showMore.value = !showMore.value
}

function switchRole() {
  showMore.value = false
  router.push('/select-role')
}

function logout() {
  showMore.value = false
  logoutApi().catch(() => {})
  localStorage.removeItem('displayName')
  localStorage.removeItem('currentRole')
  localStorage.removeItem('userRoles')
  router.push('/login')
}
</script>

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
  padding: 8px 12px;
  transition: color 0.2s;
}

.tab-item.active {
  color: var(--primary);
}

.tab-icon {
  font-size: 22px;
}

.tab-label {
  font-size: 11px;
}

.more-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.4);
  z-index: 199;
}

.more-menu {
  position: fixed;
  bottom: 64px;
  left: 0;
  right: 0;
  background: white;
  padding: 12px 0;
  border-top-left-radius: 16px;
  border-top-right-radius: 16px;
  box-shadow: 0 -4px 20px rgba(0,0,0,0.12);
}

.more-item {
  display: block;
  padding: 16px 24px;
  font-size: 17px;
  color: #333;
  text-decoration: none;
  transition: background 0.2s;
}

.more-item:hover {
  background: #FFF3E0;
}

.more-action {
  cursor: pointer;
  border-top: 1px solid #f0f0f0;
  margin-top: 8px;
  padding-top: 16px;
}
</style>
