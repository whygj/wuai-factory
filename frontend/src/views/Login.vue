<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-header">
        <h1>五爱食品工厂</h1>
        <p>管理系统</p>
      </div>

      <!-- Login Form -->
      <el-form v-if="step === 'login'" @submit.prevent="handleSendCode" class="login-form">
        <el-form-item>
          <el-input v-model="phone" type="tel" placeholder="请输入手机号" size="large" maxlength="11">
            <template #prefix><span style="font-size: 18px;">📱</span></template>
          </el-input>
        </el-form-item>
        <el-form-item>
          <div style="display: flex; gap: 10px; width: 100%;">
            <el-input v-model="code" type="text" placeholder="验证码" size="large" maxlength="6" style="flex: 1;">
              <template #prefix><span style="font-size: 18px;">🔑</span></template>
            </el-input>
            <el-button size="large" :disabled="countdown > 0" @click="handleSendCode" style="min-width: 120px;">
              {{ countdown > 0 ? `${countdown}s` : '获取验证码' }}
            </el-button>
          </div>
        </el-form-item>
        <el-button type="primary" size="large" :loading="loading" @click="handleLogin" style="width: 100%; height: 48px; font-size: 18px;">
          登 录
        </el-button>
        <div class="dev-hint" v-if="devHint">开发模式：验证码 123456</div>
      </el-form>

      <!-- Register Form -->
      <div v-if="step === 'register'" class="register-form">
        <h3 style="text-align: center; color: #E65100; margin-bottom: 20px;">新用户注册</h3>
        <div class="phone-display">手机号：{{ phone }}</div>
        <el-form @submit.prevent="handleRegister">
          <el-form-item>
            <el-input v-model="displayName" placeholder="请输入您的姓名" size="large">
              <template #prefix><span style="font-size: 18px;">👤</span></template>
            </el-input>
          </el-form-item>
          <div class="role-select">
            <p style="margin-bottom: 12px; color: #666;">选择您的身份：</p>
            <div class="role-cards">
              <div class="role-card" :class="{ active: selectedRole === 'boss' }" @click="selectedRole = 'boss'">
                <div class="role-icon">👔</div>
                <div class="role-name">老板</div>
                <div class="role-desc">全面管理</div>
              </div>
              <div class="role-card" :class="{ active: selectedRole === 'clerk' }" @click="selectedRole = 'clerk'">
                <div class="role-icon">📋</div>
                <div class="role-name">内勤</div>
                <div class="role-desc">销售/采购</div>
              </div>
              <div class="role-card" :class="{ active: selectedRole === 'leader' }" @click="selectedRole = 'leader'">
                <div class="role-icon">👷</div>
                <div class="role-name">班长</div>
                <div class="role-desc">生产/试验</div>
              </div>
            </div>
          </div>
          <el-button type="primary" size="large" :loading="loading" @click="handleRegister" style="width: 100%; height: 48px; font-size: 18px; margin-top: 16px;">
            提交注册
          </el-button>
          <el-button size="large" @click="step = 'login'" style="width: 100%; margin-top: 8px;">
            返回登录
          </el-button>
        </el-form>
      </div>

      <!-- Pending Status -->
      <div v-if="step === 'pending'" class="pending-box">
        <div style="text-align: center;">
          <div style="font-size: 48px; margin-bottom: 16px;">⏳</div>
          <h3 style="color: #E65100;">注册成功！</h3>
          <p style="color: #666; margin-top: 8px;">请等待管理员审核通过后即可登录</p>
          <el-button type="primary" size="large" @click="resetForm" style="margin-top: 24px; width: 100%; height: 48px;">
            返回登录
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { sendVerifyCode, loginWithCode, register } from '../api'
import { ElMessage } from 'element-plus'

const router = useRouter()
const loading = ref(false)
const phone = ref('')
const code = ref('')
const countdown = ref(0)
const devHint = ref(false)
const step = ref('login') // login / register / pending
const displayName = ref('')
const selectedRole = ref('clerk')
let timer = null

