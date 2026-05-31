<template>
  <div class="boss-dashboard">
    <h2 class="page-title">经营总览</h2>

    <el-row :gutter="16" class="kpi-row">
      <el-col :xs="12" :sm="6">
        <KpiCard label="本月销售额" :value="'¥' + (data.month_sales || 0)" icon="💰" color="#E65100" />
      </el-col>
      <el-col :xs="12" :sm="6">
        <KpiCard label="应收款" :value="'¥' + (data.receivables || 0)" icon="📋" color="#F44336" />
      </el-col>
      <el-col :xs="12" :sm="6">
        <KpiCard label="库存预警" :value="data.alert_count || 0" icon="⚠️" color="#FF9800" />
      </el-col>
      <el-col :xs="12" :sm="6">
        <KpiCard label="今日产量" :value="data.today_production || 0" icon="🏭" color="#4CAF50" />
      </el-col>
    </el-row>

    <el-row :gutter="16" class="charts-row">
      <el-col :xs="24" :sm="14">
        <el-card class="chart-card">
          <template #header><span class="chart-title">近30天销售趋势</span></template>
          <v-chart :option="salesTrendOption" style="height: 320px" autoresize />
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="10">
        <el-card class="chart-card">
          <template #header><span class="chart-title">本月客户TOP5</span></template>
          <v-chart :option="customerTop5Option" style="height: 320px" autoresize />
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" class="bottom-row">
      <el-col :xs="24" :sm="12">
        <el-card v-if="data.alerts && data.alerts.length" class="alert-card">
          <template #header><span class="chart-title" style="color:#F44336">⚠️ 库存预警</span></template>
          <div v-for="a in data.alerts" :key="a.id" class="alert-item">
            <span class="alert-name">{{ a.name }}</span>
            <span class="alert-value">{{ a.current }} / {{ a.safety }} {{ a.unit }}</span>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12">
        <el-card class="activity-card">
          <template #header><span class="chart-title">今日动态</span></template>
          <div v-if="data.today_activities && data.today_activities.length">
            <div v-for="(act, idx) in data.today_activities" :key="idx" class="activity-item">
              <span class="act-icon">{{ act.icon }}</span>
              <span class="act-time">{{ act.time }}</span>
              <el-tag size="small" :type="actTagType(act.type)" class="act-tag">{{ act.type }}</el-tag>
              <span class="act-desc">{{ act.desc }}</span>
            </div>
          </div>
          <div v-else class="empty-text">今日暂无动态</div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { LineChart, BarChart } from 'echarts/charts'
import { TitleComponent, TooltipComponent, GridComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import KpiCard from './KpiCard.vue'
import { getBossDashboard } from '../api'

use([LineChart, BarChart, TitleComponent, TooltipComponent, GridComponent, CanvasRenderer])

const data = ref({ month_sales: 0, receivables: 0, alert_count: 0, today_production: 0, customer_top5: [], alerts: [], sales_trend: [], today_activities: [] })

const salesTrendOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { left: 60, right: 20, top: 20, bottom: 40 },
  xAxis: { type: 'category', data: data.value.sales_trend.map(r => r.date.slice(5)), axisLabel: { fontSize: 12 } },
  yAxis: { type: 'value', axisLabel: { fontSize: 12 } },
  series: [{
    type: 'line', smooth: true, data: data.value.sales_trend.map(r => r.amount),
    areaStyle: { color: 'rgba(230,81,0,0.15)' },
    lineStyle: { color: '#E65100', width: 3 },
    itemStyle: { color: '#E65100' },
  }],
}))

const customerTop5Option = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { left: 100, right: 20, top: 20, bottom: 20 },
  xAxis: { type: 'value' },
  yAxis: { type: 'category', data: data.value.customer_top5.map(r => r.name).reverse(), axisLabel: { fontSize: 13 } },
  series: [{
    type: 'bar', data: data.value.customer_top5.map(r => r.amount).reverse(),
    itemStyle: { color: '#E65100', borderRadius: [0, 6, 6, 0] }, barWidth: 22,
  }],
}))

function actTagType(type) {
  if (type === '采购入库') return 'warning'
  if (type === '生产') return 'success'
  if (type === '销售') return 'danger'
  return 'info'
}

onMounted(async () => {
  try { data.value = await getBossDashboard() } catch (e) {}
})
</script>

<style scoped>
.page-title { font-size: 24px; font-weight: 700; color: var(--primary); margin-bottom: 20px; }
.kpi-row { margin-bottom: 20px; }
.kpi-row .el-col { margin-bottom: 12px; }
.charts-row .el-col, .bottom-row .el-col { margin-bottom: 16px; }
.chart-card, .alert-card, .activity-card { height: 100%; }
.chart-title { font-size: 16px; font-weight: 600; }
.alert-item { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #f0f0f0; font-size: 15px; }
.alert-item:last-child { border-bottom: none; }
.alert-name { font-weight: 600; color: #F44336; }
.alert-value { color: #999; }
.activity-item { display: flex; align-items: center; gap: 8px; padding: 8px 0; border-bottom: 1px solid #f0f0f0; font-size: 14px; }
.activity-item:last-child { border-bottom: none; }
.act-icon { font-size: 18px; }
.act-time { color: #999; font-size: 13px; min-width: 44px; }
.act-tag { flex-shrink: 0; }
.act-desc { flex: 1; }
.empty-text { color: #999; text-align: center; padding: 20px; font-size: 15px; }
</style>
