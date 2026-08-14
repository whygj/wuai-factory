<template>
  <div class="page">
    <div class="page-header">
      <h2>采购管理</h2>
      <div style="display:flex; gap:8px;">
        <el-button :loading="exporting" @click="handleExport" size="large">导出Excel</el-button>
        <el-button v-if="canEdit('purchase')" type="primary" @click="openDialog()" size="large">
          + 新增采购
        </el-button>
      </div>
    </div>

    <div class="filter-bar">
      <el-select v-model="supplierFilter" placeholder="选择供应商" clearable style="width: 180px;" size="large" @change="loadData">
        <el-option v-for="s in supplierList" :key="s.id" :label="s.name" :value="s.id" />
      </el-select>
      <el-select v-model="statusFilter" placeholder="状态" clearable style="width: 140px;" size="large" @change="loadData">
        <el-option label="待到货" value="待到货" />
        <el-option label="已到货" value="已到货" />
        <el-option label="已入库" value="已入库" />
        <el-option label="已取消" value="已取消" />
      </el-select>
      <el-date-picker v-model="dateRange" type="daterange" start-placeholder="开始日期" end-placeholder="结束日期" value-format="YYYY-MM-DD" style="width: 280px;" size="large" @change="loadData" />
      <el-button type="primary" plain @click="loadData" size="large">查询</el-button>
    </div>

    <el-table :data="orders" stripe style="width: 100%" size="large" class="hidden-mobile">
      <el-table-column prop="order_no" label="采购单号" width="160" />
      <el-table-column prop="date" label="日期" width="120" />
      <el-table-column prop="supplier_name" label="供应商" min-width="140" />
      <el-table-column label="金额" width="120" align="right">
        <template #default="{ row }">
          <span style="font-weight: 600; color: #E65100;">¥{{ (row.total_amount || 0).toFixed(2) }}</span>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="110" align="center">
        <template #default="{ row }">
          <el-tag :type="statusTagType(row.status)" size="small">{{ row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="operator" label="操作人" width="100" />
      <el-table-column label="操作" width="180" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="viewDetail(row)">明细</el-button>
          <el-button v-if="canEdit('purchase') && (row.status === '待到货' || row.status === '已到货')" link type="success" @click="handleInbound(row)">入库</el-button>
          <el-button v-if="canEdit('purchase') && row.status === '待到货'" link type="warning" @click="handleArrive(row)">到货</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="card-list visible-mobile">
      <div class="record-card" v-for="item in orders" :key="item.id">
        <div class="card-main">
          <div class="card-title">{{ item.order_no }}</div>
          <el-tag :type="statusTagType(item.status)" size="small">{{ item.status }}</el-tag>
        </div>
        <div class="card-info">
          <span>{{ item.supplier_name }}</span>
          <span>{{ item.date }}</span>
        </div>
        <div class="card-info">
          <span style="color: #E65100; font-weight: 600;">¥{{ (item.total_amount || 0).toFixed(2) }}</span>
        </div>
        <div class="card-actions">
          <el-button size="small" @click="viewDetail(item)">明细</el-button>
          <el-button v-if="canEdit('purchase') && (item.status === '待到货' || item.status === '已到货')" size="small" type="success" @click="handleInbound(item)">入库</el-button>
          <el-button v-if="canEdit('purchase') && item.status === '待到货'" size="small" type="warning" @click="handleArrive(item)">到货</el-button>
        </div>
      </div>
    </div>

    <div class="pagination" v-if="total > pageSize">
      <el-pagination background layout="prev, pager, next" :total="total" :page-size="pageSize" v-model:current-page="page" @current-change="loadData" />
    </div>

    <!-- New Purchase Dialog -->
    <el-dialog v-model="dialogVisible" title="新增采购单" :width="isMobile ? '90%' : '650px'" destroy-on-close>
      <el-form :model="form" label-width="90px" size="large">
        <el-form-item label="日期" required>
          <el-date-picker v-model="form.date" type="date" placeholder="选择日期" value-format="YYYY-MM-DD" style="width: 100%;" />
        </el-form-item>
        <el-form-item label="供应商" required>
          <el-select v-model="form.supplier_id" placeholder="选择供应商" style="width: 100%;" filterable>
            <el-option v-for="s in supplierList" :key="s.id" :label="s.name" :value="s.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="原料明细">
          <div style="width: 100%;">
            <div v-for="(item, idx) in form.items" :key="idx" class="order-item-row">
              <el-select v-model="item.material_id" placeholder="选择原料" style="flex: 1;" @change="onMaterialChange(idx)">
                <el-option v-for="m in materialList" :key="m.id" :label="m.name" :value="m.id" />
              </el-select>
              <el-input-number v-model="item.quantity" :min="0" placeholder="数量" style="width: 120px;" @change="calcSubtotal(idx)" />
              <el-input-number v-model="item.unit_price" :min="0" :precision="2" placeholder="单价" style="width: 120px;" @change="calcSubtotal(idx)" />
              <span class="subtotal-label">¥{{ (item.subtotal || 0).toFixed(2) }}</span>
              <el-button link type="danger" @click="form.items.splice(idx, 1)">删除</el-button>
              <div class="batch-fields">
                <el-input v-model="item.batch_no" placeholder="批次号（留空自动生成）" style="flex: 1;" />
                <el-date-picker v-model="item.production_date" type="date" placeholder="原料生产日期" value-format="YYYY-MM-DD" style="width: 150px;" :clearable="true" />
                <el-date-picker v-model="item.expiry_date" type="date" placeholder="保质期到" value-format="YYYY-MM-DD" style="width: 150px;" :clearable="true" />
                <span class="batch-hint">选填：填任一项即建批次可追溯</span>
              </div>
            </div>
            <el-button type="primary" plain @click="addItem" style="margin-top: 8px; width: 100%;">+ 添加原料</el-button>
          </div>
        </el-form-item>
        <el-form-item label="合计金额">
          <span style="font-size: 20px; font-weight: 700; color: #E65100;">¥{{ totalAmount.toFixed(2) }}</span>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.notes" type="textarea" :rows="2" placeholder="备注信息" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false" size="large">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting" size="large">提交采购</el-button>
      </template>
    </el-dialog>

    <!-- Detail Dialog -->
    <el-dialog v-model="detailVisible" title="采购单明细" :width="isMobile ? '90%' : '600px'" destroy-on-close>
      <el-descriptions :column="2" border size="large" v-if="detailOrder">
        <el-descriptions-item label="采购单号">{{ detailOrder.order_no }}</el-descriptions-item>
        <el-descriptions-item label="日期">{{ detailOrder.date }}</el-descriptions-item>
        <el-descriptions-item label="供应商">{{ detailOrder.supplier_name }}</el-descriptions-item>
        <el-descriptions-item label="状态">{{ detailOrder.status }}</el-descriptions-item>
        <el-descriptions-item label="金额">¥{{ (detailOrder.total_amount || 0).toFixed(2) }}</el-descriptions-item>
      </el-descriptions>
      <el-table :data="detailItems" stripe size="large" style="margin-top: 16px;">
        <el-table-column prop="material_name" label="原料" />
        <el-table-column prop="quantity" label="数量" width="100" />
        <el-table-column prop="unit" label="单位" width="80" />
        <el-table-column label="单价" width="100" align="right">
          <template #default="{ row }">¥{{ (row.unit_price || 0).toFixed(2) }}</template>
        </el-table-column>
        <el-table-column label="小计" width="120" align="right">
          <template #default="{ row }">
            <span style="color: #E65100; font-weight: 600;">¥{{ (row.subtotal || 0).toFixed(2) }}</span>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import {
  getPurchases, createPurchase, confirmInbound, updatePurchaseStatus,
  getSuppliers, getMaterials, canEdit, downloadExport,
} from '../api'
import { ElMessage, ElMessageBox } from 'element-plus'

const isMobile = ref(window.innerWidth <= 768)
window.addEventListener('resize', () => { isMobile.value = window.innerWidth <= 768 })

const orders = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = 50
const supplierFilter = ref('')
const statusFilter = ref('')
const dateRange = ref(null)
const dialogVisible = ref(false)
const detailVisible = ref(false)
const submitting = ref(false)
const exporting = ref(false)
const supplierList = ref([])
const materialList = ref([])
const detailOrder = ref(null)
const detailItems = ref([])

const defaultForm = { date: new Date().toISOString().slice(0, 10), supplier_id: '', items: [], notes: '' }
const form = ref({ ...defaultForm })

const totalAmount = computed(() => form.value.items.reduce((sum, i) => sum + (i.subtotal || 0), 0))

function statusTagType(s) {
  const map = { '待到货': 'warning', '已到货': '', '已入库': 'success', '已取消': 'danger' }
  return map[s] || ''
}

async function loadData() {
  const params = { page: page.value, page_size: pageSize }
  if (supplierFilter.value) params.supplier_id = supplierFilter.value
  if (statusFilter.value) params.status = statusFilter.value
  if (dateRange.value && dateRange.value.length === 2) {
    params.start_date = dateRange.value[0]
    params.end_date = dateRange.value[1]
  }
  const res = await getPurchases(params)
  orders.value = res.items
  total.value = res.total
}

async function loadOptions() {
  const [sRes, mRes] = await Promise.all([getSuppliers({ page_size: 200 }), getMaterials({ page_size: 200 })])
  supplierList.value = sRes.items
  materialList.value = mRes.items
}

function openDialog() {
  form.value = { ...defaultForm, items: [] }
  dialogVisible.value = true
}

function addItem() {
  form.value.items.push({ material_id: '', quantity: 1, unit_price: 0, subtotal: 0, batch_no: '', production_date: null, expiry_date: null })
}

function onMaterialChange(idx) {
  const item = form.value.items[idx]
  const material = materialList.value.find(m => m.id === item.material_id)
  if (material) item.unit_price = material.purchase_price || 0
  calcSubtotal(idx)
}

function calcSubtotal(idx) {
  const item = form.value.items[idx]
  item.subtotal = (item.quantity || 0) * (item.unit_price || 0)
}

async function handleSubmit() {
  if (!form.value.date || !form.value.supplier_id || form.value.items.length === 0) {
    ElMessage.warning('请填写日期、供应商和原料明细')
    return
  }
  submitting.value = true
  try {
    await createPurchase({
      date: form.value.date,
      supplier_id: form.value.supplier_id,
      items: form.value.items.map(i => ({
        material_id: i.material_id, quantity: i.quantity, unit_price: i.unit_price,
        batch_no: i.batch_no || null,
        production_date: i.production_date || null,
        expiry_date: i.expiry_date || null,
      })),
      notes: form.value.notes,
    })
    ElMessage.success('采购单创建成功')
    dialogVisible.value = false
    loadData()
  } catch (e) {} finally {
    submitting.value = false
  }
}

async function handleExport() {
  exporting.value = true
  try {
    const params = {}
    if (dateRange.value && dateRange.value.length === 2) {
      params.start_date = dateRange.value[0]
      params.end_date = dateRange.value[1]
    }
    await downloadExport('purchases', params, '采购明细')
    ElMessage.success('导出成功')
  } catch (e) {} finally {
    exporting.value = false
  }
}

async function handleArrive(row) {
  await ElMessageBox.confirm('确认已到货？', '确认到货')
  await updatePurchaseStatus(row.id, { status: '已到货' })
  ElMessage.success('已确认到货')
  loadData()
}

async function handleInbound(row) {
  await ElMessageBox.confirm('确认入库？将增加原料库存。', '确认入库', { type: 'warning' })
  await confirmInbound(row.id)
  ElMessage.success('入库成功，原料库存已增加')
  loadData()
}

function viewDetail(row) {
  detailOrder.value = row
  try {
    detailItems.value = JSON.parse(row.items || '[]')
  } catch {
    detailItems.value = []
  }
  detailVisible.value = true
}

onMounted(() => { loadData(); loadOptions() })
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
.order-item-row {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-bottom: 8px;
  flex-wrap: wrap;
}
.batch-fields {
  display: flex;
  gap: 8px;
  align-items: center;
  width: 100%;
  flex-wrap: wrap;
}
.batch-hint {
  font-size: 12px;
  color: #999;
}
.subtotal-label {
  min-width: 90px;
  text-align: right;
  font-weight: 600;
  color: #E65100;
}
.visible-mobile { display: none; }
.hidden-mobile { display: block; }
.card-list { display: flex; flex-direction: column; gap: 8px; }
.record-card {
  background: white; border-radius: 8px; padding: 12px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.08);
}
.card-main { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.card-title { font-size: 15px; font-weight: 600; color: #212121; }
.card-sub { font-size: 12px; color: #999; }
.card-info { display: flex; gap: 16px; font-size: 13px; color: #666; margin-bottom: 6px; flex-wrap: wrap; }
.card-actions { display: flex; gap: 8px; justify-content: flex-end; }

@media (max-width: 768px) {
  .visible-mobile { display: block; }
  .hidden-mobile { display: none; }
  .page { padding: 8px; }
  .page-header { flex-direction: column; align-items: stretch; gap: 8px; }
  .filter-bar { flex-direction: column; }
  .filter-bar .el-input, .filter-bar .el-select { width: 100% !important; }
  .order-item-row { flex-wrap: wrap; }
  .order-item-row .el-input-number { width: 100px !important; }
  :deep(.el-form-item__label) { font-size: 13px; }
  :deep(.el-dialog) { margin: 8px auto; }
}
</style>
