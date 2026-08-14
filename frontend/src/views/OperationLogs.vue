<template>
  <div class="page">
    <div class="page-header">
      <h2>操作日志</h2>
    </div>

    <div class="filter-bar">
      <el-select v-model="filters.table_name" placeholder="操作对象" clearable style="width: 160px;" size="large" @change="loadData">
        <el-option v-for="t in tableOptions" :key="t.value" :label="t.label" :value="t.value" />
      </el-select>
      <el-select v-model="filters.user_name" placeholder="操作人" clearable filterable style="width: 140px;" size="large" @change="loadData">
        <el-option v-for="u in userOptions" :key="u" :label="u" :value="u" />
      </el-select>
      <el-date-picker v-model="dateRange" type="daterange" start-placeholder="开始日期" end-placeholder="结束日期" value-format="YYYY-MM-DD" style="width: 280px;" size="large" @change="loadData" />
      <el-button type="primary" plain @click="loadData" size="large">查询</el-button>
    </div>

    <el-table :data="logs" stripe style="width: 100%" size="large" class="hidden-mobile">
      <el-table-column label="时间" width="170">
        <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
      </el-table-column>
      <el-table-column prop="user_name" label="操作人" width="110" />
      <el-table-column label="操作" width="150">
        <template #default="{ row }">
          <el-tag :type="actionTagType(row.action)" size="small">{{ row.action }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="对象" width="130">
        <template #default="{ row }">{{ tableLabel(row.table_name) }}</template>
      </el-table-column>
      <el-table-column prop="record_id" label="记录ID" width="80" align="center" />
      <el-table-column prop="detail" label="详情" min-width="220" show-overflow-tooltip />
    </el-table>

    <div class="card-list visible-mobile">
      <div class="record-card" v-for="item in logs" :key="item.id">
        <div class="card-main">
          <el-tag :type="actionTagType(item.action)" size="small">{{ item.action }}</el-tag>
          <span class="card-time">{{ formatTime(item.created_at) }}</span>
        </div>
        <div class="card-info">
          <span>{{ item.user_name }}</span>
          <span>{{ tableLabel(item.table_name) }} #{{ item.record_id }}</span>
        </div>
        <div class="card-info" v-if="item.detail">
          <span class="card-sub">{{ item.detail }}</span>
        </div>
      </div>
    </div>

    <div class="pagination" v-if="total > pageSize">
      <el-pagination background layout="prev, pager, next" :total="total" :page-size="pageSize" v-model:current-page="page" @current-change="loadData" />
    </div>

    <el-empty v-if="!loading && logs.length === 0" description="暂无操作记录" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getOperationLogs, getOperationLogFilters } from '../api'

const TABLE_LABELS = {
  'customers': '客户', 'suppliers': '供应商', 'raw_materials': '原料',
  'products': '产品', 'production_records': '生产记录', 'shipment_records': '发货记录',
  'sales_orders': '销售订单', 'purchase_orders': '采购单', 'lab_records': '试验记录',
  'users': '用户',
}

const logs = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = 50
const loading = ref(true)
const filters = ref({ table_name: '', user_name: '' })
const dateRange = ref(null)
const tableOptions = ref([])
const userOptions = ref([])

function tableLabel(t) {
  return TABLE_LABELS[t] || t || '-'
}

function actionTagType(action) {
  if (action.includes('删除') || action.includes('拒绝')) return 'danger'
  if (action.includes('新增') || action.includes('创建') || action.includes('入库')) return 'success'
  if (action.includes('修改') || action.includes('更新')) return 'warning'
  return 'info'
}

function formatTime(t) {
  if (!t) return ''
  return new Date(t.replace(' ', 'T')).toLocaleString('zh-CN', { hour12: false })
}

async function loadData() {
  loading.value = true
  try {
    const params = { page: page.value, page_size: pageSize }
    if (filters.value.table_name) params.table_name = filters.value.table_name
    if (filters.value.user_name) params.user_name = filters.value.user_name
    if (dateRange.value && dateRange.value.length === 2) {
      params.start_date = dateRange.value[0]
      params.end_date = dateRange.value[1]
    }
    const res = await getOperationLogs(params)
    logs.value = res.items
    total.value = res.total
  } catch (e) {
  } finally {
    loading.value = false
  }
}

async function loadFilters() {
  try {
    const res = await getOperationLogFilters()
    tableOptions.value = res.tables.map(t => ({ label: tableLabel(t), value: t }))
    userOptions.value = res.users
  } catch (e) {}
}

onMounted(() => { loadData(); loadFilters() })
</script>

<style scoped>
.page { max-width: 1200px; }
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}
.page-header h2 { font-size: 22px; color: #333; margin: 0; }
.filter-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}
.pagination {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}
.visible-mobile { display: none; }
.hidden-mobile { display: block; }
.card-list { display: flex; flex-direction: column; gap: 8px; }
.record-card {
  background: white; border-radius: 8px; padding: 12px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.08);
}
.card-main { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.card-time { font-size: 12px; color: #999; }
.card-info { display: flex; gap: 16px; font-size: 13px; color: #666; margin-bottom: 6px; flex-wrap: wrap; }
.card-sub { font-size: 12px; color: #999; }

@media (max-width: 768px) {
  .visible-mobile { display: block; }
  .hidden-mobile { display: none; }
  .filter-bar { flex-direction: column; }
  .filter-bar .el-select, .filter-bar .el-date-editor { width: 100% !important; }
}
</style>
