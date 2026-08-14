<template>
  <div class="production-page">
    <div class="page-header">
      <h2 class="page-title">生产登记</h2>
      <el-button @click="$router.push('/production')">查看记录</el-button>
    </div>

    <el-card>
      <el-form :model="form" label-width="100px" class="production-form">
        <el-row :gutter="16">
          <el-col :xs="24" :sm="12">
            <el-form-item label="生产日期">
              <el-date-picker v-model="form.date" type="date" value-format="YYYY-MM-DD" placeholder="选择日期" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12">
            <el-form-item label="生产产品">
              <el-select v-model="form.product_id" placeholder="选择产品" style="width: 100%" @change="onProductOrQtyChange">
                <el-option v-for="p in products" :key="p.id" :label="`${p.name} (${p.unit})`" :value="p.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="8">
            <el-form-item label="生产数量">
              <el-input-number v-model="form.quantity" :min="0.01" :precision="2" style="width: 100%" @change="onProductOrQtyChange" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="8">
            <el-form-item label="糖度">
              <el-input-number v-model="form.sugar_degree" :min="0" :precision="1" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="8">
            <el-form-item label="备注">
              <el-input v-model="form.notes" />
            </el-form-item>
          </el-col>
        </el-row>

        <!-- Raw Materials Usage -->
        <el-divider>消耗原料</el-divider>
        <el-alert v-if="noBomHint" type="info" :closable="false" class="no-bom-alert"
          :title="noBomHint" />
        <el-alert v-else-if="bomApplied" type="success" :closable="false" class="no-bom-alert"
          :title="`已按配方预填（每${bomBaseText}），用量可修改`" />
        <div v-for="(item, idx) in form.raw_materials_used" :key="idx" class="material-row">
          <div v-if="item.insufficient" class="insufficient-warn">库存不足，当前 {{ item.current_stock }} 需 {{ item.quantity }}</div>
          <el-row :gutter="12" align="middle">
            <el-col :span="10">
              <el-select v-model="item.material_id" placeholder="选择原料" style="width: 100%">
                <el-option v-for="m in materials" :key="m.id" :label="`${m.name} (库存:${m.current_stock}${m.unit})`" :value="m.id" />
              </el-select>
            </el-col>
            <el-col :span="8">
              <el-input-number v-model="item.quantity" :min="0.01" :precision="2" placeholder="数量" style="width: 100%" @change="onQtyChange(idx)" />
            </el-col>
            <el-col :span="4">
              <span class="material-unit">{{ getMaterialUnit(item.material_id) }}</span>
            </el-col>
            <el-col :span="2">
              <el-button type="danger" circle size="small" @click="removeMaterial(idx)">-</el-button>
            </el-col>
          </el-row>
          <div v-if="item.batch_preview && item.batch_preview.length" class="batch-preview">
            将消耗：{{ item.batch_preview.map(p => `${p.batch_no}(${p.take})`).join(' → ') }}
          </div>
        </div>
        <el-button type="primary" plain @click="addMaterial" style="margin-top: 12px">+ 添加消耗原料</el-button>

        <div class="form-actions">
          <el-button type="primary" size="large" @click="handleSubmit" :loading="loading" style="min-width: 200px">
            提交生产记录
          </el-button>
        </div>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { createProduction, getProducts, getMaterials, previewBatchUsage, previewBom } from '../api'
import { ElMessage } from 'element-plus'

const loading = ref(false)
const products = ref([])
const materials = ref([])
const noBomHint = ref('')
const bomApplied = ref(false)
const bomBaseText = ref('')

let bomTimer = null
function onProductOrQtyChange() {
  // 防抖查配方预填（纯计算接口）
  clearTimeout(bomTimer)
  bomTimer = setTimeout(applyBomPreview, 400)
}

