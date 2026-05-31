<template>
  <div class="layout">
    <!-- Desktop Sidebar -->
    <aside class="sidebar" v-if="!isMobile">
      <div class="sidebar-header">
        <h2>五爱食品工厂</h2>
      </div>
      <nav class="sidebar-nav">
        <router-link to="/" class="nav-item" :class="{ active: $route.path === '/' }">
          <span class="nav-icon">📊</span><span>仪表盘</span>
        </router-link>
        <router-link to="/customers" class="nav-item" :class="{ active: $route.path === '/customers' }">
          <span class="nav-icon">👥</span><span>客户管理</span>
        </router-link>
        <router-link to="/suppliers" class="nav-item" :class="{ active: $route.path === '/suppliers' }">
          <span class="nav-icon">🏭</span><span>供应商</span>
        </router-link>
        <router-link to="/purchases" class="nav-item" :class="{ active: $route.path === '/purchases' }">
          <span class="nav-icon">📦</span><span>采购管理</span>
        </router-link>
        <router-link to="/materials" class="nav-item" :class="{ active: $route.path === '/materials' }">
          <span class="nav-icon">🧈</span><span>原料库存</span>
        </router-link>
        <router-link to="/products" class="nav-item" :class="{ active: $route.path === '/products' }">
          <span class="nav-icon">📦</span><span>产品库存</span>
        </router-link>
        <router-link to="/production/new" class="nav-item" :class="{ active: $route.path.includes('/production') }">
          <span class="nav-icon">⚙️</span><span>生产管理</span>
        </router-link>
        <router-link to="/lab" class="nav-item" :class="{ active: $route.path === '/lab' }">
          <span class="nav-icon">🔬</span><span>试验室</span>
        </router-link>
        <router-link to="/sales-orders" class="nav-item" :class="{ active: $route.path === '/sales-orders' }">
          <span class="nav-icon">🚚</span><span>销售发货</span>
        </router-link>
        <router-link to="/receivables" class="nav-item" :class="{ active: $route.path === '/receivables' }">
          <span class="nav-icon">💰</span><span>应收款</span>
        </router-link>
        <router-link to="/reports" class="nav-item" :class="{ active: $route.path === '/reports' }">
          <span class="nav-icon">📊</span><span>经营报表</span>
        </router-link>
        <router-link v-if="currentRole === 'boss'" to="/users" class="nav-item" :class="{ active: $route.path === '/users' }">
          <span class="nav-icon">👥</span><span>用户管理</span>
          <span v-if="pendingCount > 0" class="nav-badge">{{ pendingCount }}</span>
        </router-link>
      </nav>
      <div class="sidebar-footer">
        <div class="user-info">
          <span class="user-name">{{ userDisplay }}</span>
          <el-tag size="small" type="warning" class="role-tag">{{ roleLabel }}</el-tag>
        </div>
        <div class="footer-actions">
          <el-button v-if="hasMultipleRoles" size="small" @click="switchRole" text style="color: rgba(255,255,255,0.8)">切换角色</el-button>
          <el-button size="small" @click="logout" text style="color: rgba(255,255,255,0.8)">退出</el-button>
        </div>
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
import { getPendingUsersApi } from '../api'

const router = useRouter()
const isMobile = ref(false)
const pendingCount = ref(0)
const userDisplay = computed(() => localStorage.getItem('displayName') || '')
const currentRole = computed(() => localStorage.getItem('currentRole') || '')
const userRoles = computed(() => JSON.parse(localStorage.getItem('userRoles') || '[]'))
const hasMultipleRoles = computed(() => userRoles.value.length > 1)

const roleLabels = { boss: '老板', clerk: '内勤', leader: '班长' }
const roleLabel = computed(() => roleLabels[currentRole.value] || currentRole.value)

function checkMobile() {
  isMobile.value = window.innerWidth <= 768
}

async function loadPendingCount() {
  if (currentRole.value === 'boss') {
    try {
      const users = await getPendingUsersApi()
      pendingCount.value = users.length
    } catch (e) {
      pendingCount.value = 0
    }
  }
}

function logout() {
  localStorage.removeItem('token')
  localStorage.removeItem('displayName')
  localStorage.removeItem('currentRole')
  localStorage.removeItem('userRoles')
  router.push('/login')
}

function switchRole() {
  router.push('/select-role')
}

onMounted(() => {
  checkMobile()
  window.addEventListener('resize', checkMobile)
  loadPendingCount()
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
  overflow-y: auto;
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

.nav-badge {
  background: #f56c6c;
  color: white;
  font-size: 12px;
  padding: 1px 6px;
  border-radius: 10px;
  margin-left: auto;
  min-width: 18px;
  text-align: center;
}

.sidebar-footer {
  padding: 16px 20px;
  border-top: 1px solid rgba(255,255,255,0.15);
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.user-name {
  color: rgba(255,255,255,0.9);
  font-size: 14px;
}

.role-tag {
  background: rgba(255,255,255,0.2);
  border: none;
  color: white;
}

.footer-actions {
  display: flex;
  gap: 4px;
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
