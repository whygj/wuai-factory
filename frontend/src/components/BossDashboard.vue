<template>
  <div class="boss-dashboard">
    <h2 class="page-title">经营总览</h2>

    <!-- Row 1: Core KPIs (4 cols) -->
    <el-row :gutter="16" class="kpi-row">
      <el-col :xs="12" :sm="12" :md="6">
        <KpiCard label="今日销售额" :value="'¥' + (data.today_sales || 0)" :icon="Money" color="#E65100" @click="$router.push('/sales-orders')" />
      </el-col>
      <el-col :xs="12" :sm="12" :md="6">
        <div class="kpi-with-change" @click="$router.push('/sales-orders')" style="cursor:pointer">
          <KpiCard label="本月销售额" :value="'¥' + (data.month_sales || 0)" :icon="TrendCharts" color="#E65100" />
          <span class="change-tag" :class="{ up: data.month_change > 0, down: data.month_change < 0 }">
            {{ data.month_change > 0 ? '↑' : '↓' }} {{ Math.abs(data.month_change || 0) }}%
          </span>
        </div>
      </el-col>
      <el-col :xs="12" :sm="12" :md="6">
        <KpiCard label="应收款总额" :value="'¥' + (data.receivables_total || 0)" :icon="Document" color="#F44336" @click="$router.push('/receivables')" />
      </el-col>
      <el-col :xs="12" :sm="12" :md="6">
        <div class="kpi-wrap" @click="$router.push('/receivables')" style="cursor:pointer">
          <KpiCard label="逾期应收款" :value="'¥' + (data.receivables_overdue || 0)" :icon="Warning" color="#D32F2F" />
          <span v-if="data.receivables_overdue > 0" class="overdue-hint">需关注</span>
        </div>
      </el-col>
    </el-row>

    <!-- Row 2: Operational KPIs + Quick Search (3 cols) -->
    <el-row :gutter="16" class="kpi-row">
      <el-col :xs="12" :sm="8">
        <KpiCard label="库存预警" :value="data.alert_count || 0" :icon="Box" color="#FF9800" @click="$router.push('/materials')" />
      </el-col>
      <el-col :xs="12" :sm="8">
        <KpiCard label="今日产量" :value="data.today_production || 0" :icon="OfficeBuilding" color="#4CAF50" @click="$router.push('/production/new')" />
      </el-col>
      <el-col :xs="24" :sm="8">
        <div class="quick-search-card">
          <el-input v-model="searchKeyword" placeholder="搜索客户/订单/产品..." size="large" @keyup.enter="doSearch" clearable class="search-input">
            <template #prefix><el-icon><Search /></el-icon></template>
          </el-input>
          <el-button type="primary" size="large" @click="doSearch" class="search-btn">查询</el-button>
        </div>
      </el-col>
    </el-row>

    <!-- Search Results Dialog -->
    <el-dialog v-model="showSearchResults" title="搜索结果" width="700px">
      <div v-if="searchResults.customers && searchResults.customers.length">
        <h4 class="result-heading">客户</h4>
        <el-table :data="searchResults.customers" size="small" @row-click="r => $router.push('/customers')" style="cursor:pointer; margin-bottom:16px;">
          <el-table-column prop="name" label="名称" /><el-table-column prop="phone" label="电话" /><el-table-column prop="type" label="类型" />
        </el-table>
      </div>
      <div v-if="searchResults.orders && searchResults.orders.length">
        <h4 class="result-heading">订单</h4>
        <el-table :data="searchResults.orders" size="small" @row-click="r => $router.push('/sales-orders')" style="cursor:pointer; margin-bottom:16px;">
          <el-table-column prop="order_no" label="订单号" /><el-table-column prop="customer_name" label="客户" /><el-table-column prop="total_amount" label="金额" /><el-table-column prop="status" label="状态" />
        </el-table>
      </div>
      <div v-if="searchResults.products && searchResults.products.length">
        <h4 class="result-heading">产品</h4>
        <el-table :data="searchResults.products" size="small" @row-click="r => $router.push('/products')" style="cursor:pointer; margin-bottom:16px;">
          <el-table-column prop="name" label="名称" /><el-table-column prop="stock" label="库存" /><el-table-column prop="unit" label="单位" />
        </el-table>
      </div>
      <div v-if="searchResults.suppliers && searchResults.suppliers.length">
        <h4 class="result-heading">供应商</h4>
        <el-table :data="searchResults.suppliers" size="small" @row-click="r => $router.push('/suppliers')" style="cursor:pointer; margin-bottom:16px;">
          <el-table-column prop="name" label="名称" /><el-table-column prop="phone" label="电话" /><el-table-column prop="category" label="类别" />
        </el-table>
      </div>
      <div v-if="hasNoResults" class="empty-text">未找到相关结果</div>
    </el-dialog>

    <!-- Row 3: Pending Items (2 cols) -->
    <el-row :gutter="16" class="pending-row">
      <el-col :xs="24" :sm="12">
        <el-card class="section-card" @click="$router.push('/sales-orders')" style="cursor:pointer">
          <template #header>
            <div class="section-header">
              <el-icon class="section-icon" style="color: #1976D2"><Van /></el-icon>
              <span class="section-title">待发货订单</span>
              <el-tag v-if="data.shipments_pending > 0" type="danger" size="small" round>{{ data.shipments_pending }}</el-tag>
            </div>
          </template>
          <div v-if="data.shipments_pending > 0" class="pending-count">{{ data.shipments_pending }} 笔待发货</div>
          <div v-else class="empty-text">暂无待发货订单</div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12">
        <el-card class="section-card" @click="$router.push('/users')" style="cursor:pointer">
          <template #header>
            <div class="section-header">
              <el-icon class="section-icon" style="color: #7B1FA2"><User /></el-icon>
              <span class="section-title">待审核用户</span>
              <el-tag v-if="data.pending_users > 0" type="warning" size="small" round>{{ data.pending_users }}</el-tag>
            </div>
          </template>
          <div v-if="data.pending_users > 0" class="pending-count">{{ data.pending_users }} 人待审核</div>
          <div v-else class="empty-text">暂无待审核用户</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Row 4: Charts (2 cols: 14+10) -->
    <el-row :gutter="16" class="charts-row">
      <el-col :xs="24" :md="14">
        <el-card class="chart-card">
          <template #header><span class="chart-title">近30天销售趋势</span></template>
          <v-chart :option="salesTrendOption" style="height: 360px" autoresize />
        </el-card>
      </el-col>
      <el-col :xs="24" :md="10">
        <el-card class="chart-card">
          <template #header><span class="chart-title">本月客户TOP5</span></template>
          <v-chart :option="customerTop5Option" style="height: 360px" autoresize />
        </el-card>
      </el-col>
    </el-row>

    <!-- Row 5: Product TOP5 (full width) -->
    <el-row :gutter="16" style="margin-top: 16px;">
      <el-col :span="24">
        <el-card class="chart-card">
          <template #header><span class="chart-title">本月产品销量TOP5</span></template>
          <v-chart :option="productTop5Option" style="height: 280px" autoresize />
        </el-card>
      </el-col>
    </el-row>

    <!-- Row 6: Bottom info (2 cols) -->
    <el-row :gutter="16" class="bottom-row">
      <el-col :xs="24" :sm="12">
        <el-card v-if="data.alerts && data.alerts.length" class="section-card">
          <template #header>
            <div class="section-header">
              <el-icon class="section-icon" style="color: #F44336"><Warning /></el-icon>
              <span class="chart-title" style="color:#F44336">库存预警 ({{ data.alerts.length }})</span>
            </div>
          </template>
          <div v-for="a in data.alerts" :key="a.id" class="alert-item">
            <span class="alert-name">{{ a.name }}</span>
            <span class="alert-value">{{ a.current }} / {{ a.safety }} {{ a.unit }}</span>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12">
        <el-card v-if="expiring.length" class="section-card" @click="$router.push('/batch-trace')" style="cursor:pointer">
          <template #header>
            <div class="section-header">
              <el-icon class="section-icon" style="color: #FF9800"><Warning /></el-icon>
              <span class="chart-title" style="color:#FF9800">原料临期 ({{ expiring.length }})</span>
            </div>
          </template>
          <div v-for="e in expiring" :key="e.id" class="alert-item">
            <span class="alert-name">{{ e.material_name }} {{ e.batch_no }}</span>
            <span class="alert-value" :style="{ color: e.expired || e.remain_days <= 7 ? '#C62828' : '#FF9800', fontWeight: 700 }">
              {{ e.expired ? '已过期' + (-e.remain_days) + '天' : '剩' + e.remain_days + '天' }} / 余{{ e.quantity_remaining }}{{ e.unit }}
            </span>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12">
        <el-card class="section-card">
          <template #header>
            <div class="section-header">
              <el-icon class="section-icon" style="color: #E65100"><TrendCharts /></el-icon>
              <span class="chart-title">今日动态</span>
            </div>
          </template>
          <div v-if="data.today_activities && data.today_activities.length">
            <div v-for="(act, idx) in data.today_activities" :key="idx" class="activity-item">
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
import { Money, TrendCharts, Document, Warning, Box, OfficeBuilding, Search, Van, User } from '@element-plus/icons-vue'
import KpiCard from './KpiCard.vue'
import { getBossDashboardExtended, quickSearch, getExpiringBatches } from '../api'

