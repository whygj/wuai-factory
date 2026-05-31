<template>
  <div class="page">
    <div class="page-header">
      <h2>销售发货</h2>
      <el-button v-if="canEdit('sales')" type="primary" @click="openDialog()" size="large">
        + 新增订单
      </el-button>
    </div>

    <div class="filter-bar">
      <el-select v-model="customerFilter" placeholder="选择客户" clearable style="width: 180px;" size="large" @change="loadData">
        <el-option v-for="c in customerList" :key="c.id" :label="c.name" :value="c.id" />
      </el-select>
      <el-select v-model="statusFilter" placeholder="订单状态" clearable style="width: 140px;" size="large" @change="loadData">
        <el-option label="待发货" value="待发货" />
        <el-option label="部分发货" value="部分发货" />
        <el-option label="已发货" value="已发货" />
        <el-option label="已签收" value="已签收" />
        <el-option label="已取消" value="已取消" />
      </el-select>
      <el-date-picker v-model="dateRange" type="daterange" start-placeholder="开始日期" end-placeholder="结束日期" value-format="YYYY-MM-DD" style="width: 280px;" size="large" @change="loadData" />
      <el-button type="primary" plain @click="loadData" size="large">查询</el-button>
    </div>

    <el-table :data="orders" stripe style="width: 100%" size="large" class="hidden-mobile">
      <el-table-column prop="order_no" label="订单号" width="160" />
      <el-table-column prop="date" label="日期" width="120" />
      <el-table-column prop="customer_name" label="客户" min-width="140" />
      <el-table-column label="金额" width="120" align="right">
        <template #default="{ row }">
          <span style="font-weight: 600; color: #E65100;">¥{{ (row.total_amount || 0).toFixed(2) }}</span>
        </template>
      </el-table-column>
      <el-table-column label="订单状态" width="110" align="center">
        <template #default="{ row }">
          <el-tag :type="statusTagType(row.status)" size="small">{{ row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="付款状态" width="110" align="center">
        <template #default="{ row }">
          <el-tag :type="paymentTagType(row.payment_status)" size="small">{{ row.payment_status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="operator" label="操作人" width="100" />
      <el-table-column label="操作" width="220" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="viewDetail(row)">明细</el-button>
          <el-button v-if="canEdit('sales') && row.status === '待发货'" link type="success" @click="handleShip(row)">发货</el-button>
          <el-button v-if="canEdit('sales') && row.payment_status !== '已付款' && row.status !== '已取消'" link type="warning" @click="openPaymentDialog(row)">回款</el-button>
          <el-button v-if="canEdit('sales') && row.status === '已发货'" link type="primary" @click="handleSign(row)">签收</el-button>
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
          <span>{{ item.customer_name }}</span>
          <span>{{ item.date }}</span>
        </div>
        <div class="card-info">
          <span style="color: #E65100; font-weight: 600;">¥{{ (item.total_amount || 0).toFixed(2) }}</span>
          <el-tag :type="paymentTagType(item.payment_status)" size="small">{{ item.payment_status }}</el-tag>
        </div>
        <div class="card-actions">
          <el-button size="small" @click="viewDetail(item)">明细</el-button>
          <el-button v-if="canEdit('sales') && item.status === '待发货'" size="small" type="success" @click="handleShip(item)">发货</el-button>
          <el-button v-if="canEdit('sales') && item.payment_status !== '已付款' && item.status !== '已取消'" size="small" type="warning" @click="openPaymentDialog(item)">回款</el-button>
          <el-button v-if="canEdit('sales') && item.status === '已发货'" size="small" type="primary" @click="handleSign(item)">签收</el-button>
        </div>
      </div>
    </div>

    <div class="pagination" v-if="total > pageSize">
      <el-pagination background layout="prev, pager, next" :total="total" :page-size="pageSize" v-model:current-page="page" @current-change="loadData" />
    </div>

    <!-- New/Edit Order Dialog -->
    <el-dialog v-model="dialogVisible" title="新增销售订单" :width="isMobile ? '90%' : '650px'" destroy-on-close>
      <el-form :model="form" label-width="90px" size="large">
        <el-form-item label="日期" required>
          <el-date-picker v-model="form.date" type="date" placeholder="选择日期" value-format="YYYY-MM-DD" style="width: 100%;" />
        </el-form-item>
        <el-form-item label="客户" required>
          <el-select v-model="form.customer_id" placeholder="选择客户" style="width: 100%;" filterable>
            <el-option v-for="c in customerList" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="产品明细">
          <div style="width: 100%;">
            <div v-for="(item, idx) in form.items" :key="idx" class="order-item-row">
              <el-select v-model="item.product_id" placeholder="选择产品" style="flex: 1;" @change="onProductChange(idx)">
                <el-option v-for="p in productList" :key="p.id" :label="p.name" :value="p.id" />
              </el-select>
              <el-input-number v-model="item.quantity" :min="0" placeholder="数量" style="width: 120px;" @change="calcSubtotal(idx)" />
              <el-input-number v-model="item.unit_price" :min="0" :precision="2" placeholder="单价" style="width: 120px;" @change="calcSubtotal(idx)" />
              <span class="subtotal-label">¥{{ (item.subtotal || 0).toFixed(2) }}</span>
              <el-button link type="danger" @click="form.items.splice(idx, 1)">删除</el-button>
            </div>
            <el-button type="primary" plain @click="addItem" style="margin-top: 8px; width: 100%;">+ 添加产品</el-button>
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
        <el-button type="primary" @click="handleSubmit" :loading="submitting" size="large">提交订单</el-button>
      </template>
    </el-dialog>

    <!-- Payment Dialog -->
    <el-dialog v-model="paymentDialogVisible" title="登记回款" :width="isMobile ? '90%' : '400px'" destroy-on-close>
      <el-form :model="paymentForm" label-width="80px" size="large">
        <el-form-item label="订单号">
          <span>{{ paymentOrder?.order_no }}</span>
        </el-form-item>
        <el-form-item label="订单金额">
          <span>¥{{ (paymentOrder?.total_amount || 0).toFixed(2) }}</span>
        </el-form-item>
        <el-form-item label="已付金额">
          <span>¥{{ (paymentOrder?.paid_amount || 0).toFixed(2) }}</span>
        </el-form-item>
        <el-form-item label="本次回款" required>
          <el-input-number v-model="paymentForm.paid_amount" :min="0" :precision="2" style="width: 100%;" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="paymentDialogVisible = false" size="large">取消</el-button>
        <el-button type="primary" @click="handlePayment" :loading="submitting" size="large">确认回款</el-button>
      </template>
    </el-dialog>

    <!-- Detail Dialog -->
    <el-dialog v-model="detailVisible" title="订单明细" :width="isMobile ? '90%' : '600px'" destroy-on-close>
      <el-descriptions :column="2" border size="large" v-if="detailOrder">
        <el-descriptions-item label="订单号">{{ detailOrder.order_no }}</el-descriptions-item>
        <el-descriptions-item label="日期">{{ detailOrder.date }}</el-descriptions-item>
        <el-descriptions-item label="客户">{{ detailOrder.customer_name }}</el-descriptions-item>
        <el-descriptions-item label="状态">{{ detailOrder.status }}</el-descriptions-item>
        <el-descriptions-item label="付款状态">{{ detailOrder.payment_status }}</el-descriptions-item>
        <el-descriptions-item label="金额">¥{{ (detailOrder.total_amount || 0).toFixed(2) }}</el-descriptions-item>
      </el-descriptions>
      <el-table :data="detailItems" stripe size="large" style="margin-top: 16px;">
        <el-table-column prop="product_name" label="产品" />
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
  getSalesOrders, createSalesOrder, shipSalesOrder, recordPayment,
  updateSalesOrderStatus, getCustomers, getProducts, canEdit,
} from '../api'
import { ElMessage, ElMessageBox } from 'element-plus'

const isMobile = ref(window.innerWidth <= 768)
window.addEventListener('resize', () => { isMobile.value = window.innerWidth <= 768 })

const orders = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = 50
const customerFilter = ref('')
const statusFilter = ref('')
const dateRange = ref(null)
const dialogVisible = ref(false)
const paymentDialogVisible = ref(false)
const detailVisible = ref(false)
const submitting = ref(false)
const customerList = ref([])
const productList = ref([])
const detailOrder = ref(null)
const detailItems = ref([])
const paymentOrder = ref(null)

const defaultForm = { date: new Date().toISOString().slice(0, 10), customer_id: '', items: [], notes: '' }
const form = ref({ ...defaultForm })
const paymentForm = ref({ paid_amount: 0 })

const totalAmount = computed(() => form.value.items.reduce((sum, i) => sum + (i.subtotal || 0), 0))

function statusTagType(s) {
  const map = { '待发货': 'warning', '部分发货': '', '已发货': 'success', '已签收': 'info', '已取消': 'danger' }
  return map[s] || ''
}
function paymentTagType(s) {
  const map = { '未付款': 'danger', '部分付款': 'warning', '已付款': 'success' }
  return map[s] || ''
}

async function loadData() {
  const params = { page: page.value, page_size: pageSize }
  if (customerFilter.value) params.customer_id = customerFilter.value
  if (statusFilter.value) params.status = statusFilter.value
  if (dateRange.value && dateRange.value.length === 2) {
    params.start_date = dateRange.value[0]
    params.end_date = dateRange.value[1]
  }
  const res = await getSalesOrders(params)
  orders.value = res.items
  total.value = res.total
}

async function loadOptions() {
  const [cRes, pRes] = await Promise.all([getCustomers({ page_size: 200 }), getProducts({ page_size: 200 })])
  customerList.value = cRes.items
  productList.value = pRes.items
}

function openDialog() {
  form.value = { ...defaultForm, items: [] }
  dialogVisible.value = true
}

function addItem() {
  form.value.items.push({ product_id: '', quantity: 1, unit_price: 0, subtotal: 0 })
}

function onProductChange(idx) {
  const item = form.value.items[idx]
  const product = productList.value.find(p => p.id === item.product_id)
  if (product) item.unit_price = product.spec ? 0 : 0
  calcSubtotal(idx)
}

function calcSubtotal(idx) {
  const item = form.value.items[idx]
  item.subtotal = (item.quantity || 0) * (item.unit_price || 0)
}

async function handleSubmit() {
  if (!form.value.date || !form.value.customer_id || form.value.items.length === 0) {
    ElMessage.warning('请填写日期、客户和产品明细')
    return
  }
  submitting.value = true
  try {
    await createSalesOrder({
      date: form.value.date,
      customer_id: form.value.customer_id,
      items: form.value.items.map(i => ({ product_id: i.product_id, quantity: i.quantity, unit_price: i.unit_price })),
      notes: form.value.notes,
    })
    ElMessage.success('订单创建成功')
    dialogVisible.value = false
    loadData()
  } catch (e) {} finally {
    submitting.value = false
  }
}

async function handleShip(row) {
  await ElMessageBox.confirm(`确认发货？将扣减产品库存。`, '确认发货', { type: 'warning' })
  await shipSalesOrder(row.id)
  ElMessage.success('发货成功，库存已扣减')
  loadData()
}

function openPaymentDialog(row) {
  paymentOrder.value = row
  paymentForm.value.paid_amount = row.total_amount - row.paid_amount
  paymentDialogVisible.value = true
}

async function handlePayment() {
  if (!paymentForm.value.paid_amount || paymentForm.value.paid_amount <= 0) {
    ElMessage.warning('请输入回款金额')
    return
  }
  submitting.value = true
  try {
    await recordPayment(paymentOrder.value.id, paymentForm.value)
    ElMessage.success('回款登记成功')
    paymentDialogVisible.value = false
    loadData()
  } catch (e) {} finally {
    submitting.value = false
  }
}

async function handleSign(row) {
  await ElMessageBox.confirm('确认已签收？', '确认签收')
  await updateSalesOrderStatus(row.id, { status: '已签收' })
  ElMessage.success('已签收')
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
