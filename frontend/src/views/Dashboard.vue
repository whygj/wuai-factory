<template>
  <div class="dashboard">
    <h2 class="page-title">仪表盘</h2>

    <!-- KPI Cards -->
    <el-row :gutter="16" class="kpi-row">
      <el-col :xs="12" :sm="6">
        <KpiCard label="原料种类" :value="data.material_count" icon="🧈" color="#E65100" />
      </el-col>
      <el-col :xs="12" :sm="6">
        <KpiCard label="产品种类" :value="data.product_count" icon="📦" color="#4CAF50" />
      </el-col>
      <el-col :xs="12" :sm="6">
        <KpiCard label="今日生产" :value="data.today_production" icon="🏭" color="#FF9800" />
      </el-col>
      <el-col :xs="12" :sm="6">
        <KpiCard label="待发货" :value="data.pending_shipments" icon="🚚" color="#F44336" />
      </el-col>
    </el-row>

    <!-- Alerts -->
    <AlertBar :alerts="data.alerts" class="alert-section" />

    <!-- Charts -->
    <el-row :gutter="16" class="charts-row">
      <el-col :xs="24" :sm="12">
        <el-card class="chart-card">
          <template #header>
            <span class="chart-title">原料库存分布</span>
          </template>
          <v-chart :option="pieOption" style="height: 320px" autoresize />
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12">
        <el-card class="chart-card">
          <template #header>
            <span class="chart-title">产品库存排行</span>
          </template>
          <v-chart :option="barOption" style="height: 320px" autoresize />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { PieChart, BarChart } from 'echarts/charts'
import { TitleComponent, TooltipComponent, LegendComponent, GridComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import KpiCard from '../components/KpiCard.vue'
import AlertBar from '../components/AlertBar.vue'
import { getDashboard, getMaterialDistribution, getProductRanking } from '../api'

use([PieChart, BarChart, TitleComponent, TooltipComponent, LegendComponent, GridComponent, CanvasRenderer])

const data = ref({
  material_count: 0,
  product_count: 0,
  today_production: 0,
  pending_shipments: 0,
  alerts: [],
})

const materialDist = ref([])
const productRank = ref([])

const pieOption = computed(() => ({
  tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
  color: ['#E65100', '#FF8A50', '#FFB74D', '#4CAF50', '#81C784', '#FF9800', '#FFD54F', '#F44336', '#EF5350', '#795548'],
  series: [{
    type: 'pie',
    radius: ['40%', '70%'],
    itemStyle: { borderRadius: 8 },
    label: { fontSize: 13 },
    data: materialDist.value,
  }],
}))

const barOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { left: 100, right: 20, top: 20, bottom: 40 },
  xAxis: { type: 'value' },
  yAxis: {
    type: 'category',
    data: productRank.value.map(p => p.name).reverse(),
    axisLabel: { fontSize: 13 },
  },
  series: [{
    type: 'bar',
    data: productRank.value.map(p => p.value).reverse(),
    itemStyle: {
      color: '#E65100',
      borderRadius: [0, 6, 6, 0],
    },
    barWidth: 22,
  }],
}))

onMounted(async () => {
  try {
    const [overview, dist, rank] = await Promise.all([
      getDashboard(),
      getMaterialDistribution(),
      getProductRanking(),
    ])
    data.value = overview
    materialDist.value = dist
    productRank.value = rank
  } catch (e) {}
})
</script>

<style scoped>
.page-title {
  font-size: 24px;
  font-weight: 700;
  color: var(--primary);
  margin-bottom: 20px;
}

.kpi-row {
  margin-bottom: 20px;
}

.kpi-row .el-col {
  margin-bottom: 12px;
}

.alert-section {
  margin-bottom: 20px;
}

.charts-row .el-col {
  margin-bottom: 16px;
}

.chart-card {
  height: 100%;
}

.chart-title {
  font-size: 16px;
  font-weight: 600;
}
</style>