use([LineChart, BarChart, TitleComponent, TooltipComponent, GridComponent, CanvasRenderer])

const data = ref({
  month_sales: 0, last_month_sales: 0, month_change: 0,
  today_sales: 0, receivables_total: 0, receivables_overdue: 0,
  alert_count: 0, pending_users: 0, shipments_pending: 0, today_production: 0,
  customer_top5: [], products_top5: [], customers_active: [],
  alerts: [], sales_trend: [], today_activities: [],
})

const searchKeyword = ref('')
const showSearchResults = ref(false)
const searchResults = ref({ customers: [], orders: [], products: [], suppliers: [] })
const expiring = ref([])
const hasNoResults = computed(() => {
  const r = searchResults.value
  return (!r.customers || !r.customers.length) && (!r.orders || !r.orders.length) &&
    (!r.products || !r.products.length) && (!r.suppliers || !r.suppliers.length)
})

async function doSearch() {
  if (!searchKeyword.value.trim()) return
  try {
    searchResults.value = await quickSearch({ keyword: searchKeyword.value.trim() })
    showSearchResults.value = true
  } catch (e) {}
}

const chartBg = '#FFF3E0'
const primaryColor = '#E65100'

const salesTrendOption = computed(() => ({
  tooltip: { trigger: 'axis', backgroundColor: '#fff', borderColor: primaryColor, borderWidth: 1 },
  grid: { left: 64, right: 24, top: 24, bottom: 40 },
  xAxis: { type: 'category', data: data.value.sales_trend.map(r => r.date.slice(5)), axisLabel: { fontSize: 12, color: '#757575' }, axisLine: { lineStyle: { color: '#E0E0E0' } } },
  yAxis: { type: 'value', axisLabel: { fontSize: 12, color: '#757575' }, splitLine: { lineStyle: { color: '#F5F5F5' } } },
  series: [{
    type: 'line', smooth: true, data: data.value.sales_trend.map(r => r.amount),
    areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: 'rgba(230,81,0,0.25)' }, { offset: 1, color: 'rgba(230,81,0,0.02)' }] } },
    lineStyle: { color: primaryColor, width: 3 },
    itemStyle: { color: primaryColor },
    symbolSize: 6,
  }],
}))

