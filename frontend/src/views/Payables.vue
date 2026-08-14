<template>
  <div class="page">
    <div class="page-header">
      <h2>应付款管理</h2>
    </div>

    <el-row :gutter="16" class="kpi-row">
      <el-col :xs="24" :sm="8">
        <KpiCard label="总应付" :value="'¥' + (summary.total_payable || 0)" :icon="Wallet" color="#E65100" />
      </el-col>
      <el-col :xs="24" :sm="8">
        <KpiCard label="本月已付" :value="'¥' + (summary.month_paid || 0)" :icon="Money" color="#4CAF50" />
      </el-col>
      <el-col :xs="24" :sm="8">
        <KpiCard label="欠款总额" :value="'¥' + (summary.unpaid_total || 0)" :icon="Warning" color="#F44336" />
      </el-col>
    </el-row>

    <div class="filter-bar">
      <el-select v-model="supplierFilter" placeholder="按供应商筛选" clearable filterable style="width: 200px;" size="large" @change="loadData">
        <el-option v-for="s in supplierList" :key="s.id" :label="s.name" :value="s.id" />
      </el-select>
      <el-select v-model="statusFilter" placeholder="付款状态" clearable style="width: 140px;" size="large" @change="loadData">
        <el-option label="未付款" value="未付款" />
        <el-option label="部分付款" value="部分付款" />
        <el-option label="已付款" value="已付款" />
      </el-select>
      <el-button type="primary" plain @click="loadData" size="large">查询</el-button>
    </div>

    <el-table :data="orders" stripe style="width: 100%" size="large" class="hidden-mobile">
      <el-table-column prop="order_no" label="采购单号" width="160" />
      <el-table-column prop="date" label="日期" width="110" />
      <el-table-column prop="supplier_name" label="供应商" min-width="130" />
      <el-table-column label="总额" width="110" align="right">
        <template #default="{ row }">¥{{ (row.total_amount || 0).toFixed(2) }}</template>
      </el-table-column>
      <el-table-column label="已付" width="110" align="right">
        <template #default="{ row }">
          <span style="color: #67c23a;">¥{{ (row.paid_amount || 0).toFixed(2) }}</span>
        </template>
      </el-table-column>
      <el-table-column label="欠款" width="110" align="right">
        <template #default="{ row }">
          <span :style="{ color: row.unpaid_amount < 0 ? '#67c23a' : '#E65100', fontWeight: 600 }">
            {{ row.unpaid_amount < 0 ? '多付 ¥' + (-row.unpaid_amount).toFixed(2) : '¥' + row.unpaid_amount.toFixed(2) }}
          </span>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="100" align="center">
        <template #default="{ row }">
          <el-tag :type="payTagType(row.payment_status)" size="small">{{ row.payment_status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button v-if="isBoss && row.payment_status !== '已付款'" link type="primary" @click="openPayDialog(row)">付款登记</el-button>
          <el-button link type="info" @click="viewPayments(row)">流水</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="card-list visible-mobile">
      <div class="record-card" v-for="item in orders" :key="item.id">
        <div class="card-main">
          <div class="card-title">{{ item.supplier_name }}</div>
          <el-tag :type="payTagType(item.payment_status)" size="small">{{ item.payment_status }}</el-tag>
        </div>
        <div class="card-info">
          <span>{{ item.order_no }}</span>
          <span>{{ item.date }}</span>
        </div>
        <div class="card-info">
          <span>总额 ¥{{ (item.total_amount || 0).toFixed(2) }}</span>
          <span style="color:#67c23a;">已付 ¥{{ (item.paid_amount || 0).toFixed(2) }}</span>
        </div>
        <div class="card-info">
          <span style="color:#E65100; font-weight:600;">{{ item.unpaid_amount < 0 ? '多付 ¥' + (-item.unpaid_amount).toFixed(2) : '欠款 ¥' + item.unpaid_amount.toFixed(2) }}</span>
        </div>
        <div class="card-actions">
          <el-button v-if="isBoss && item.payment_status !== '已付款'" size="small" type="primary" @click="openPayDialog(item)">付款登记</el-button>
          <el-button size="small" @click="viewPayments(item)">流水</el-button>
        </div>
      </div>
    </div>

    <el-empty v-if="!loading && orders.length === 0" description="暂无未付清采购单" />

    <!-- Payment Dialog -->
    <el-dialog v-model="payDialogVisible" title="付款登记" :width="isMobile ? '90%' : '420px'" destroy-on-close>
      <el-form :model="payForm" label-width="80px" size="large">
        <el-form-item label="采购单">
          <span>{{ payOrder?.order_no }}（{{ payOrder?.supplier_name }}）</span>
        </el-form-item>
        <el-form-item label="总额/欠款">
          <span>¥{{ (payOrder?.total_amount || 0).toFixed(2) }} / <span style="color:#E65100;">¥{{ (payOrder?.unpaid_amount || 0).toFixed(2) }}</span></span>
        </el-form-item>
        <el-form-item label="付款金额" required>
          <el-input-number v-model="payForm.amount" :min="0.01" :precision="2" style="width: 100%" />
        </el-form-item>
        <el-form-item label="付款日期" required>
          <el-date-picker v-model="payForm.date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item label="付款方式">
          <el-select v-model="payForm.method" style="width: 100%" allow-create filterable default-first-option placeholder="转账/现金/承兑，可输入">
            <el-option label="转账" value="转账" />
            <el-option label="现金" value="现金" />
            <el-option label="承兑" value="承兑" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="payForm.notes" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="payDialogVisible = false" size="large">取消</el-button>
        <el-button type="primary" @click="handlePay" :loading="submitting" size="large">确认付款</el-button>
      </template>
    </el-dialog>

    <!-- Payments List Dialog -->
    <el-dialog v-model="paymentsVisible" title="付款流水" :width="isMobile ? '90%' : '560px'">
      <el-table :data="payments" stripe size="large">
        <el-table-column prop="date" label="日期" width="110" />
        <el-table-column label="金额" width="110" align="right">
          <template #default="{ row }">
            <span :style="{ textDecoration: row.status === '已作废' ? 'line-through' : 'none', color: row.status === '已作废' ? '#999' : '#333' }">¥{{ (row.amount || 0).toFixed(2) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="method" label="方式" width="80" />
        <el-table-column prop="operator" label="操作人" width="90" />
        <el-table-column label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === '有效' ? 'success' : 'info'" size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column v-if="isBoss" label="操作" width="70" fixed="right">
          <template #default="{ row }">
            <el-button v-if="row.status === '有效'" link type="danger" @click="handleVoidPayment(row)">作废</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="payments.length === 0" description="暂无付款记录" />
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Wallet, Money, Warning } from '@element-plus/icons-vue'
import KpiCard from '../components/KpiCard.vue'
import { getPayablesSummary, getPayables, addPurchasePayment, getPurchasePayments, voidPurchasePayment, getSuppliers } from '../api'
import { ElMessage, ElMessageBox } from 'element-plus'

const isMobile = ref(window.innerWidth <= 768)
window.addEventListener('resize', () => { isMobile.value = window.innerWidth <= 768 })
const isBoss = localStorage.getItem('currentRole') === 'boss'

const summary = ref({})
const orders = ref([])
const supplierList = ref([])
const supplierFilter = ref('')
const statusFilter = ref('')
const loading = ref(true)
const payDialogVisible = ref(false)
const paymentsVisible = ref(false)
const submitting = ref(false)
const payOrder = ref(null)
const payForm = ref({ amount: 0, date: new Date().toISOString().slice(0, 10), method: '转账', notes: '' })
const payments = ref([])

function payTagType(s) {
  const map = { '未付款': 'danger', '部分付款': 'warning', '已付款': 'success' }
  return map[s] || ''
}

async function loadData() {
  loading.value = true
  try {
    const params = {}
    if (supplierFilter.value) params.supplier_id = supplierFilter.value
    if (statusFilter.value) params.payment_status = statusFilter.value
    const [s, o] = await Promise.all([getPayablesSummary(), getPayables(params)])
    summary.value = s
    orders.value = o.items
  } finally {
    loading.value = false
  }
}

function openPayDialog(row) {
  payOrder.value = row
  payForm.value = { amount: row.unpaid_amount > 0 ? row.unpaid_amount : 0.01, date: new Date().toISOString().slice(0, 10), method: '转账', notes: '' }
  payDialogVisible.value = true
}

async function handlePay() {
  if (!payForm.value.amount || payForm.value.amount <= 0) {
    ElMessage.warning('请输入付款金额')
    return
  }
  submitting.value = true
  try {
    await addPurchasePayment(payOrder.value.id, payForm.value)
    ElMessage.success('付款登记成功')
    payDialogVisible.value = false
    loadData()
  } catch (e) {} finally {
    submitting.value = false
  }
}

async function viewPayments(row) {
  payments.value = await getPurchasePayments(row.id)
  paymentsVisible.value = true
}

async function handleVoidPayment(row) {
  try {
    await ElMessageBox.confirm(`确认作废这笔付款 ¥${(row.amount || 0).toFixed(2)}？作废后已付金额将恢复。`, '作废确认', { type: 'warning' })
    await voidPurchasePayment(row.id)
    ElMessage.success('已作废')
    payments.value = await getPurchasePayments(payOrder.value?.id || row.purchase_order_id)
    loadData()
  } catch (e) {
    if (e !== 'cancel') { /* interceptor */ }
  }
}

onMounted(async () => {
  loadData()
  const res = await getSuppliers({ page_size: 200 })
  supplierList.value = res.items
})
</script>

<style scoped>
.page { max-width: 1200px; }
.page-header { margin-bottom: 20px; }
.page-header h2 { font-size: 22px; color: #333; margin: 0; }
.kpi-row { margin-bottom: 20px; }
.kpi-row .el-col { margin-bottom: 12px; }
.filter-bar { display: flex; gap: 12px; margin-bottom: 20px; flex-wrap: wrap; }
.visible-mobile { display: none; }
.hidden-mobile { display: block; }
.card-list { display: flex; flex-direction: column; gap: 8px; }
.record-card { background: white; border-radius: 8px; padding: 12px; box-shadow: 0 1px 4px rgba(0,0,0,0.08); }
.card-main { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.card-title { font-size: 15px; font-weight: 600; color: #212121; }
.card-info { display: flex; gap: 16px; font-size: 13px; color: #666; margin-bottom: 6px; flex-wrap: wrap; }
.card-actions { display: flex; gap: 8px; justify-content: flex-end; }

@media (max-width: 768px) {
  .visible-mobile { display: block; }
  .hidden-mobile { display: none; }
  .filter-bar { flex-direction: column; }
  .filter-bar .el-select { width: 100% !important; }
}
</style>
