<template>
  <div class="shipment-list-page">
    <div class="page-header">
      <h2 class="page-title">发货列表</h2>
      <div class="page-actions">
        <el-select v-model="statusFilter" placeholder="状态筛选" clearable @change="loadRecords" style="width: 120px">
          <el-option label="待发货" value="待发货" />
          <el-option label="已发货" value="已发货" />
          <el-option label="已签收" value="已签收" />
        </el-select>
        <el-button type="primary" @click="$router.push('/shipments/new')">新建发货</el-button>
      </div>
    </div>

    <el-card>
      <el-table :data="records" stripe style="width: 100%" class="hidden-mobile">
        <el-table-column prop="date" label="日期" width="110" />
        <el-table-column prop="customer_name" label="客户" min-width="110" />
        <el-table-column label="关联订单" width="150">
          <template #default="{ row }">
            <span v-if="row.order_no" class="order-link" @click="goToOrder(row.sales_order_id)">{{ row.order_no }}</span>
            <span v-else style="color: #999;">独立发货</span>
          </template>
        </el-table-column>
        <el-table-column prop="product_name" label="产品" min-width="120" />
        <el-table-column prop="quantity" label="数量" width="100">
          <template #default="{ row }">{{ row.quantity }} {{ row.unit }}</template>
        </el-table-column>
        <el-table-column prop="total_amount" label="金额" width="100">
          <template #default="{ row }">{{ row.total_amount ? '¥' + row.total_amount.toFixed(2) : '-' }}</template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" size="large">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="openPrint(row)">打印</el-button>
            <template v-if="row.status === '待发货'">
              <el-button size="small" type="primary" @click="updateStatus(row.id, '已发货')">发货</el-button>
            </template>
            <template v-if="row.status === '已发货'">
              <el-button size="small" type="success" @click="updateStatus(row.id, '已签收')">签收</el-button>
            </template>
          </template>
        </el-table-column>
      </el-table>

      <div class="card-list visible-mobile">
        <div class="record-card" v-for="item in records" :key="item.id">
          <div class="card-main">
            <div>
              <div class="card-title">{{ item.customer_name }}</div>
              <div class="card-sub">{{ item.product_name }}</div>
            </div>
            <el-tag :type="statusType(item.status)" size="small">{{ item.status }}</el-tag>
          </div>
          <div class="card-info">
            <span>{{ item.date }}</span>
            <span>{{ item.quantity }} {{ item.unit }}</span>
            <span v-if="item.total_amount">¥{{ item.total_amount.toFixed(2) }}</span>
          </div>
          <div class="card-info" v-if="item.order_no">
            <span style="color: #E65100;">关联: <span class="order-link" @click="goToOrder(item.sales_order_id)">{{ item.order_no }}</span></span>
          </div>
          <div class="card-actions">
            <el-button size="small" @click="openPrint(item)">打印</el-button>
            <el-button v-if="item.status === '待发货'" size="small" type="primary" @click="updateStatus(item.id, '已发货')">发货</el-button>
            <el-button v-if="item.status === '已发货'" size="small" type="success" @click="updateStatus(item.id, '已签收')">签收</el-button>
          </div>
        </div>
      </div>
    </el-card>

    <!-- Delivery Note Print Overlay (A4) -->
    <div v-if="printData" class="print-overlay" @click.self="printData = null">
      <div class="print-sheet">
        <div class="doc-header">
          <h1>五爱食品 送货单</h1>
        </div>
        <div class="doc-meta">
          <div>单号：{{ printData.order_no || ('SHP-' + printData.id) }}</div>
          <div>日期：{{ printData.date }}</div>
        </div>
        <div class="doc-customer">
          <div>客户：{{ printData.customer_name }}</div>
        </div>
        <table class="doc-table">
          <thead>
            <tr><th>产品</th><th>数量</th><th>单位</th><th>单价</th><th>金额</th></tr>
          </thead>
          <tbody>
            <tr>
              <td>{{ printData.product_name }}</td>
              <td>{{ printData.quantity }}</td>
              <td>{{ printData.unit }}</td>
              <td>{{ printData.unit_price != null ? '¥' + printData.unit_price.toFixed(2) : '—' }}</td>
              <td>{{ printData.total_amount ? '¥' + printData.total_amount.toFixed(2) : '—' }}</td>
            </tr>
          </tbody>
        </table>
        <div class="doc-total">
          合计：<span>¥{{ printData.total_amount ? printData.total_amount.toFixed(2) : '—' }}</span>
        </div>
        <div class="doc-signs">
          <div>司机签字：______________</div>
          <div>客户签字：______________</div>
        </div>
        <div class="doc-signs">
          <div>收货日期：______________</div>
        </div>
        <div class="doc-note">退货请在收货时当面清点提出</div>
        <div class="doc-footer">打印时间：{{ printTime }}　操作人：{{ printData.operator || '' }}</div>
        <div class="print-actions no-print">
          <el-button type="primary" size="large" @click="doPrint">打印</el-button>
          <el-button size="large" @click="printData = null">关闭</el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getShipments, updateShipmentStatus } from '../api'
