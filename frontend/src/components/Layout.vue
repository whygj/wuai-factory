<template>
  <div class="layout">
    <!-- Desktop Sidebar -->
    <aside class="sidebar" v-if="!isMobile">
      <div class="sidebar-header">
        <h2>五爱食品工厂</h2>
      </div>
      <nav class="sidebar-nav">
        <!-- 经营分析 -->
        <div class="nav-group">
          <div class="nav-group-title" @click="toggleGroup('overview')">
            <span>📊 经营分析</span>
            <span class="nav-arrow" :class="{ open: expandedGroups.overview }">›</span>
          </div>
          <div class="nav-group-items" v-show="expandedGroups.overview">
            <router-link to="/" class="nav-item" :class="{ active: $route.path === '/' }">
              <span>仪表盘</span>
            </router-link>
            <router-link to="/reports" class="nav-item" :class="{ active: $route.path === '/reports' }">
              <span>经营报表</span>
            </router-link>
            <router-link to="/cost" class="nav-item" :class="{ active: $route.path === '/cost' }">
              <span>生产成本</span>
            </router-link>
          </div>
        </div>

        <!-- 客户供应商 -->
        <div class="nav-group">
          <div class="nav-group-title" @click="toggleGroup('trade')">
            <span>👥 客户供应商</span>
            <span class="nav-arrow" :class="{ open: expandedGroups.trade }">›</span>
          </div>
          <div class="nav-group-items" v-show="expandedGroups.trade">
            <router-link to="/customers" class="nav-item" :class="{ active: $route.path === '/customers' }">
              <span>客户管理</span>
            </router-link>
            <router-link to="/suppliers" class="nav-item" :class="{ active: $route.path === '/suppliers' }">
              <span>供应商</span>
            </router-link>
          </div>
        </div>

        <!-- 采购库存 -->
        <div class="nav-group">
          <div class="nav-group-title" @click="toggleGroup('stock')">
            <span>📦 采购库存</span>
            <span class="nav-arrow" :class="{ open: expandedGroups.stock }">›</span>
          </div>
          <div class="nav-group-items" v-show="expandedGroups.stock">
            <router-link to="/purchases" class="nav-item" :class="{ active: $route.path === '/purchases' }">
              <span>采购管理</span>
            </router-link>
            <router-link to="/materials" class="nav-item" :class="{ active: $route.path === '/materials' }">
              <span>原料库存</span>
            </router-link>
            <router-link to="/products" class="nav-item" :class="{ active: $route.path === '/products' }">
              <span>产品库存</span>
            </router-link>
          </div>
        </div>

        <!-- 生产质量 -->
        <div class="nav-group">
          <div class="nav-group-title" @click="toggleGroup('prod')">
            <span>🏭 生产质量</span>
            <span class="nav-arrow" :class="{ open: expandedGroups.prod }">›</span>
          </div>
          <div class="nav-group-items" v-show="expandedGroups.prod">
            <router-link to="/production/new" class="nav-item" :class="{ active: $route.path.includes('/production') }">
              <span>生产管理</span>
            </router-link>
            <router-link to="/lab" class="nav-item" :class="{ active: $route.path === '/lab' }">
              <span>试验室</span>
            </router-link>
            <router-link to="/batch-trace" class="nav-item" :class="{ active: $route.path === '/batch-trace' }">
              <span>批次追溯</span>
            </router-link>
          </div>
        </div>

        <!-- 销售财务 -->
        <div class="nav-group">
          <div class="nav-group-title" @click="toggleGroup('sales')">
            <span>🚚 销售财务</span>
            <span class="nav-arrow" :class="{ open: expandedGroups.sales }">›</span>
          </div>
          <div class="nav-group-items" v-show="expandedGroups.sales">
            <router-link to="/sales-orders" class="nav-item" :class="{ active: $route.path === '/sales-orders' }">
              <span>销售发货</span>
            </router-link>
            <router-link to="/receivables" class="nav-item" :class="{ active: $route.path === '/receivables' }">
              <span>应收款</span>
            </router-link>
            <router-link to="/payables" class="nav-item" :class="{ active: $route.path === '/payables' }">
              <span>应付款</span>
            </router-link>
          </div>
        </div>

        <!-- 系统管理 -->
        <div class="nav-group" v-if="currentRole === 'boss'">
          <div class="nav-group-title" @click="toggleGroup('system')">
            <span>⚙️ 系统管理</span>
            <span class="nav-arrow" :class="{ open: expandedGroups.system }">›</span>
          </div>
          <div class="nav-group-items" v-show="expandedGroups.system">
            <router-link to="/users" class="nav-item" :class="{ active: $route.path === '/users' }">
              <span>用户管理</span>
              <span v-if="pendingCount > 0" class="nav-badge">{{ pendingCount }}</span>
            </router-link>
            <router-link to="/operation-logs" class="nav-item" :class="{ active: $route.path === '/operation-logs' }">
              <span>操作日志</span>
            </router-link>
          </div>
        </div>
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

    <!-- Mobile Top Bar (退出按钮始终可见) -->
    <div class="mobile-topbar" v-if="isMobile">
      <span class="topbar-title">五爱食品工厂</span>
      <div class="topbar-actions">
        <span class="topbar-user">{{ userDisplay }}</span>
        <el-tag size="small" type="warning">{{ roleLabel }}</el-tag>
        <el-button size="small" type="danger" plain @click="logout" style="margin-left:8px;">退出</el-button>
      </div>
    </div>

    <!-- Main Content -->
    <main class="main-content" :class="{ 'has-topbar': isMobile }">
      <router-view />
    </main>

    <!-- Mobile Bottom Nav -->
    <MobileNav v-if="isMobile" />
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import MobileNav from './MobileNav.vue'
import { getPendingUsersApi, logoutApi } from '../api'

