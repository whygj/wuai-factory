<template>
  <div class="boss-dashboard">
    <h2 class="page-title">经营总览</h2>

    <!-- KPI Cards Row 1 -->
    <el-row :gutter="16" class="kpi-row">
      <el-col :xs="12" :sm="8" :md="4">
        <KpiCard label="今日销售额" :value="'¥' + (data.today_sales || 0)" icon="💰" color="#E65100" @click="$router.push('/sales-orders')" style="cursor:pointer" />
      </el-col>
      <el-col :xs="12" :sm="8" :md="4">
        <div class="kpi-with-change" @click="$router.push('/sales-orders')" style="cursor:pointer">
          <KpiCard label="本月销售额" :value="'¥' + (data.month_sales || 0)" icon="📊" color="#E65100" />
          <span class="change-tag" :class="{ up: data.month_change > 0, down: data.month_change < 0 }">
            {{ data.month_change > 0 ? '↑' : '↓' }} {{ Math.abs(data.month_change || 0) }}%
          </span>
        </div>
      </el-col>
      <el-col :xs="12" :sm="8" :md="4">
        <KpiCard label="应收款总额" :value="'¥' + (data.receivables_total || 0)" icon="📋" color="#F44336" @click="$router.push('/receivables')" style="cursor:pointer" />
      </el-col>
      <el-col :xs="12" :sm="8" :md="4">
        <div class="kpi-wrap" @click="$router.push('/receivables')" style="cursor:pointer">
          <KpiCard label="逾期应收款" :value="'¥' + (data.receivables_overdue || 0)" icon="⚠️" color="#D32F2F" />
          <span v-if="data.receivables_overdue > 0" class="overdue-hint">需关注</span>
        </div>
      </el-col>
      <el-col :xs="12" :sm="8" :md="4">
        <KpiCard label="库存预警" :value="data.alert_count || 0" icon="📦" color="#FF9800" @click="$router.push('/materials')" style="cursor:pointer" />
      </el-col>
      <el-col :xs="12" :sm="8" :md="4">
        <KpiCard label="今日产量" :value="data.today_production || 0" icon="🏭" color="#4CAF50" @click="$router.push('/production/new')" style="cursor:pointer" />
      </el-col>
    </el-row>

    <!-- KPI Cards Row 2 -->
    <el-row :gutter="16" class="kpi-row">
      <el-col :xs="12" :sm="8">
        <KpiCard label="待发货订单" :value="data.shipments_pending || 0" icon="🚚" color="#1976D2" @click="$router.push('/sales-orders')" style="cursor:pointer" />
      </el-col>
      <el-col :xs="12" :sm="8">
        <KpiCard label="待审核用户" :value="data.pending_users || 0" icon="👥" color="#7B1FA2" @click="$router.push('/users')" style="cursor:pointer" />
      </el-col>
      <el-col :xs="24" :sm="8">
        <el-card class="quick-search-card">
          <div class="search-box">
            <el-input v-model="searchKeyword" placeholder="搜索客户/订单/产品..." size="large" @keyup.enter="doSearch" clearable>
              <template #prefix><span>🔍</span></template>
            </el-input>
            <el-button type="primary" size="large" @click="doSearch" style="margin-left: 8px;">查询</el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Search Results -->
    <el-dialog v-model="showSearchResults" title="搜索结果" width="700px">
      <div v-if="searchResults.customers && searchResults.customers.length">
        <h4>👥 客户</h4>
        <el-table :data="searchResults.customers" size="small" @row-click="r => $router.push('/customers')" style="cursor:pointer; margin-bottom:16px;">
          <el-table-column prop="name" label="名称" /><el-table-column prop="phone" label="电话" /><el-table-column prop="type" label="类型" />
        </el-table>
      </div>
      <div v-if="searchResults.orders && searchResults.orders.length">
        <h4>📋 订单</h4>
        <el-table :data="searchResults.orders" size="small" @row-click="r => $router.push('/sales-orders')" style="cursor:pointer; margin-bottom:16px;">
          <el-table-column prop="order_no" label="订单号" /><el-table-column prop="customer_name" label="客户" /><el-table-column prop="total_amount" label="金额" /><el-table-column prop="status" label="状态" />
        </el-table>
      </div>
      <div v-if="searchResults.products && searchResults.products.length">
        <h4>📦 产品</h4>
        <el-table :data="searchResults.products" size="small" @row-click="r => $router.push('/products')" style="cursor:pointer; margin-bottom:16px;">
          <el-table-column prop="name" label="名称" /><el-table-column prop="stock" label="库存" /><el-table-column prop="unit" label="单位" />
        </el-table>
      </div>
      <div v-if="searchResults.suppliers && searchResults.suppliers.length">
        <h4>🏭 供应商</h4>
        <el-table :data="searchResults.suppliers" size="small" @row-click="r => $router.push('/suppliers')" style="cursor:pointer; margin-bottom:16px;">
          <el-table-column prop="name" label="名称" /><el-table-column prop="phone" label="电话" /><el-table-column prop="category" label="类别" />
        </el-table>
      </div>
      <div v-if="hasNoResults" style="text-align:center; color:#999; padding:24px;">未找到相关结果</div>
    </el-dialog>

    <!-- Charts Row -->
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

    <!-- Product TOP5 -->
    <el-row :gutter="16" style="margin-top: 16px;">
      <el-col :span="24">
        <el-card>
          <template #header><span class="chart-title">本月产品销量TOP5</span></template>
          <v-chart :option="productTop5Option" style="height: 280px" autoresize />
        </el-card>
      </el-col>
    </el-row>

    <!-- Bottom Row: Alerts + Activities -->
    <el-row :gutter="16" class="bottom-row">
      <el-col :xs="24" :sm="12">
        <el-card v-if="data.alerts && data.alerts.length" class="alert-card">
          <template #header><span class="chart-title" style="color:#F44336">⚠️ 库存预警 ({{ data.alerts.length }})</span></template>
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
import { getBossDashboardExtended, quickSearch } from '../api'

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

const productTop5Option = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { left: 120, right: 20, top: 20, bottom: 20 },
  xAxis: { type: 'value' },
  yAxis: { type: 'category', data: data.value.products_top5.map(r => r.name).reverse(), axisLabel: { fontSize: 13 } },
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
})
</script>

<style scoped>
.page-title { font-size: 24px; font-weight: 700; color: var(--primary); margin-bottom: 20px; }
.kpi-row { margin-bottom: 16px; }
.kpi-row .el-col { margin-bottom: 12px; }
.charts-row .el-col, .bottom-row .el-col { margin-bottom: 16px; }
.chart-card, .alert-card, .activity-card { height: 100%; }
.chart-title { font-size: 16px; font-weight: 600; }

.kpi-with-change { position: relative; }
.change-tag {
  position: absolute; top: 8px; right: 8px;
  font-size: 12px; font-weight: 700; padding: 2px 8px;
  border-radius: 10px; background: #f5f5f5; color: #999;
}
.change-tag.up { color: #4CAF50; background: #E8F5E9; }
.change-tag.down { color: #F44336; background: #FFEBEE; }

.kpi-wrap { position: relative; }
.overdue-hint {
  position: absolute; top: 8px; right: 8px;
  font-size: 12px; font-weight: 700; padding: 2px 8px;
  border-radius: 10px; color: #D32F2F; background: #FFEBEE;
}

.quick-search-card { height: 100%; }
.quick-search-card :deep(.el-card__body) { padding: 16px; }
.search-box { display: flex; align-items: center; }

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
