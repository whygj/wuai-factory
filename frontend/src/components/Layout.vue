<template>
  <div class="layout">
    <!-- Desktop Sidebar -->
    <aside class="sidebar" v-if="!isMobile">
      <div class="sidebar-header">
        <h2>五爱食品工厂</h2>
      </div>
      <nav class="sidebar-nav">
        <router-link to="/" class="nav-item" :class="{ active: $route.path === '/' }">
          <span class="nav-icon">📊</span>
          <span>仪表盘</span>
        </router-link>
        <router-link to="/materials" class="nav-item" :class="{ active: $route.path === '/materials' }">
          <span class="nav-icon">🧈</span>
          <span>原料管理</span>
        </router-link>
        <router-link to="/production/new" class="nav-item" :class="{ active: $route.path.includes('/production') }">
          <span class="nav-icon">🏭</span>
          <span>生产管理</span>
        </router-link>
        <router-link to="/shipments/new" class="nav-item" :class="{ active: $route.path.includes('/shipments') }">
          <span class="nav-icon">🚚</span>
          <span>发货管理</span>
        </router-link>
      </nav>
      <div class="sidebar-footer">
        <div class="user-info">
          <span>{{ userDisplay }}</span>
        </div>
        <el-button size="small" @click="logout" text>退出登录</el-button>
      </div>
    </aside>

    <!-- Main Content -->
    <main class="main-content">
      <router-view />
    </main>

    <!-- Mobile Bottom Nav -->
    <MobileNav v-if="isMobile" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import MobileNav from './MobileNav.vue'

const router = useRouter()
const isMobile = ref(false)
const userDisplay = computed(() => localStorage.getItem('displayName') || '')

function checkMobile() {
  isMobile.value = window.innerWidth <= 768
}

function logout() {
  localStorage.removeItem('token')
  localStorage.removeItem('displayName')
  router.push('/login')
}

onMounted(() => {
  checkMobile()
  window.addEventListener('resize', checkMobile)
})
onUnmounted(() => {
  window.removeEventListener('resize', checkMobile)
})
</script>

<style scoped>
.layout {
  display: flex;
  min-height: 100vh;
}

.sidebar {
  width: 220px;
  background: var(--primary);
  color: white;
  display: flex;
  flex-direction: column;
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  z-index: 100;
}

.sidebar-header {
  padding: 24px 20px;
  border-bottom: 1px solid rgba(255,255,255,0.15);
}

.sidebar-header h2 {
  font-size: 18px;
  font-weight: 700;
}

.sidebar-nav {
  flex: 1;
  padding: 12px 0;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 24px;
  color: rgba(255,255,255,0.8);
  text-decoration: none;
  font-size: 16px;
  transition: all 0.2s;
}

.nav-item:hover,
.nav-item.active {
  background: rgba(255,255,255,0.15);
  color: white;
}

.nav-icon {
  font-size: 20px;
}

.sidebar-footer {
  padding: 16px 20px;
  border-top: 1px solid rgba(255,255,255,0.15);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.user-info {
  color: rgba(255,255,255,0.9);
  font-size: 14px;
}

.main-content {
  flex: 1;
  margin-left: 220px;
  padding: 24px;
  min-height: 100vh;
}

@media (max-width: 768px) {
  .sidebar {
    display: none;
  }
  .main-content {
    margin-left: 0;
    padding: 16px;
    padding-bottom: 80px;
  }
}
</style>
