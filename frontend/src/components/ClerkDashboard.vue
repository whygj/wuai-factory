<template>
  <div class="clerk-dashboard">
    <h2 class="page-title">今日待办</h2>

    <el-row :gutter="16" class="kpi-row">
      <el-col :xs="12" :sm="6">
        <router-link to="/sales-orders" class="kpi-link">
          <KpiCard label="待发货" :value="data.pending_shipments || 0" icon="🚚" color="#E65100" />
        </router-link>
      </el-col>
      <el-col :xs="12" :sm="6">
        <router-link to="/purchases" class="kpi-link">
          <KpiCard label="待入库" :value="data.pending_inbound || 0" icon="📦" color="#FF9800" />
        </router-link>
      </el-col>
      <el-col :xs="12" :sm="6">
        <router-link to="/materials" class="kpi-link">
          <KpiCard label="库存预警" :value="data.alerts ? data.alerts.length : 0" icon="⚠️" color="#F44336" />
        </router-link>
      </el-col>
      <el-col :xs="12" :sm="6">
        <KpiCard label="今日销售" :value="'¥' + (data.today_sales || 0)" icon="💰" color="#4CAF50" />
      </el-col>
    </el-row>

    <el-card v-if="data.alerts && data.alerts.length" class="alert-card">
      <template #header><span class="card-title" style="color:#F44336">⚠️ 库存预警</span></template>
      <div v-for="a in data.alerts" :key="a.id" class="alert-item">
        <span class="alert-name">{{ a.name }}</span>
        <span class="alert-value">当前 {{ a.current }} / 安全 {{ a.safety }} {{ a.unit }}</span>
      </div>
    </el-card>

    <el-card v-else class="ok-card">
      <div class="ok-text">✅ 库存状态良好，无预警</div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import KpiCard from './KpiCard.vue'
import { getClerkDashboard } from '../api'

const data = ref({ pending_shipments: 0, pending_inbound: 0, alerts: [], today_sales: 0 })

onMounted(async () => {
  try { data.value = await getClerkDashboard() } catch (e) {}
})
</script>

<style scoped>
.page-title { font-size: 24px; font-weight: 700; color: var(--primary); margin-bottom: 20px; }
.kpi-row { margin-bottom: 20px; }
.kpi-row .el-col { margin-bottom: 12px; }
.kpi-link { text-decoration: none; display: block; }
.alert-card { margin-top: 16px; }
.card-title { font-size: 16px; font-weight: 600; }
.alert-item { display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #f0f0f0; font-size: 15px; }
.alert-item:last-child { border-bottom: none; }
.alert-name { font-weight: 600; color: #F44336; }
.alert-value { color: #999; }
.ok-card { margin-top: 16px; }
.ok-text { text-align: center; padding: 30px; font-size: 18px; color: #4CAF50; }
</style>