async function applyBomPreview() {
  bomApplied.value = false
  noBomHint.value = ''
  if (!form.value.product_id || !form.value.quantity || form.value.quantity <= 0) return
  try {
    const res = await previewBom({ product_id: form.value.product_id, quantity: form.value.quantity })
    if (!res.has_bom) {
      noBomHint.value = '该产品未设配方，可在「产品库存→配方」中设置；下方手动填写用量'
      return
    }
    bomBaseText.value = `${res.base_quantity}${res.base_unit}`
    // 预填全部原料（每行可改，提交时用的是这里的值）
    form.value.raw_materials_used = res.items.map(i => ({
      material_id: i.material_id,
      quantity: i.needed_quantity,
      unit: i.material_unit,
      batch_preview: [],
      insufficient: !i.sufficient,
      current_stock: i.current_stock,
    }))
    bomApplied.value = true
    // 预填后刷新各行FEFO预览
    form.value.raw_materials_used.forEach((_, idx) => loadBatchPreview(idx))
  } catch (e) {}
}

const form = ref({
  date: new Date().toISOString().slice(0, 10),
  product_id: null,
  quantity: 0,
  sugar_degree: null,
  notes: '',
  raw_materials_used: [],
})

function getMaterialUnit(id) {
  const m = materials.value.find(m => m.id === id)
  return m ? m.unit : ''
}

function addMaterial() {
  form.value.raw_materials_used.push({ material_id: null, quantity: 0, unit: '', batch_preview: [] })
}

function removeMaterial(idx) {
  form.value.raw_materials_used.splice(idx, 1)
}

let previewTimer = null
function onQtyChange(idx) {
  // 手改用量后重检库存充足标志
  const item = form.value.raw_materials_used[idx]
  if (item && item.material_id) {
    const m = materials.value.find(x => x.id === item.material_id)
    if (m) {
      item.current_stock = m.current_stock
      item.insufficient = item.quantity > m.current_stock
    }
  }
  // 防抖300ms查FEFO预览（只读提示，班长不手选批次）
  clearTimeout(previewTimer)
  previewTimer = setTimeout(() => loadBatchPreview(idx), 300)
}

async function loadBatchPreview(idx) {
  const item = form.value.raw_materials_used[idx]
  if (!item || !item.material_id || !item.quantity || item.quantity <= 0) {
    if (item) item.batch_preview = []
    return
  }
  try {
    item.batch_preview = await previewBatchUsage(item.material_id, item.quantity)
  } catch (e) {
    item.batch_preview = []
  }
}

async function handleSubmit() {
  if (!form.value.product_id) {
    ElMessage.warning('请选择生产产品')
    return
  }
  if (!form.value.quantity || form.value.quantity <= 0) {
    ElMessage.warning('请输入生产数量')
    return
  }

  const materialsUsed = form.value.raw_materials_used
    .filter(m => m.material_id && m.quantity > 0)
    .map(m => ({
      material_id: m.material_id,
      quantity: m.quantity,
      unit: getMaterialUnit(m.material_id),
    }))

  loading.value = true
  try {
    await createProduction({
      date: form.value.date,
      product_id: form.value.product_id,
      quantity: form.value.quantity,
      sugar_degree: form.value.sugar_degree,
      notes: form.value.notes,
      raw_materials_used: materialsUsed,
    })
    ElMessage.success('生产记录已提交，库存已更新')
    form.value = {
      date: new Date().toISOString().slice(0, 10),
      product_id: null, quantity: 0, sugar_degree: null, notes: '', raw_materials_used: [],
    }
  } catch (e) {} finally {
    loading.value = false
  }
}

onMounted(async () => {
  try {
    const [pRes, mRes] = await Promise.all([getProducts(), getMaterials()])
    products.value = pRes.items
    materials.value = mRes.items
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

.material-row {
  margin-bottom: 8px;
}

.material-unit {
  font-size: 14px;
  color: var(--text-light);
  line-height: 44px;
}

.batch-preview {
  margin: 2px 0 8px;
  padding: 6px 10px;
  background: #FFF3E0;
  border-radius: 6px;
  font-size: 13px;
  color: #E65100;
}
.no-bom-alert {
  margin-bottom: 12px;
}
.insufficient-warn {
  margin-bottom: 4px;
  padding: 4px 10px;
  background: #FFEBEE;
  border-radius: 6px;
  font-size: 13px;
  color: #C62828;
  font-weight: 600;
}

.form-actions {
  text-align: center;
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid var(--border);
}
@media (max-width: 768px) {
  .production-page { padding: 8px; }
  :deep(.el-form-item__label) { font-size: 13px; }
  .form-actions .el-button { width: 100%; min-width: auto !important; }
}
</style>
