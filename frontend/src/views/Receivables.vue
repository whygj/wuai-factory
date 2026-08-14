<template>
  <div class="page">
    <div class="page-header">
      <h2>应收款管理</h2>
      <el-button :loading="exporting" @click="handleExport" size="large">导出Excel</el-button>
    </div>

    <div class="stats-cards">
      <el-card shadow="hover">
        <div class="stat-item">
          <div class="stat-value" style="color: #E65100;">¥{{ totalUnpaid.toFixed(2) }}</div>
          <div class="stat-label">未回款总额</div>
        </div>
      </el-card>
      <el-card shadow="hover">
        <div class="stat-item">
          <div class="stat-value" style="color: #f56c6c;">{{ overdueCount }}</div>
          <div class="stat-label">逾期订单数</div>
        </div>
      </el-card>
      <el-card shadow="hover">
        <div class="stat-item">
          <div class="stat-value">{{ receivables.length }}</div>
          <div class="stat-label">未回款订单数</div>
        </div>
      </el-card>
    </div>

    <el-tabs v-model="activeTab" size="large">
      <el-tab-pane label="未回款订单" name="list">
        <el-table :data="receivables" stripe style="width: 100%" size="large" class="hidden-mobile">
          <el-table-column prop="order_no" label="订单号" width="160" />
          <el-table-column prop="date" label="日期" width="120" />
          <el-table-column prop="customer_name" label="客户" min-width="140" />
          <el-table-column label="订单金额" width="120" align="right">
            <template #default="{ row }">¥{{ (row.total_amount || 0).toFixed(2) }}</template>
          </el-table-column>
          <el-table-column label="已付金额" width="120" align="right">
            <template #default="{ row }">
              <span style="color: #67c23a;">¥{{ (row.paid_amount || 0).toFixed(2) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="未付金额" width="120" align="right">
            <template #default="{ row }">
              <span style="color: #E65100; font-weight: 600;">¥{{ (row.unpaid_amount || 0).toFixed(2) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="付款状态" width="110" align="center">
            <template #default="{ row }">
              <el-tag :type="paymentTagType(row.payment_status)" size="small">{{ row.payment_status }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120" fixed="right">
            <template #default="{ row }">
              <el-button v-if="canEdit('sales')" link type="primary" @click="openPaymentDialog(row)">登记回款</el-button>
            </template>
          </el-table-column>
        </el-table>

        <div class="card-list visible-mobile">
          <div class="record-card" v-for="item in receivables" :key="item.id">
            <div class="card-main">
              <div class="card-title">{{ item.customer_name }}</div>
              <el-tag :type="paymentTagType(item.payment_status)" size="small">{{ item.payment_status }}</el-tag>
            </div>
            <div class="card-info">
              <span>{{ item.order_no }}</span>
              <span>{{ item.date }}</span>
            </div>
            <div class="card-info">
              <span>金额: ¥{{ (item.total_amount || 0).toFixed(2) }}</span>
              <span style="color: #67c23a;">已付: ¥{{ (item.paid_amount || 0).toFixed(2) }}</span>
            </div>
            <div class="card-info">
              <span style="color: #E65100; font-weight: 600;">未付: ¥{{ (item.unpaid_amount || 0).toFixed(2) }}</span>
            </div>
            <div class="card-actions">
              <el-button v-if="canEdit('sales')" size="small" type="primary" @click="openPaymentDialog(item)">登记回款</el-button>
            </div>
          </div>
        </div>
      </el-tab-pane>

      <el-tab-pane label="逾期订单" name="overdue">
        <el-table :data="overdueList" stripe style="width: 100%" size="large" class="hidden-mobile">
          <el-table-column prop="order_no" label="订单号" width="160" />
          <el-table-column prop="date" label="日期" width="120" />
          <el-table-column prop="customer_name" label="客户" min-width="140" />
          <el-table-column label="未付金额" width="120" align="right">
            <template #default="{ row }">
              <span style="color: #f56c6c; font-weight: 600;">¥{{ (row.unpaid_amount || 0).toFixed(2) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="逾期天数" width="100" align="center">
            <template #default="{ row }">
              <el-tag type="danger" size="small">{{ row.overdue_days }}天</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120" fixed="right">
            <template #default="{ row }">
              <el-button v-if="canEdit('sales')" link type="primary" @click="openPaymentDialog(row)">登记回款</el-button>
            </template>
          </el-table-column>
        </el-table>

        <div class="card-list visible-mobile">
          <div class="record-card" v-for="item in overdueList" :key="item.id">
            <div class="card-main">
              <div class="card-title">{{ item.customer_name }}</div>
              <el-tag type="danger" size="small">{{ item.overdue_days }}天</el-tag>
            </div>
            <div class="card-info">
              <span>{{ item.order_no }}</span>
              <span>{{ item.date }}</span>
            </div>
            <div class="card-info">
              <span style="color: #f56c6c; font-weight: 600;">未付: ¥{{ (item.unpaid_amount || 0).toFixed(2) }}</span>
            </div>
            <div class="card-actions">
              <el-button v-if="canEdit('sales')" size="small" type="primary" @click="openPaymentDialog(item)">登记回款</el-button>
            </div>
          </div>
        </div>
      </el-tab-pane>

      <el-tab-pane label="按客户汇总" name="summary">
        <el-table :data="summaryList" stripe style="width: 100%" size="large" class="hidden-mobile">
          <el-table-column prop="customer_name" label="客户名称" min-width="200" />
          <el-table-column label="订单总额" width="140" align="right">
            <template #default="{ row }">¥{{ (row.total_amount || 0).toFixed(2) }}</template>
          </el-table-column>
          <el-table-column label="已付金额" width="140" align="right">
            <template #default="{ row }">
              <span style="color: #67c23a;">¥{{ (row.paid_amount || 0).toFixed(2) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="未付金额" width="140" align="right">
            <template #default="{ row }">
              <span style="color: #E65100; font-weight: 600;">¥{{ (row.unpaid_amount || 0).toFixed(2) }}</span>
            </template>
          </el-table-column>
        </el-table>

        <div class="card-list visible-mobile">
          <div class="record-card" v-for="(item, idx) in summaryList" :key="idx">
            <div class="card-main">
              <div class="card-title">{{ item.customer_name }}</div>
            </div>
            <div class="card-info">
              <span>总额: ¥{{ (item.total_amount || 0).toFixed(2) }}</span>
            </div>
            <div class="card-info">
              <span style="color: #67c23a;">已付: ¥{{ (item.paid_amount || 0).toFixed(2) }}</span>
              <span style="color: #E65100; font-weight: 600;">未付: ¥{{ (item.unpaid_amount || 0).toFixed(2) }}</span>
            </div>
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- Payment Dialog -->
    <el-dialog v-model="paymentDialogVisible" title="登记回款" :width="isMobile ? '90%' : '400px'" destroy-on-close>
      <el-form :model="paymentForm" label-width="80px" size="large">
        <el-form-item label="订单号">
          <span>{{ paymentOrder?.order_no }}</span>
        </el-form-item>
        <el-form-item label="客户">
          <span>{{ paymentOrder?.customer_name }}</span>
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
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import {
  getReceivables, getOverdueReceivables, getReceivablesSummary, recordPayment, canEdit, downloadExport,
} from '../api'
import { ElMessage } from 'element-plus'

const isMobile = ref(window.innerWidth <= 768)
window.addEventListener('resize', () => { isMobile.value = window.innerWidth <= 768 })

const activeTab = ref('list')
const receivables = ref([])
const overdueList = ref([])
const summaryList = ref([])
const paymentDialogVisible = ref(false)
const submitting = ref(false)
const exporting = ref(false)
const paymentOrder = ref(null)
const paymentForm = ref({ paid_amount: 0 })

const totalUnpaid = computed(() => receivables.value.reduce((sum, r) => sum + (r.unpaid_amount || 0), 0))
const overdueCount = computed(() => overdueList.value.length)

async function handleExport() {
  exporting.value = true
  try {
    await downloadExport('receivables', {}, '应收账款')
    ElMessage.success('导出成功')
  } catch (e) {} finally {
    exporting.value = false
  }
}

function paymentTagType(s) {
  const map = { '未付款': 'danger', '部分付款': 'warning', '已付款': 'success' }
  return map[s] || ''
}

async function loadData() {
  const [rRes, oRes, sRes] = await Promise.all([
    getReceivables({ page_size: 200 }),
    getOverdueReceivables({ page_size: 200 }),
    getReceivablesSummary(),
  ])
  receivables.value = rRes.items
  overdueList.value = oRes.items
  summaryList.value = sRes
}

function openPaymentDialog(row) {
  paymentOrder.value = row
  paymentForm.value.paid_amount = row.unpaid_amount || 0
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

onMounted(loadData)
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
.stats-cards {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
}
.stats-cards .el-card {
  flex: 1;
}
.stat-item {
  text-align: center;
  padding: 8px 0;
}
.stat-value {
  font-size: 28px;
  font-weight: 700;
}
.stat-label {
  font-size: 14px;
  color: #999;
  margin-top: 4px;
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
  .stats-cards {
    flex-direction: column;
  }
  :deep(.el-form-item__label) { font-size: 13px; }
  :deep(.el-dialog) { margin: 8px auto; }
}
</style>
