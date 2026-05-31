<template>
  <div class="shipment-new-page">
    <div class="page-header">
      <h2 class="page-title">发货登记</h2>
      <el-button @click="$router.push('/shipments')">发货列表</el-button>
    </div>

    <!-- Order info banner -->
    <el-card v-if="orderInfo" class="order-banner" shadow="hover">
      <div class="order-banner-title">关联销售订单: {{ orderInfo.order_no }}</div>
      <div class="order-banner-info">
        <span>客户: {{ orderInfo.customer_name }}</span>
        <span>订单状态: {{ orderInfo.status }}</span>
        <span>订单金额: ¥{{ (orderInfo.total_amount || 0).toFixed(2) }}</span>
      </div>
    </el-card>

    <el-card>
      <el-form :model="form" label-width="100px">
        <el-row :gutter="16">
          <el-col :xs="24" :sm="12">
            <el-form-item label="发货日期">
              <el-date-picker v-model="form.date" type="date" value-format="YYYY-MM-DD" placeholder="选择日期" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12">
            <el-form-item label="客户名称">
              <el-input v-model="form.customer_name" placeholder="客户名称" :disabled="!!fromOrderId" />
            </el-form-item>
          </el-col>

          <!-- Order-based shipment: show product list with remaining qty -->
          <template v-if="fromOrderId && orderProgress.length > 0">
            <el-col :span="24">
              <el-form-item label="发货产品">
                <el-table :data="orderProgress" stripe size="large" style="width: 100%">
                  <el-table-column prop="product_name" label="产品" />
                  <el-table-column label="订单量" width="90" align="center">
                    <template #default="{ row }">{{ row.ordered_qty }} {{ row.unit }}</template>
                  </el-table-column>
                  <el-table-column label="已发" width="80" align="center">
                    <template #default="{ row }">{{ row.shipped_qty }}</template>
                  </el-table-column>
                  <el-table-column label="剩余" width="80" align="center">
                    <template #default="{ row }">
                      <span style="color: #E65100; font-weight: 600;">{{ row.remaining_qty }}</span>
                    </template>
                  </el-table-column>
                  <el-table-column label="本次发货" width="140" align="center">
                    <template #default="{ row }">
                      <el-input-number
                        v-model="row.ship_qty"
                        :min="0"
                        :max="row.remaining_qty"
                        :precision="2"
                        size="default"
                        style="width: 120px;"
                      />
                    </template>
                  </el-table-column>
                </el-table>
              </el-form-item>
            </el-col>
          </template>

          <!-- Standalone shipment: original product select -->
          <template v-if="!fromOrderId">
            <el-col :xs="24" :sm="8">
              <el-form-item label="发货产品">
                <el-select v-model="form.product_id" placeholder="选择产品" style="width: 100%">
                  <el-option v-for="p in products" :key="p.id" :label="`${p.name} (库存:${p.current_stock}${p.unit})`" :value="p.id" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :xs="24" :sm="8">
              <el-form-item label="发货数量">
                <el-input-number v-model="form.quantity" :min="0.01" :precision="2" style="width: 100%" />
              </el-form-item>
            </el-col>
            <el-col :xs="24" :sm="8">
              <el-form-item label="单价">
                <el-input-number v-model="form.unit_price" :min="0" :precision="2" style="width: 100%" />
              </el-form-item>
            </el-col>
          </template>

          <el-col :span="24">
            <el-form-item label="备注">
              <el-input v-model="form.notes" type="textarea" :rows="2" />
            </el-form-item>
          </el-col>
        </el-row>
        <div class="form-actions">
          <el-button type="primary" size="large" @click="handleSubmit" :loading="loading" style="min-width: 200px">
            确认发货
          </el-button>
        </div>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { createShipment, getProducts, getSalesOrder, getOrderShipmentProgress } from '../api'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const products = ref([])
const fromOrderId = ref(route.query.order_id ? parseInt(route.query.order_id) : null)
const orderInfo = ref(null)
const orderProgress = ref([])

const form = ref({
  date: new Date().toISOString().slice(0, 10),
  customer_name: '',
  customer_id: null,
  product_id: null,
  quantity: 0,
  unit_price: null,
  sales_order_id: null,
  notes: '',
})

async function loadOrderData() {
  if (!fromOrderId.value) return
  try {
    const order = await getSalesOrder(fromOrderId.value)
    orderInfo.value = order
    form.value.customer_name = order.customer_name || ''
    form.value.customer_id = order.customer_id
    form.value.sales_order_id = order.id

    const progressRes = await getOrderShipmentProgress(order.id)
    orderProgress.value = (progressRes.progress || [])
      .filter(p => p.remaining_qty > 0)
      .map(p => ({ ...p, ship_qty: 0 }))
  } catch (e) {
    ElMessage.error('加载订单信息失败')
  }
}

async function handleSubmit() {
  if (fromOrderId.value) {
    const itemsToShip = orderProgress.value.filter(p => p.ship_qty > 0)
    if (itemsToShip.length === 0) {
      ElMessage.warning('请至少为一个产品填写发货数量')
      return
    }
    loading.value = true
    try {
      for (const item of itemsToShip) {
        await createShipment({
          date: form.value.date,
          customer_name: form.value.customer_name,
          customer_id: form.value.customer_id,
          product_id: item.product_id,
          quantity: item.ship_qty,
          unit: item.unit,
          unit_price: item.unit_price,
          sales_order_id: fromOrderId.value,
          notes: form.value.notes,
        })
      }
      ElMessage.success(`成功创建 ${itemsToShip.length} 条发货记录`)
      router.push('/shipments')
    } catch (e) {} finally {
      loading.value = false
    }
  } else {
    if (!form.value.customer_name) {
      ElMessage.warning('请输入客户名称')
      return
    }
    if (!form.value.product_id) {
      ElMessage.warning('请选择发货产品')
      return
    }
    if (!form.value.quantity || form.value.quantity <= 0) {
      ElMessage.warning('请输入发货数量')
      return
    }
    loading.value = true
    try {
      await createShipment(form.value)
      ElMessage.success('发货登记成功，产品库存已扣减')
      form.value = {
        date: new Date().toISOString().slice(0, 10),
        customer_name: '', customer_id: null, product_id: null, quantity: 0, unit_price: null, sales_order_id: null, notes: '',
      }
    } catch (e) {} finally {
      loading.value = false
    }
  }
}

onMounted(async () => {
  try {
    const res = await getProducts()
    products.value = res.items
  } catch (e) {}
  if (fromOrderId.value) {
    await loadOrderData()
  }
})
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-title {
  font-size: 24px;
  font-weight: 700;
  color: var(--primary);
}

.order-banner {
  margin-bottom: 16px;
  background: #FFF3E0;
  border: 1px solid #E65100;
}
.order-banner-title {
  font-size: 16px;
  font-weight: 600;
  color: #E65100;
  margin-bottom: 8px;
}
.order-banner-info {
  display: flex;
  gap: 20px;
  font-size: 14px;
  color: #666;
  flex-wrap: wrap;
}

.form-actions {
  text-align: center;
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid var(--border);
}
@media (max-width: 768px) {
  .shipment-new-page { padding: 8px; }
  :deep(.el-form-item__label) { font-size: 13px; }
  .form-actions .el-button { width: 100%; min-width: auto !important; }
  .order-banner-info { flex-direction: column; gap: 4px; }
}
</style>
