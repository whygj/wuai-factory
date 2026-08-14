<template>
  <div class="page">
    <div class="page-header">
      <h2 class="page-title">产品库存</h2>
      <el-button v-if="canEdit('product')" type="primary" size="large" @click="openDialog()">+ 新增产品</el-button>
    </div>

    <div class="toolbar">
      <el-input v-model="search" placeholder="搜索产品" clearable @input="load" style="max-width:300px" />
    </div>

    <el-card>
      <el-table :data="products" stripe class="hidden-mobile">
        <el-table-column prop="name" label="产品名称" min-width="160" />
        <el-table-column prop="category" label="类别" width="100" />
        <el-table-column prop="spec" label="规格" width="100" />
        <el-table-column prop="current_stock" label="库存" width="100">
          <template #default="{ row }">
            <span :class="{ 'low-stock': row.current_stock <= 10 }">{{ row.current_stock }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="unit" label="单位" width="70" />
        <el-table-column v-if="canEdit('product') || currentRole === 'boss'" label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button link type="success" @click="openBomDialog(row)">配方</el-button>
            <el-button v-if="canEdit('product')" link type="primary" @click="openDialog(row)">编辑</el-button>
            <el-button v-if="currentRole === 'boss'" link type="warning" @click="openAdjust(row)">盘点</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="card-list visible-mobile">
        <div class="record-card" v-for="item in products" :key="item.id">
          <div class="card-main">
            <div class="card-title">{{ item.name }}</div>
            <el-tag v-if="item.category" size="small">{{ item.category }}</el-tag>
          </div>
          <div class="card-info">
            <span>库存: <span :class="{ 'low-stock': item.current_stock <= 10 }">{{ item.current_stock }}</span> {{ item.unit }}</span>
            <span v-if="item.spec">规格: {{ item.spec }}</span>
          </div>
          <div class="card-actions" v-if="canEdit('product') || currentRole === 'boss'">
            <el-button size="small" type="success" plain @click="openBomDialog(item)">配方</el-button>
            <el-button v-if="canEdit('product')" size="small" @click="openDialog(item)">编辑</el-button>
            <el-button v-if="currentRole === 'boss'" size="small" type="warning" plain @click="openAdjust(item)">盘点</el-button>
          </div>
        </div>
      </div>
    </el-card>

    <!-- Add/Edit Dialog -->
    <el-dialog v-model="dialogVisible" :title="editing ? '编辑产品' : '新增产品'" :width="isMobile ? '90%' : '480px'" destroy-on-close>
      <el-form :model="form" label-width="80px" size="large">
        <el-form-item label="名称" required>
          <el-input v-model="form.name" placeholder="产品名称" />
        </el-form-item>
        <el-form-item label="类别">
          <el-select v-model="form.category" placeholder="选择类别" style="width: 100%" clearable>
            <el-option v-for="c in categories" :key="c" :label="c" :value="c" />
          </el-select>
        </el-form-item>
        <el-form-item label="单位">
          <el-select v-model="form.unit" placeholder="选择单位" style="width: 100%">
            <el-option v-for="u in units" :key="u" :label="u" :value="u" />
          </el-select>
        </el-form-item>
        <el-form-item label="规格">
          <el-input v-model="form.spec" placeholder="如 200g/盒" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.notes" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false" size="large">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting" size="large">保存</el-button>
      </template>
    </el-dialog>

    <!-- BOM Dialog -->
    <el-dialog v-model="bomDialogVisible" :title="`配方 - ${bomProduct?.name || ''}`" :width="isMobile ? '95%' : '640px'" destroy-on-close>
      <div v-if="!canEditBom" class="bom-readonly-hint">当前角色只读（配方维护：老板/班长）</div>
      <el-form :model="bomForm" label-width="90px" size="large">
        <el-form-item label="基准批量">
          <div style="display:flex; gap:8px; width:100%;">
            <el-input-number v-model="bomForm.base_quantity" :min="0.01" :precision="2" style="width: 160px;" />
            <el-input v-model="bomForm.base_unit" placeholder="单位（如 盒）" style="width: 120px;" />
            <span class="bom-hint">每 {{ bomForm.base_quantity }}{{ bomForm.base_unit }} 的用料如下</span>
          </div>
        </el-form-item>
        <el-form-item label="原料明细">
          <div style="width: 100%;">
            <div v-for="(item, idx) in bomForm.items" :key="idx" class="bom-row">
              <el-select v-model="item.material_id" placeholder="选择原料" style="flex: 1;" filterable>
                <el-option v-for="m in materialList" :key="m.id" :label="m.name" :value="m.id" />
              </el-select>
              <el-input-number v-model="item.material_quantity" :min="0.01" :precision="2" placeholder="用量" style="width: 130px;" />
              <span class="bom-unit">{{ getBomUnit(item.material_id) }}</span>
              <el-button v-if="canEditBom" link type="danger" @click="bomForm.items.splice(idx, 1)">删</el-button>
            </div>
            <el-button v-if="canEditBom" type="primary" plain @click="addBomItem" style="margin-top: 8px; width: 100%;">+ 添加原料</el-button>
          </div>
        </el-form-item>
      </el-form>
      <div class="bom-cost" v-if="bomCostPreview">
        <div>每{{ bomForm.base_quantity }}{{ bomForm.base_unit }}原料成本：<b>¥{{ bomCostPreview.base_cost.toFixed(2) }}</b></div>
        <div>单位成本：<b style="color:#E65100;">¥{{ bomCostPreview.unit_cost.toFixed(3) }}</b> / {{ bomForm.base_unit }}</div>
      </div>
      <div class="bom-cost" v-else style="color:#999;">成本试算需要原料档案价（未设进价的原料按0计）</div>
      <template #footer>
        <el-button @click="bomDialogVisible = false" size="large">关闭</el-button>
        <el-button v-if="canEditBom" type="primary" @click="handleSaveBom" :loading="bomSaving" size="large">保存配方</el-button>
      </template>
    </el-dialog>

    <!-- Stocktake Adjust Dialog (boss only) -->
    <el-dialog v-model="adjustDialogVisible" :title="`盘点 - ${adjustTarget?.name || ''}`" :width="isMobile ? '90%' : '480px'" destroy-on-close>
      <el-form :model="adjustForm" label-width="80px" size="large">
        <el-form-item label="账面库存">
          <div class="book-stock">{{ adjustTarget?.current_stock }} {{ adjustTarget?.unit }}</div>
        </el-form-item>
        <el-form-item label="实际数量" required>
          <el-input-number v-model="adjustForm.actual_stock" :min="0" :precision="2" style="width: 100%" />
        </el-form-item>
        <el-form-item label="盘点原因" required>
          <el-input v-model="adjustForm.reason" type="textarea" :rows="2" placeholder="如：搬运破损2盒" />
        </el-form-item>
      </el-form>
      <div class="adjust-diff" v-if="adjustDiff !== null && adjustDiff !== 0"
           :class="{ 'diff-up': adjustDiff > 0, 'diff-down': adjustDiff < 0 }">
        {{ adjustDiff > 0 ? `盘盈 +${adjustDiff}` : `盘亏 ${adjustDiff}` }} {{ adjustTarget?.unit }}
      </div>
      <div class="adjust-diff diff-zero" v-else-if="adjustDiff === 0">账实一致，无需调整</div>
      <template #footer>
        <el-button @click="adjustDialogVisible = false" size="large">取消</el-button>
        <el-button type="primary" @click="handleAdjust" :loading="adjusting" size="large" :disabled="adjustDiff === null || adjustDiff === 0">确认调整</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getProducts, createProduct, updateProduct, adjustProduct, canEdit, getBom, saveBom, getMaterials } from '../api'
