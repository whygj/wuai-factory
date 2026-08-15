<template>
  <div class="page">
    <div class="page-header">
      <h2>领用记录</h2>
      <el-button v-if="activeTab === 'additive'" type="warning" :loading="exporting" @click="handleExportAdditive" size="large">导出Excel</el-button>
    </div>

    <el-tabs v-model="activeTab" size="large" @tab-change="onTabChange">
      <!-- Tab1 原料领用台账 -->
      <el-tab-pane label="原料领用台账" name="materials">
        <div class="filter-bar">
          <el-date-picker v-model="dateRange" type="daterange" start-placeholder="开始日期" end-placeholder="结束日期" value-format="YYYY-MM-DD" style="width: 260px;" size="large" @change="loadData" />
          <el-select v-model="materialFilter" placeholder="按原料筛选" clearable filterable style="width: 180px;" size="large" @change="loadData">
            <el-option v-for="m in materialList" :key="m.id" :label="m.name" :value="m.id" />
          </el-select>
          <el-select v-model="categoryFilter" placeholder="按类别筛选" clearable style="width: 150px;" size="large" @change="loadData">
            <el-option v-for="c in categoryOptions" :key="c" :label="c" :value="c" />
          </el-select>
          <el-button :loading="exporting" @click="handleExportAll" size="large">导出Excel</el-button>
        </div>

        <el-table :data="logs" stripe style="width: 100%" size="large" class="hidden-mobile">
          <el-table-column prop="date" label="日期" width="110" />
          <el-table-column prop="material_name" label="原料" min-width="120" />
          <el-table-column label="类别" width="100">
            <template #default="{ row }">
              <el-tag v-if="row.category === '添加剂'" type="warning" size="small">添加剂</el-tag>
              <span v-else>{{ row.category || '-' }}</span>
            </template>
          </el-table-column>
          <el-table-column label="领用量" width="100" align="right">
            <template #default="{ row }">{{ row.quantity }} {{ row.unit }}</template>
          </el-table-column>
          <el-table-column label="用途" min-width="160">
            <template #default="{ row }">
              <span v-if="row.product_name">生产 {{ row.product_name }} {{ row.production_quantity }}</span>
              <span v-else style="color:#999;">-</span>
            </template>
          </el-table-column>
          <el-table-column label="领用后余量" width="110" align="right">
            <template #default="{ row }">
              <span style="font-weight: 600;">{{ row.stock_after }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="operator" label="领用人" width="90" />
        </el-table>

        <div class="card-list visible-mobile">
          <div class="record-card" v-for="l in logs" :key="l.id">
            <div class="card-main">
              <div class="card-title">
                {{ l.material_name }}
                <el-tag v-if="l.category === '添加剂'" type="warning" size="small" style="margin-left:4px;">添加剂</el-tag>
              </div>
              <span class="card-sub">{{ l.date }}</span>
            </div>
            <div class="card-info">
              <span>领用 {{ l.quantity }} {{ l.unit }}</span>
              <span>余 {{ l.stock_after }}</span>
            </div>
            <div class="card-info" v-if="l.product_name">
              <span>生产 {{ l.product_name }} {{ l.production_quantity }}</span>
              <span>{{ l.operator }}</span>
            </div>
          </div>
        </div>

        <div class="pagination" v-if="total > pageSize">
          <el-pagination background layout="prev, pager, next" :total="total" :page-size="pageSize" v-model:current-page="page" @current-change="loadData" />
        </div>
        <el-empty v-if="!loading && logs.length === 0" description="暂无领用记录——生产登记提交后自动生成" />
      </el-tab-pane>

      <!-- Tab2 添加剂台账（监管视图） -->
      <el-tab-pane label="添加剂台账" name="additive">
        <el-alert type="warning" :closable="false" class="gb-alert"
          title="按 GB 2760 食品添加剂管理要求记录，供监督检查使用" />

        <div class="filter-bar">
          <el-date-picker v-model="dateRange" type="daterange" start-placeholder="开始日期" end-placeholder="结束日期" value-format="YYYY-MM-DD" style="width: 260px;" size="large" @change="loadData" />
        </div>

        <h4 class="section-title">汇总</h4>
        <el-table :data="summary" stripe size="large" class="hidden-mobile">
          <el-table-column prop="material_name" label="添加剂" min-width="140" />
          <el-table-column label="累计用量" width="120" align="right">
            <template #default="{ row }">{{ row.total_used }} {{ row.unit }}</template>
          </el-table-column>
          <el-table-column prop="use_count" label="使用次数" width="100" align="center" />
          <el-table-column prop="last_used_date" label="最近使用" width="120" />
        </el-table>
        <div class="card-list visible-mobile">
          <div class="record-card" v-for="s in summary" :key="s.material_id">
            <div class="card-main">
              <div class="card-title">{{ s.material_name }}</div>
              <span style="color:#E65100; font-weight:600;">{{ s.total_used }} {{ s.unit }}</span>
            </div>
            <div class="card-info">
              <span>使用 {{ s.use_count }} 次</span>
              <span>最近 {{ s.last_used_date }}</span>
            </div>
          </div>
        </div>

        <h4 class="section-title">明细</h4>
        <el-table :data="additiveLogs" stripe size="large">
          <el-table-column prop="date" label="日期" width="110" />
          <el-table-column prop="material_name" label="添加剂" min-width="120" />
          <el-table-column label="领用量" width="100" align="right">
            <template #default="{ row }">{{ row.quantity }} {{ row.unit }}</template>
          </el-table-column>
          <el-table-column label="用途" min-width="160">
            <template #default="{ row }">
              <span v-if="row.product_name">生产 {{ row.product_name }} {{ row.production_quantity }}</span>
            </template>
          </el-table-column>
          <el-table-column label="领用后余量" width="110" align="right">
            <template #default="{ row }">{{ row.stock_after }}</template>
          </el-table-column>
          <el-table-column prop="operator" label="领用人" width="90" />
        </el-table>
        <el-empty v-if="additiveLogs.length === 0" description="暂无添加剂领用记录" />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getUsageLogs, getAdditiveUsageSummary, getMaterials, downloadExport } from '../api'
