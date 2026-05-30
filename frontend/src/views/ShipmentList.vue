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
      <el-table :data="records" stripe style="width: 100%">
        <el-table-column prop="date" label="日期" width="120" />
        <el-table-column prop="customer_name" label="客户" min-width="120" />
        <el-table-column prop="product_name" label="产品" min-width="140" />
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
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <template v-if="row.status === '待发货'">
              <el-button size="small" type="primary" @click="updateStatus(row.id, '已发货')">发货</el-button>
            </template>
            <template v-if="row.status === '已发货'">
              <el-button size="small" type="success" @click="updateStatus(row.id, '已签收')">签收</el-button>
            </template>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getShipments, updateShipmentStatus } from '../api'
import { ElMessage } from 'element-plus'

const records = ref([])
const statusFilter = ref('')

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

@media (max-width: 768px) {
  .page-actions {
    flex-direction: column;
    width: 100%;
  }
}
</style>