const router = useRouter()
const isMobile = ref(false)
const pendingCount = ref(0)
const userDisplay = computed(() => localStorage.getItem('displayName') || '')
const currentRole = computed(() => localStorage.getItem('currentRole') || '')
const userRoles = computed(() => JSON.parse(localStorage.getItem('userRoles') || '[]'))
const hasMultipleRoles = computed(() => userRoles.value.length > 1)

const roleLabels = { boss: '老板', clerk: '内勤', leader: '班长' }
const roleLabel = computed(() => roleLabels[currentRole.value] || currentRole.value)

const expandedGroups = reactive({
  overview: true,
  trade: true,
  stock: true,
  prod: true,
  sales: true,
  system: true,
})

function toggleGroup(group) {
  expandedGroups[group] = !expandedGroups[group]
}

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
  logoutApi().catch(() => {})
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
  padding: 8px 0;
  overflow-y: auto;
}

.nav-group {
  margin-bottom: 2px;
}

.nav-group-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  font-size: 15px;
  font-weight: 600;
  color: rgba(255,255,255,0.95);
  cursor: pointer;
  user-select: none;
  transition: background 0.2s;
}

.nav-group-title:hover {
  background: rgba(255,255,255,0.08);
}

.nav-arrow {
  font-size: 18px;
  transition: transform 0.2s;
  display: inline-block;
}

.nav-arrow.open {
  transform: rotate(90deg);
}

.nav-group-items {
  padding: 0;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px 10px 32px;
  color: rgba(255,255,255,0.7);
  text-decoration: none;
  font-size: 14px;
  transition: all 0.2s;
}

.nav-item:hover,
.nav-item.active {
  background: rgba(255,255,255,0.15);
  color: white;
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

/* Mobile Top Bar */
.mobile-topbar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 48px;
  background: var(--primary);
  color: white;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 12px;
  z-index: 200;
  box-shadow: 0 2px 8px rgba(0,0,0,0.15);
}

.topbar-title {
  font-size: 16px;
  font-weight: 700;
}

.topbar-actions {
  display: flex;
  align-items: center;
  gap: 6px;
}

.topbar-user {
  font-size: 13px;
  opacity: 0.9;
}

@media (max-width: 768px) {
  .sidebar {
    display: none;
  }
  .main-content {
    margin-left: 0;
    padding: 16px;
    padding-top: 60px;
    padding-bottom: 80px;
  }
}
</style>