import { ElMessage } from 'element-plus'

const activeTab = ref('materials')
const logs = ref([])
const additiveLogs = ref([])
const summary = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = 50
const loading = ref(true)
const exporting = ref(false)
const dateRange = ref(null)
const materialFilter = ref('')
const categoryFilter = ref('')
const materialList = ref([])
const categoryOptions = ['巧克力类', '油脂类', '果酱类', '乳制品', '粉类', '糖浆类', '添加剂']

function buildParams() {
  const params = { page: page.value, page_size: pageSize }
  if (dateRange.value && dateRange.value.length === 2) {
    params.start_date = dateRange.value[0]
    params.end_date = dateRange.value[1]
  }
  if (materialFilter.value) params.material_id = materialFilter.value
  if (categoryFilter.value) params.category = categoryFilter.value
  return params
}

async function loadData() {
  loading.value = true
  try {
    if (activeTab.value === 'materials') {
      const res = await getUsageLogs(buildParams())
      logs.value = res.items
      total.value = res.total
    } else {
      const dateParams = {}
      if (dateRange.value && dateRange.value.length === 2) {
        dateParams.start_date = dateRange.value[0]
        dateParams.end_date = dateRange.value[1]
      }
      const [s, d] = await Promise.all([
        getAdditiveUsageSummary(dateParams),
        getUsageLogs({ ...dateParams, category: '添加剂', page: 1, page_size: 200 }),
      ])
      summary.value = s
      additiveLogs.value = d.items
    }
  } finally {
    loading.value = false
  }
}

function onTabChange() {
  page.value = 1
  loadData()
}

async function handleExportAll() {
  exporting.value = true
  try {
    const params = {}
    if (dateRange.value && dateRange.value.length === 2) {
      params.start_date = dateRange.value[0]
      params.end_date = dateRange.value[1]
    }
    if (materialFilter.value) params.material_id = materialFilter.value
    if (categoryFilter.value) params.category = categoryFilter.value
    await downloadExport('usage-logs', params, '领用台账')
    ElMessage.success('导出成功')
  } catch (e) {} finally {
    exporting.value = false
  }
}

async function handleExportAdditive() {
  exporting.value = true
  try {
    const params = {}
    if (dateRange.value && dateRange.value.length === 2) {
      params.start_date = dateRange.value[0]
      params.end_date = dateRange.value[1]
    }
    await downloadExport('additive-usage', params, '添加剂台账')
    ElMessage.success('导出成功')
  } catch (e) {} finally {
    exporting.value = false
  }
}

onMounted(async () => {
  loadData()
  const res = await getMaterials({ page_size: 200 })
  materialList.value = res.items
})
</script>

<style scoped>
.page { max-width: 1200px; }
.page-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.page-header h2 { font-size: 22px; color: #333; margin: 0; }
.filter-bar { display: flex; gap: 12px; margin-bottom: 16px; flex-wrap: wrap; }
.gb-alert { margin-bottom: 16px; }
.section-title { font-size: 15px; color: #333; margin: 16px 0 8px; }
.pagination { display: flex; justify-content: center; margin-top: 20px; }
.visible-mobile { display: none; }
.hidden-mobile { display: block; }
.card-list { display: flex; flex-direction: column; gap: 8px; margin-bottom: 8px; }
.record-card { background: white; border-radius: 8px; padding: 12px; box-shadow: 0 1px 4px rgba(0,0,0,0.08); }
.card-main { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.card-title { font-size: 15px; font-weight: 600; color: #212121; }
.card-sub { font-size: 12px; color: #999; }
.card-info { display: flex; gap: 16px; font-size: 13px; color: #666; margin-bottom: 6px; flex-wrap: wrap; }
@media (max-width: 768px) {
  .visible-mobile { display: block; }
  .hidden-mobile { display: none; }
  .filter-bar { flex-direction: column; }
  .filter-bar .el-select, .filter-bar .el-date-editor { width: 100% !important; }
}
</style>
