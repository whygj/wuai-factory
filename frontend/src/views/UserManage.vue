<template>
  <div class="page">
    <h2 class="page-title">用户管理</h2>

    <!-- Pending Users -->
    <div v-if="pendingUsers.length > 0" class="section">
      <h3 class="section-title">待审核用户（{{ pendingUsers.length }}）</h3>
      <div class="user-cards">
        <div v-for="u in pendingUsers" :key="u.id" class="user-card pending">
          <div class="user-avatar">{{ (u.display_name || '?')[0] }}</div>
          <div class="user-info">
            <div class="user-name">{{ u.display_name || '未命名' }}</div>
            <div class="user-phone">{{ u.phone }}</div>
            <el-tag size="small" type="warning">{{ roleLabels[u.roles[0]] || u.roles[0] }}</el-tag>
          </div>
          <div class="user-actions">
            <el-button type="primary" size="large" @click="handleApprove(u.id)">通过</el-button>
            <el-button size="large" @click="handleReject(u.id)">拒绝</el-button>
          </div>
        </div>
      </div>
    </div>

    <el-empty v-else-if="!loading" description="暂无待审核用户" />

    <!-- All Users -->
    <div class="section" style="margin-top: 24px;">
      <h3 class="section-title">全部用户</h3>
      <el-table :data="allUsers" stripe style="width: 100%;" size="large" class="hidden-mobile">
        <el-table-column prop="display_name" label="姓名" width="120" />
        <el-table-column prop="phone" label="手机号" width="140" />
        <el-table-column label="角色" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="row.roles[0] === 'boss' ? 'danger' : row.roles[0] === 'clerk' ? 'warning' : 'info'">
              {{ roleLabels[row.roles[0]] || row.roles[0] }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="statusType(row.status)">{{ statusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="注册时间">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
      </el-table>

      <div class="card-list visible-mobile">
        <div class="record-card" v-for="item in allUsers" :key="item.id">
          <div class="card-main">
            <div class="card-title">{{ item.display_name || '未命名' }}</div>
            <el-tag size="small" :type="statusType(item.status)">{{ statusText(item.status) }}</el-tag>
          </div>
          <div class="card-info">
            <span>{{ item.phone }}</span>
            <el-tag size="small" :type="item.roles[0] === 'boss' ? 'danger' : item.roles[0] === 'clerk' ? 'warning' : 'info'">
              {{ roleLabels[item.roles[0]] || item.roles[0] }}
            </el-tag>
          </div>
          <div class="card-info card-sub">{{ formatTime(item.created_at) }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getPendingUsersApi, getAllUsersApi, approveUserApi, rejectUserApi } from '../api'
import { ElMessage, ElMessageBox } from 'element-plus'

const loading = ref(true)
const pendingUsers = ref([])
const allUsers = ref([])
const roleLabels = { boss: '老板', clerk: '内勤', leader: '班长' }

async function loadData() {
  loading.value = true
  try {
    const [pending, all] = await Promise.all([
      getPendingUsersApi(),
      getAllUsersApi(),
    ])
    pendingUsers.value = pending
    allUsers.value = all
  } catch (e) {
    // handled by interceptor
  } finally {
    loading.value = false
  }
}

async function handleApprove(userId) {
  try {
    await ElMessageBox.confirm('确认通过该用户的注册申请？', '审核确认', { type: 'success' })
    await approveUserApi(userId)
    ElMessage.success('已通过')
    loadData()
  } catch (e) {
    if (e !== 'cancel') {
      // handled by interceptor
    }
  }
}

async function handleReject(userId) {
  try {
    await ElMessageBox.confirm('确认拒绝该用户的注册申请？', '审核确认', { type: 'warning' })
    await rejectUserApi(userId)
    ElMessage.success('已拒绝')
    loadData()
  } catch (e) {
    if (e !== 'cancel') {
      // handled by interceptor
    }
  }
}

function statusType(s) {
  return s === 'approved' ? 'success' : s === 'rejected' ? 'danger' : 'warning'
}

function statusText(s) {
  return s === 'approved' ? '已通过' : s === 'rejected' ? '已拒绝' : '待审核'
}

function formatTime(t) {
  if (!t) return ''
  return new Date(t).toLocaleString('zh-CN')
}

onMounted(loadData)
</script>

<style scoped>
.page {
  max-width: 900px;
}

.page-title {
  font-size: 24px;
  color: #E65100;
  font-weight: 700;
  margin-bottom: 24px;
}

.section-title {
  font-size: 18px;
  color: #333;
  margin-bottom: 16px;
}

.user-cards {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.user-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 20px;
  background: white;
  border-radius: 12px;
  border: 2px solid #eee;
}

.user-card.pending {
  border-color: #E65100;
  background: #FFF8F0;
}

.user-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: #E65100;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  font-weight: 700;
  flex-shrink: 0;
}

.user-info {
  flex: 1;
}

.user-name {
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.user-phone {
  font-size: 14px;
  color: #999;
  margin: 4px 0;
}

.user-actions {
  display: flex;
  gap: 8px;
}

.visible-mobile { display: none; }
.hidden-mobile { display: block; }
.card-list { display: flex; flex-direction: column; gap: 8px; }
.record-card {
  background: white; border-radius: 8px; padding: 12px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.08);
}
.card-main { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.card-title { font-size: 15px; font-weight: 600; color: #212121; }
.card-sub { font-size: 12px; color: #999; }
.card-info { display: flex; gap: 16px; font-size: 13px; color: #666; margin-bottom: 6px; flex-wrap: wrap; align-items: center; }
.card-actions { display: flex; gap: 8px; justify-content: flex-end; }

@media (max-width: 600px) {
  .visible-mobile { display: block; }
  .hidden-mobile { display: none; }
  .user-card {
    flex-wrap: wrap;
  }
  .user-actions {
    width: 100%;
  }
  .user-actions .el-button {
    flex: 1;
  }
}
</style>