import { ElMessage } from 'element-plus'

const isMobile = ref(window.innerWidth <= 768)
window.addEventListener('resize', () => { isMobile.value = window.innerWidth <= 768 })

const currentRole = localStorage.getItem('currentRole') || ''
// 配方维护：boss + leader（班长最懂配方）
const canEditBom = ['boss', 'leader'].includes(currentRole)

const products = ref([])
const search = ref('')
const dialogVisible = ref(false)
const editing = ref(null)
const submitting = ref(false)
const categories = ['慕斯', '果酱', '巧克力', '其他']
const units = ['盒', '瓶', '箱', '个']

const bomDialogVisible = ref(false)
const bomSaving = ref(false)
const bomProduct = ref(null)
const materialList = ref([])
const bomForm = ref({ base_quantity: 100, base_unit: '盒', items: [] })

function getBomUnit(materialId) {
  const m = materialList.value.find(x => x.id === materialId)
  return m ? m.unit : ''
}

const bomCostPreview = computed(() => {
  if (!bomForm.value.items.length) return null
  const baseCost = bomForm.value.items.reduce((sum, item) => {
    const m = materialList.value.find(x => x.id === item.material_id)
    return sum + (item.material_quantity || 0) * ((m && m.purchase_price) || 0)
  }, 0)
  if (!bomForm.value.base_quantity) return null
  return { base_cost: baseCost, unit_cost: baseCost / bomForm.value.base_quantity }
})

async function openBomDialog(row) {
  bomProduct.value = row
  if (!materialList.value.length) {
    const res = await getMaterials({ page_size: 200 })
    materialList.value = res.items
  }
  const bom = await getBom(row.id)
  if (bom && bom.items && bom.items.length) {
    bomForm.value = {
      base_quantity: bom.base_quantity,
      base_unit: bom.base_unit,
      items: bom.items.map(i => ({ material_id: i.material_id, material_quantity: i.material_quantity })),
    }
  } else {
    bomForm.value = { base_quantity: 100, base_unit: row.unit || '盒', items: [] }
  }
  bomDialogVisible.value = true
}