const customerTop5Option = computed(() => ({
  tooltip: { trigger: 'axis', backgroundColor: '#fff', borderColor: primaryColor, borderWidth: 1 },
  grid: { left: 100, right: 24, top: 24, bottom: 24 },
  xAxis: { type: 'value', axisLabel: { color: '#757575' }, splitLine: { lineStyle: { color: '#F5F5F5' } } },
  yAxis: { type: 'category', data: data.value.customer_top5.map(r => r.name).reverse(), axisLabel: { fontSize: 13, color: '#212121' } },
  series: [{
    type: 'bar', data: data.value.customer_top5.map(r => r.amount).reverse(),
    itemStyle: { color: primaryColor, borderRadius: [0, 6, 6, 0] }, barWidth: 22,
  }],
}))

const productTop5Option = computed(() => ({
  tooltip: { trigger: 'axis', backgroundColor: '#fff', borderColor: '#FF8A50', borderWidth: 1 },
  grid: { left: 120, right: 24, top: 24, bottom: 24 },
  xAxis: { type: 'value', axisLabel: { color: '#757575' }, splitLine: { lineStyle: { color: '#F5F5F5' } } },
  yAxis: { type: 'category', data: data.value.products_top5.map(r => r.name).reverse(), axisLabel: { fontSize: 13, color: '#212121' } },
  series: [{
    type: 'bar', data: data.value.products_top5.map(r => r.quantity).reverse(),
    itemStyle: { color: '#FF8A50', borderRadius: [0, 6, 6, 0] }, barWidth: 20,
  }],
}))

