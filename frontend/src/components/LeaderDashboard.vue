<template>
  <div class="leader-dashboard">
    <h2 class="page-title">生产面板</h2>

    <el-row :gutter="16" class="kpi-row">
      <el-col :xs="12" :sm="8">
        <KpiCard label="今日产量" :value="data.today_quantity || 0" icon="🏭" color="#E65100" />
      </el-col>
      <el-col :xs="12" :sm="8">
        <KpiCard label="今日登记" :value="data.today_records || 0" icon="📋" color="#4CAF50" />
      </el-col>
      <el-col :xs="24" :sm="8">
        <router-link to="/production/new" class="action-btn-link">
          <el-button type="primary" size="large" class="action-btn">+ 登记生产</el-button>
        </router-link>
      </el-col>
    </el-row>

    <el-row :gutter="16" class="charts-row">
      <el-col :xs="24" :sm="14">
        <el-card class="chart-card">
          <template #header><span class="chart-title">近7天产量趋势</span></template>
          <v-chart :option="trendOption" style="height: 300px" autoresize />
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="10">
        <el-card class="material-card">
          <template #header><span class="chart-title">原料状态</span></template>
          <el-table :data="data.material_status" size="small" stripe>
            <el-table-column prop="name" label="原料" />
            <el-table-column label="库存/安全" width="110">
              <template #default="{ row }">
                <span :class="{ 'low-text': row.ratio <= 1 }">{{ row.current }}/{{ row.safety }}</span>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { LineChart } from 'echarts/charts'
import { TitleComponent, TooltipComponent, GridComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import KpiCard from './KpiCard.vue'
import { getLeaderDashboard } from '../api'

use([LineChart, TitleComponent, TooltipComponent, GridComponent, CanvasRenderer])

const data = ref({ today_quantity: 0, today_records: 0, trend: [], material_status: [] })

const trendOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { left: 50, right: 20, top: 20, bottom: 40 },
  xAxis: { type: 'category', data: data.value.trend.map(r => r.date.slice(5)), axisLabel: { fontSize: 13 } },
  yAxis: { type: 'value', axisLabel: { fontSize: 12 } },
  series: [{
    type: 'line', smooth: true, data: data.value.trend.map(r => r.quantity),
    areaStyle: { color: 'rgba(76,175,80,0.15)' },
    lineStyle: { color: '#4CAF50', width: 3 },
    itemStyle: { color: '#4CAF50' },
  }],
}))

onMounted(async () => {
  try { data.value = await getLeaderDashboard() } catch (e) {}
})
</script>

<style scoped>
.page-title { font-size: 24px; font-weight: 700; color: var(--primary); margin-bottom: 20px; }
.kpi-row { margin-bottom: 20px; }
.kpi-row .el-col { margin-bottom: 12px; }
.charts-row .el-col { margin-bottom: 16px; }
.chart-card, .material-card { height: 100%; }
.chart-title { font-size: 16px; font-weight: 600; }
.action-btn-link { text-decoration: none; display: flex; align-items: center; justify-content: center; height: 100%; }
.action-btn { height: 56px; font-size: 20px; font-weight: 700; border-radius: 12px; width: 100%; max-width: 240px; }
.low-text { color: #F44336; font-weight: 700; }
</style>