function addBomItem() {
  bomForm.value.items.push({ material_id: null, material_quantity: 1 })
}

async function handleSaveBom() {
  if (!bomForm.value.base_quantity || bomForm.value.base_quantity <= 0) {
    ElMessage.warning('请填写基准批量')
    return
  }
  if (!bomForm.value.base_unit) {
    ElMessage.warning('请填写基准批量单位')
    return
  }
  const items = bomForm.value.items.filter(i => i.material_id && i.material_quantity > 0)
  if (items.length === 0) {
    ElMessage.warning('配方至少需要一行原料')
    return
  }
  bomSaving.value = true
  try {
    await saveBom(bomProduct.value.id, {
      base_quantity: bomForm.value.base_quantity,
      base_unit: bomForm.value.base_unit,
      items: items.map(i => ({ material_id: i.material_id, material_quantity: i.material_quantity })),
    })
    ElMessage.success('配方已保存')
    bomDialogVisible.value = false
  } catch (e) {} finally {
    bomSaving.value = false
  }
}

const adjustDialogVisible = ref(false)
const adjusting = ref(false)
const adjustTarget = ref(null)
const adjustForm = ref({ actual_stock: null, reason: '' })

const adjustDiff = computed(() => {
  if (adjustForm.value.actual_stock === null || adjustForm.value.actual_stock === undefined || !adjustTarget.value) return null
  return Math.round(((adjustForm.value.actual_stock - adjustTarget.value.current_stock) + Number.EPSILON) * 100) / 100
})

const form = ref({ name: '', category: '', unit: '盒', spec: '', notes: '' })

async function load() {
  try {
    const res = await getProducts({ search: search.value })
    products.value = res.items || []
  } catch (e) {}
}

function openDialog(row) {
  editing.value = row || null
  form.value = row
    ? { name: row.name, category: row.category || '', unit: row.unit || '盒', spec: row.spec || '', notes: row.notes || '' }
    : { name: '', category: '', unit: '盒', spec: '', notes: '' }
  dialogVisible.value = true
}

async function handleSubmit() {
  if (!form.value.name) {
    ElMessage.warning('请输入产品名称')
    return
  }
  submitting.value = true
  try {
    if (editing.value) {
      await updateProduct(editing.value.id, form.value)
      ElMessage.success('保存成功')
    } else {
      await createProduct(form.value)
      ElMessage.success('新增成功')
    }
    dialogVisible.value = false
    load()
  } catch (e) {} finally {
    submitting.value = false
  }
}

function openAdjust(row) {
  adjustTarget.value = row
  adjustForm.value = { actual_stock: row.current_stock, reason: '' }
  adjustDialogVisible.value = true
}

async function handleAdjust() {
  if (adjustForm.value.actual_stock === null || adjustForm.value.actual_stock < 0) {
    ElMessage.warning('请输入实际清点数量')
    return
  }
  if (!adjustForm.value.reason || adjustForm.value.reason.trim().length < 2) {
    ElMessage.warning('请填写盘点原因（至少2个字）')
    return
  }
  adjusting.value = true
  try {
    const res = await adjustProduct(adjustTarget.value.id, {
      actual_stock: adjustForm.value.actual_stock,
      reason: adjustForm.value.reason.trim(),
    })
    ElMessage.success(`已调整：账面 ${res.old_stock} → 实际 ${res.new_stock}（${res.diff > 0 ? '+' : ''}${res.diff}）`)
    adjustDialogVisible.value = false
    load()
  } catch (e) {} finally {
    adjusting.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.page-title { font-size: 24px; font-weight: 700; color: var(--primary); margin-bottom: 16px; }
.toolbar { margin-bottom: 16px; }
.low-stock { color: #F44336; font-weight: 700; }
.book-stock {
  background: #f5f5f5;
  border-radius: 6px;
  padding: 8px 12px;
  font-size: 16px;
  font-weight: 600;
  color: #666;
  width: 100%;
}
.adjust-diff {
  margin: 8px 0 0 80px;
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 15px;
  font-weight: 700;
}
.adjust-diff.diff-up { background: #E8F5E9; color: #2E7D32; }
.adjust-diff.diff-down { background: #FFEBEE; color: #C62828; }
.adjust-diff.diff-zero { background: #f5f5f5; color: #999; font-weight: 400; }
.bom-readonly-hint { margin-bottom: 12px; color: #999; font-size: 13px; }
.bom-row { display: flex; gap: 8px; align-items: center; margin-bottom: 8px; flex-wrap: wrap; }
.bom-unit { font-size: 13px; color: #999; min-width: 30px; }
.bom-hint { font-size: 13px; color: #999; }
.bom-cost {
  margin-top: 12px;
  padding: 12px 16px;
  background: #FFF3E0;
  border-radius: 8px;
  font-size: 15px;
  display: flex;
  gap: 32px;
  flex-wrap: wrap;
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
  .toolbar .el-input { max-width: 100% !important; }
}
</style>