function startCountdown() {
  countdown.value = 60
  timer = setInterval(() => {
    countdown.value--
    if (countdown.value <= 0) clearInterval(timer)
  }, 1000)
}

async function handleSendCode() {
  if (!phone.value || phone.value.length !== 11) {
    ElMessage.warning('请输入正确的手机号')
    return
  }
  try {
    const res = await sendVerifyCode({ phone: phone.value })
    startCountdown()
    if (res.msg && res.msg.includes('开发模式')) {
      devHint.value = true
    }
    ElMessage.success(res.msg || '验证码已发送')
  } catch (e) {
    // handled by interceptor
  }
}

async function handleLogin() {
  if (!phone.value || !code.value) {
    ElMessage.warning('请输入手机号和验证码')
    return
  }
  loading.value = true
  try {
    const res = await loginWithCode({ phone: phone.value, code: code.value })
    localStorage.setItem('token', res.access_token)
    localStorage.setItem('displayName', res.display_name)
    localStorage.setItem('userRoles', JSON.stringify(res.roles))
    ElMessage.success('登录成功')
    if (res.roles.length > 1) {
      router.push('/select-role')
    } else {
      localStorage.setItem('currentRole', res.roles[0])
      router.push('/')
    }
  } catch (e) {
    const status = e.response?.status
    const detail = e.response?.data?.detail || ''
    if (status === 404 && detail.includes('未注册')) {
      step.value = 'register'
    } else if (status === 403 && detail.includes('待审核')) {
      step.value = 'pending'
    }
  } finally {
    loading.value = false
  }
}

async function handleRegister() {
  if (!displayName.value) {
    ElMessage.warning('请输入您的姓名')
    return
  }
  if (!selectedRole.value) {
    ElMessage.warning('请选择身份')
    return
  }
  loading.value = true
  try {
    await register({
      phone: phone.value,
      code: code.value,
      display_name: displayName.value,
      role: selectedRole.value,
    })
    ElMessage.success('注册成功，请等待管理员审核')
    step.value = 'pending'
  } catch (e) {
    // handled by interceptor
  } finally {
    loading.value = false
  }
}

function resetForm() {
  phone.value = ''
  code.value = ''
  displayName.value = ''
  selectedRole.value = 'clerk'
  step.value = 'login'
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
  width: 420px;
  max-width: 90vw;
  box-shadow: 0 20px 60px rgba(0,0,0,0.15);
}

.login-header {
  text-align: center;
  margin-bottom: 36px;
}

.login-header h1 {
  font-size: 28px;
  color: #E65100;
  font-weight: 800;
}

.login-header p {
  color: #999;
  font-size: 16px;
  margin-top: 4px;
}

.login-form :deep(.el-input__wrapper) {
  height: 48px;
  border-radius: 10px;
}

.dev-hint {
  text-align: center;
  margin-top: 12px;
  color: #E65100;
  font-size: 14px;
  background: #FFF3E0;
  padding: 8px;
  border-radius: 8px;
}

.register-form :deep(.el-input__wrapper) {
  height: 48px;
  border-radius: 10px;
}

.phone-display {
  text-align: center;
  color: #666;
  font-size: 16px;
  margin-bottom: 20px;
  background: #FFF3E0;
  padding: 10px;
  border-radius: 8px;
}

.role-select {
  margin-bottom: 8px;
}

.role-cards {
  display: flex;
  gap: 10px;
}

.role-card {
  flex: 1;
  text-align: center;
  padding: 16px 8px;
  border: 2px solid #eee;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.role-card:hover {
  border-color: #FF8A50;
}

.role-card.active {
  border-color: #E65100;
  background: #FFF3E0;
}

.role-icon {
  font-size: 28px;
  margin-bottom: 6px;
}

.role-name {
  font-size: 16px;
  font-weight: 700;
  color: #333;
}

.role-desc {
  font-size: 12px;
  color: #999;
  margin-top: 2px;
}

.pending-box {
  padding: 20px 0;
}
</style>
