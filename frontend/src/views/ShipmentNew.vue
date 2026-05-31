<template>
  <div class="shipment-new-page">
    <div class="page-header">
      <h2 class="page-title">发货登记</h2>
      <el-button @click="$router.push('/shipments')">发货列表</el-button>
    </div>

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
              <el-input v-model="form.customer_name" placeholder="客户名称" />
            </el-form-item>
          </el-col>
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
import { createShipment, getProducts } from '../api'
import { ElMessage } from 'element-plus'

const loading = ref(false)
const products = ref([])
const form = ref({
  date: new Date().toISOString().slice(0, 10),
  customer_name: '',
  product_id: null,
  quantity: 0,
  unit_price: null,
  notes: '',
})

async function handleSubmit() {
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
      customer_name: '', product_id: null, quantity: 0, unit_price: null, notes: '',
    }
  } catch (e) {} finally {
    loading.value = false
  }
}

onMounted(async () => {
  try {
    const res = await getProducts()
    products.value = res.items
  } catch (e) {}
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
}
</style>
