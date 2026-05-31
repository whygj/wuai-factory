<template>
  <div class="role-select-page">
    <div class="role-select-card">
      <h2>请选择角色</h2>
      <p class="subtitle">选择您当前要使用的身份</p>
      <div class="role-cards">
        <div
          v-for="role in roles"
          :key="role.key"
          class="role-card"
          :class="{ loading: loading }"
          @click="selectRole(role.key)"
        >
          <span class="role-icon">{{ role.icon }}</span>
          <span class="role-name">{{ role.label }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { selectRoleApi } from '../api'
import { ElMessage } from 'element-plus'

const router = useRouter()
const loading = ref(false)

const roleMap = {
  boss: { icon: '👔', label: '老板' },
  clerk: { icon: '📋', label: '内勤' },
  leader: { icon: '🏭', label: '班长' },
}

const roles = computed(() => {
  const saved = JSON.parse(localStorage.getItem('userRoles') || '[]')
  return saved.map(r => ({
    key: r,
    icon: roleMap[r]?.icon || '👤',
    label: roleMap[r]?.label || r,
  }))
})

async function selectRole(role) {
  loading.value = true
  try {
    const res = await selectRoleApi({ role })
    localStorage.setItem('token', res.access_token)
    localStorage.setItem('currentRole', role)
    localStorage.setItem('displayName', res.display_name)
    ElMessage.success('已切换角色')
    router.push('/')
  } catch (e) {
    // handled by interceptor
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.role-select-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #E65100 0%, #FF8A50 50%, #FFF3E0 100%);
}

.role-select-card {
  background: white;
  border-radius: 20px;
  padding: 48px 40px;
  width: 420px;
  max-width: 90vw;
  box-shadow: 0 20px 60px rgba(0,0,0,0.15);
  text-align: center;
}

.role-select-card h2 {
  font-size: 24px;
  color: #333;
  font-weight: 700;
  margin-bottom: 8px;
}

.subtitle {
  color: #999;
  font-size: 14px;
  margin-bottom: 32px;
}

.role-cards {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.role-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px 24px;
  border: 2px solid #FFF3E0;
  border-radius: 14px;
  cursor: pointer;
  transition: all 0.2s;
  background: #FFFBF5;
}

.role-card:hover {
  border-color: #E65100;
  background: #FFF3E0;
  transform: translateY(-2px);
}

.role-card.loading {
  pointer-events: none;
  opacity: 0.6;
}

.role-icon {
  font-size: 36px;
}

.role-name {
  font-size: 20px;
  font-weight: 600;
  color: #333;
}
</style>
