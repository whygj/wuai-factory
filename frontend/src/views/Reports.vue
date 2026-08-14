<template>
  <div class="page">
    <h2 class="page-title">经营报表</h2>

    <el-tabs v-model="activeTab" type="card" @tab-change="onTabChange">
      <el-tab-pane label="销售报表" name="sales">
        <div class="tab-toolbar">
          <el-date-picker v-model="salesDate" type="daterange" range-separator="至" start-placeholder="开始日期" end-placeholder="结束日期" value-format="YYYY-MM-DD" @change="loadSales" />
        </div>
        <el-row :gutter="16" class="kpi-row">
          <el-col :xs="12" :sm="8">
            <KpiCard label="销售总额" :value="'¥' + (sales.total_amount || 0)" icon="💰" color="#E65100" />
          </el-col>
          <el-col :xs="12" :sm="8">
            <KpiCard label="订单数" :value="sales.total_orders || 0" icon="📋" color="#4CAF50" />
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :xs="24" :sm="14">
            <el-card class="chart-card">
              <template #header><span class="card-title">销售趋势</span></template>
              <v-chart :option="salesDailyOption" style="height:300px" autoresize />
            </el-card>
          </el-col>
          <el-col :xs="24" :sm="10">
            <el-card class="chart-card">
              <template #header><span class="card-title">客户排行</span></template>
              <v-chart :option="salesCustomerOption" style="height:300px" autoresize />
            </el-card>
          </el-col>
        </el-row>
      </el-tab-pane>

      <el-tab-pane label="生产报表" name="production">
        <div class="tab-toolbar">
          <el-select v-model="prodDays" @change="loadProd">
            <el-option label="近7天" :value="7" />
            <el-option label="近30天" :value="30" />
            <el-option label="近90天" :value="90" />
          </el-select>
        </div>
        <el-row :gutter="16" class="kpi-row">
          <el-col :xs="12" :sm="8">
            <KpiCard label="总产量" :value="prod.total_quantity || 0" icon="🏭" color="#E65100" />
          </el-col>
          <el-col :xs="12" :sm="8">
            <KpiCard label="生产批次" :value="prod.total_records || 0" icon="📋" color="#4CAF50" />
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :xs="24" :sm="14">
            <el-card class="chart-card">
              <template #header><span class="card-title">产量趋势</span></template>
              <v-chart :option="prodDailyOption" style="height:300px" autoresize />
            </el-card>
          </el-col>
          <el-col :xs="24" :sm="10">
            <el-card class="chart-card">
              <template #header><span class="card-title">产品产量排行</span></template>
              <v-chart :option="prodByProductOption" style="height:300px" autoresize />
            </el-card>
          </el-col>
        </el-row>
      </el-tab-pane>

      <el-tab-pane label="毛利" name="margin">
        <div class="tab-toolbar">
          <el-date-picker v-model="marginMonth" type="month" placeholder="选择月份" value-format="YYYY-MM" @change="loadMargin" />
        </div>
        <div class="margin-board" v-if="margin.year">
          <div class="margin-row">
            <span class="margin-label">本月销售收入（订单额）</span>
            <span class="margin-value">¥{{ (margin.revenue || 0).toLocaleString() }}</span>
          </div>
          <div class="margin-row">
            <span class="margin-label">本月原料消耗（生产成本）</span>
            <span class="margin-value cost">− ¥{{ (margin.material_cost || 0).toLocaleString() }}</span>
          </div>
          <div class="margin-divider"></div>
          <div class="margin-row total">
            <span class="margin-label">粗毛利</span>
            <span class="margin-value" :style="{ color: margin.gross_margin >= 0 ? '#2E7D32' : '#C62828' }">
              ¥{{ (margin.gross_margin || 0).toLocaleString() }}
              <span v-if="margin.margin_pct != null" class="margin-pct">（{{ margin.margin_pct }}%）</span>
            </span>
          </div>
          <div class="margin-notes">
            注：不含人工/水电/房租/包装等费用，仅原料成本口径<br>
            注：按月汇总，生产与销售存在时间错位（如3月生产4月售出）
          </div>
        </div>
      </el-tab-pane>

      <el-tab-pane label="库存报表" name="inventory">
        <el-row :gutter="16" class="kpi-row">
          <el-col :xs="12" :sm="6">
            <KpiCard label="原料种类" :value="inv.material_count || 0" icon="🧈" color="#E65100" />
          </el-col>
          <el-col :xs="12" :sm="6">
            <KpiCard label="产品种类" :value="inv.product_count || 0" icon="📦" color="#4CAF50" />
          </el-col>
          <el-col :xs="12" :sm="6">
            <KpiCard label="库存预警" :value="inv.alert_count || 0" icon="⚠️" color="#F44336" />
          </el-col>
          <el-col :xs="12" :sm="6">
            <KpiCard label="原料价值" :value="'¥' + (inv.total_material_value || 0)" icon="💎" color="#FF9800" />
          </el-col>
        </el-row>
        <el-card>
          <template #header><span class="card-title">原料库存明细</span></template>
          <el-table :data="inv.materials || []" stripe size="small">
            <el-table-column prop="name" label="名称" />
            <el-table-column prop="category" label="类别" width="100" />
            <el-table-column prop="current" label="库存" width="80" />
            <el-table-column prop="unit" label="单位" width="60" />
            <el-table-column prop="safety" label="安全库存" width="80" />
            <el-table-column label="价值" width="90">
              <template #default="{ row }">{{ (row.value || 0).toFixed(0) }}</template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { LineChart, BarChart } from 'echarts/charts'
