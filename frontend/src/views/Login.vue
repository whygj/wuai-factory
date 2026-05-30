<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-header">
        <h1>五爱食品工厂</h1>
        <p>管理系统</p>
      </div>
      <el-form :model="form" @submit.prevent="handleLogin" class="login-form">
        <el-form-item>
          <el-input v-model="form.username" placeholder="用户名" size="large" prefix-icon="User" />
        </el-form-item>
        <el-form-item>
          <el-input v-model="form.password" type="password" placeholder="密码" size="large" prefix-icon="Lock" show-password />
        </el-form-item>
        <el-button type="primary" size="large" :loading="loading" @click="handleLogin" style="width: 100%; height: 48px; font-size: 18px;">
          登 录
        </el-button>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { login, getMe } from '../api'
import { ElMessage } from 'element-plus'

const router = useRouter()
const loading = ref(false)
const form = ref({ username: '', password: '' })

async function handleLogin() {
  if (!form.value.username || !form.value.password) {
    ElMessage.warning('请输入用户名和密码')
    return
  }
  loading.value = true
  try {
    const res = await login(form.value)
    localStorage.setItem('token', res.access_token)
    const user = await getMe()
    localStorage.setItem('displayName', user.display_name || user.username)
    ElMessage.success('登录成功')
    router.push('/')
  } catch (e) {
    // handled by interceptor
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #E65100 0%, #FF8A50 50%, #FFF3E0 100%);
}

.login-card {
  background: white;
  border-radius: 20px;
  padding: 48px 40px;
  width: 400px;
  max-width: 90vw;
  box-shadow: 0 20px 60px rgba(0,0,0,0.15);
}

.login-header {
  text-align: center;
  margin-bottom: 36px;
}

.login-header h1 {
  font-size: 28px;
  color: var(--primary);
  font-weight: 800;
}

.login-header p {
  color: var(--text-light);
  font-size: 16px;
  margin-top: 4px;
}

.login-form :deep(.el-input__wrapper) {
  height: 48px;
  border-radius: 10px;
}
</style>