function actTagType(type) {
  if (type === '采购入库') return 'warning'
  if (type === '生产') return 'success'
  if (type === '销售') return 'danger'
  return 'info'
}

onMounted(async () => {
  try { data.value = await getBossDashboardExtended() } catch (e) {}
  try { expiring.value = await getExpiringBatches(30) } catch (e) {}
})
</script>

<style scoped>
.boss-dashboard {
  max-width: 1200px;
}

.page-title {
  font-family: 'Noto Sans SC', sans-serif;
  font-size: 24px;
  font-weight: 700;
  color: var(--primary);
  margin-bottom: 24px;
}

/* KPI rows */
.kpi-row {
  margin-bottom: 16px;
}
.kpi-row .el-col {
  margin-bottom: 8px;
}

/* Change tag on month sales */
.kpi-with-change {
  position: relative;
}
.change-tag {
  position: absolute;
  top: 8px;
  right: 8px;
  font-family: 'Inter', sans-serif;
  font-size: 12px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 10px;
  background: #f5f5f5;
  color: #999;
}
.change-tag.up {
  color: #4CAF50;
  background: #E8F5E9;
}
.change-tag.down {
  color: #F44336;
  background: #FFEBEE;
}

/* Overdue hint */
.kpi-wrap {
  position: relative;
}
.overdue-hint {
  position: absolute;
  top: 8px;
  right: 8px;
  font-size: 12px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 10px;
  color: #D32F2F;
  background: #FFEBEE;
}

/* Quick search */
.quick-search-card {
  background: linear-gradient(135deg, #FFF3E0 0%, #FFFFFF 100%);
  border-radius: 12px;
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
  height: 100%;
  min-height: 88px;
  box-shadow: var(--shadow-sm);
}
.search-input {
  flex: 1;
}
.search-input :deep(.el-input__wrapper) {
  border-radius: 8px;
}
.search-btn {
  flex-shrink: 0;
}

/* Pending row */
.pending-row {
  margin-bottom: 16px;
}
.pending-row .el-col {
  margin-bottom: 8px;
}
.section-card {
  height: 100%;
}
.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
}
.section-icon {
  font-size: 20px;
}
.section-title {
  font-size: 16px;
  font-weight: 600;
  flex: 1;
}
.pending-count {
  font-family: 'Inter', sans-serif;
  font-size: 20px;
  font-weight: 700;
  color: var(--text);
  text-align: center;
  padding: 16px 0;
}

/* Charts */
.charts-row .el-col,
.bottom-row .el-col {
  margin-bottom: 16px;
}
.chart-card {
  height: 100%;
  background: #FFF3E0;
}
.chart-card :deep(.el-card__header) {
  padding: 16px 20px 8px;
  border-bottom: none;
}
.chart-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--primary);
}

/* Alerts */
.alert-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid #FFE0B2;
  font-size: 15px;
}
.alert-item:last-child {
  border-bottom: none;
}
.alert-name {
  font-weight: 600;
  color: #F44336;
}
.alert-value {
  color: var(--text-secondary);
}

/* Activities */
.activity-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 0;
  border-bottom: 1px solid #FFE0B2;
  font-size: 14px;
}
.activity-item:last-child {
  border-bottom: none;
}
.act-time {
  color: var(--text-secondary);
  font-size: 13px;
  min-width: 44px;
  font-family: 'Inter', sans-serif;
}
.act-tag {
  flex-shrink: 0;
}
.act-desc {
  flex: 1;
}

/* Search results */
.result-heading {
  font-size: 16px;
  font-weight: 600;
  color: var(--primary);
  margin-bottom: 8px;
}

.empty-text {
  color: var(--text-light);
  text-align: center;
  padding: 20px;
  font-size: 15px;
}
</style>