import { TitleComponent, TooltipComponent, GridComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import KpiCard from '../components/KpiCard.vue'
import { getSalesReport, getProductionReport, getInventoryReport, getGrossMargin } from '../api'

use([LineChart, BarChart, TitleComponent, TooltipComponent, GridComponent, CanvasRenderer])

const activeTab = ref('sales')
const salesDate = ref(null)
const sales = ref({})
const prodDays = ref(30)
const prod = ref({})
const inv = ref({})
const marginMonth = ref('')
const margin = ref({})

async function loadMargin() {
  let params = {}
  if (marginMonth.value) {
    const [y, m] = marginMonth.value.split('-')
    params = { year: y, month: m }
  }
  margin.value = await getGrossMargin(params)
}

const salesDailyOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { left: 60, right: 20, top: 20, bottom: 40 },
  xAxis: { type: 'category', data: (sales.value.daily || []).map(r => r.date.slice(5)) },
  yAxis: { type: 'value' },
  series: [{ type: 'line', smooth: true, data: (sales.value.daily || []).map(r => r.amount), areaStyle: { color: 'rgba(230,81,0,0.12)' }, lineStyle: { color: '#E65100', width: 2 }, itemStyle: { color: '#E65100' } }],
}))

const salesCustomerOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { left: 100, right: 20, top: 20, bottom: 20 },
  xAxis: { type: 'value' },
  yAxis: { type: 'category', data: (sales.value.by_customer || []).map(r => r.name).reverse() },
  series: [{ type: 'bar', data: (sales.value.by_customer || []).map(r => r.amount).reverse(), itemStyle: { color: '#E65100', borderRadius: [0, 6, 6, 0] } }],
}))

const prodDailyOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { left: 50, right: 20, top: 20, bottom: 40 },
  xAxis: { type: 'category', data: (prod.value.daily || []).map(r => r.date.slice(5)) },
  yAxis: { type: 'value' },
  series: [{ type: 'line', smooth: true, data: (prod.value.daily || []).map(r => r.quantity), areaStyle: { color: 'rgba(76,175,80,0.12)' }, lineStyle: { color: '#4CAF50', width: 2 }, itemStyle: { color: '#4CAF50' } }],
}))

const prodByProductOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { left: 120, right: 20, top: 20, bottom: 20 },
  xAxis: { type: 'value' },
  yAxis: { type: 'category', data: (prod.value.by_product || []).map(r => r.name).reverse() },
  series: [{ type: 'bar', data: (prod.value.by_product || []).map(r => r.quantity).reverse(), itemStyle: { color: '#4CAF50', borderRadius: [0, 6, 6, 0] } }],
}))

async function loadSales() {
  try {
    const params = {}
    if (salesDate.value && salesDate.value.length === 2) {
      params.start_date = salesDate.value[0]
      params.end_date = salesDate.value[1]
    }
    sales.value = await getSalesReport(params)
  } catch (e) {}
}

async function loadProd() {
  try { prod.value = await getProductionReport({ days: prodDays.value }) } catch (e) {}
}

async function loadInv() {
  try { inv.value = await getInventoryReport() } catch (e) {}
}

function onTabChange(tab) {
  if (tab === 'sales' && !sales.value.total_orders) loadSales()
  if (tab === 'production' && !prod.value.total_records) loadProd()
  if (tab === 'inventory' && !inv.value.material_count) loadInv()
  if (tab === 'margin' && !margin.value.year) loadMargin()
}

onMounted(() => { loadSales() })
</script>

<style scoped>
.page-title { font-size: 24px; font-weight: 700; color: var(--primary); margin-bottom: 20px; }
.tab-toolbar { margin-bottom: 16px; }
.kpi-row { margin-bottom: 16px; }
.margin-board {
  max-width: 560px;
  background: linear-gradient(135deg, #FFF3E0 0%, #FFFFFF 100%);
  border-radius: 12px;
  padding: 24px 28px;
}
.margin-row { display: flex; justify-content: space-between; align-items: center; padding: 10px 0; font-size: 17px; }
.margin-row.total { font-size: 20px; font-weight: 700; }
.margin-label { color: #555; }
.margin-value { font-weight: 600; }
.margin-value.cost { color: #C62828; }
.margin-divider { border-top: 2px dashed #FFCC80; margin: 8px 0; }
.margin-pct { font-size: 15px; }
.margin-notes { margin-top: 14px; font-size: 12px; color: #999; line-height: 1.8; }
.kpi-row .el-col { margin-bottom: 12px; }
.chart-card { margin-bottom: 16px; }
.card-title { font-size: 15px; font-weight: 600; }
@media (max-width: 768px) {
  .page { padding: 8px; }
  .tab-toolbar { display: flex; flex-wrap: wrap; }
  .tab-toolbar .el-date-editor { width: 100% !important; }
  :deep(.el-table) { font-size: 13px; }
  :deep(.el-table th), :deep(.el-table td) { padding: 6px 0; }
  :deep(.el-tabs__item) { font-size: 14px; padding: 0 8px; }
}
</style>