import { ElMessage } from 'element-plus'

const router = useRouter()
const records = ref([])
const statusFilter = ref('')
const printData = ref(null)
const printTime = ref('')

function openPrint(row) {
  printData.value = row
  printTime.value = new Date().toLocaleString('zh-CN', { hour12: false })
}

function doPrint() {
  window.print()
}

function statusType(status) {
  const map = { '待发货': 'warning', '已发货': 'primary', '已签收': 'success' }
  return map[status] || 'info'
}

async function loadRecords() {
  try {
    const params = {}
    if (statusFilter.value) params.status = statusFilter.value
    const res = await getShipments(params)
    records.value = res.items
  } catch (e) {}
}

async function updateStatus(id, status) {
  try {
    await updateShipmentStatus(id, { status })
    ElMessage.success(`状态已更新为${status}`)
    loadRecords()
  } catch (e) {}
}

function goToOrder(orderId) {
  if (orderId) {
    router.push('/sales-orders')
  }
}

onMounted(loadRecords)
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 12px;
}

.page-title {
  font-size: 24px;
  font-weight: 700;
  color: var(--primary);
}

.page-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.order-link {
  color: #E65100;
  cursor: pointer;
  text-decoration: underline;
}

/* ===== 送货单打印（A4纵向）===== */
.print-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.5);
  z-index: 1000;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  overflow-y: auto;
  padding: 24px 12px;
}
.print-sheet {
  background: white;
  width: 794px;
  max-width: 100%;
  min-height: 1000px;
  padding: 48px 56px;
  box-sizing: border-box;
  position: relative;
}
.doc-header { text-align: center; margin-bottom: 20px; }
.doc-header h1 { font-size: 26px; letter-spacing: 6px; color: #212121; margin: 0; }
.doc-meta { display: flex; justify-content: space-between; font-size: 15px; margin-bottom: 8px; color: #333; }
.doc-customer { font-size: 15px; margin-bottom: 16px; color: #333; }
.doc-table { width: 100%; border-collapse: collapse; margin-bottom: 16px; }
.doc-table th, .doc-table td {
  border: 1px solid #333;
  padding: 10px 12px;
  font-size: 15px;
  text-align: center;
}
.doc-total { text-align: right; font-size: 17px; margin-bottom: 40px; }
.doc-total span { font-weight: 700; }
.doc-signs { display: flex; justify-content: space-around; font-size: 16px; margin-bottom: 28px; }
.doc-note { text-align: center; font-size: 13px; color: #999; margin-top: 12px; }
.doc-footer {
  position: absolute;
  bottom: 24px;
  left: 56px;
  right: 56px;
  font-size: 12px;
  color: #999;
  border-top: 1px solid #eee;
  padding-top: 8px;
}
.print-actions { text-align: center; margin-top: 24px; }

@media print {
  .print-overlay { position: static; background: none; padding: 0; overflow: visible; }
  .print-sheet { width: 100%; min-height: auto; box-shadow: none; }
  .no-print { display: none !important; }
  body * { visibility: hidden; }
  .print-overlay, .print-overlay * { visibility: visible; }
  .print-overlay { position: absolute; left: 0; top: 0; width: 100%; }
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
  .page-actions {
    flex-direction: column;
    width: 100%;
  }
}
</style>
