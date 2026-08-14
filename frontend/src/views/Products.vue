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
        <el-table-column v-if="canEdit('product') || currentRole === 'boss'" label="操作" width="140" fixed="right">
          <template #default="{ row }">
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
import { getProducts, createProduct, updateProduct, adjustProduct, canEdit } from '../api'
import { ElMessage } from 'element-plus'

const isMobile = ref(window.innerWidth <= 768)
window.addEventListener('resize', () => { isMobile.value = window.innerWidth <= 768 })

const currentRole = localStorage.getItem('currentRole') || ''

const products = ref([])
const search = ref('')
const dialogVisible = ref(false)
const editing = ref(null)
const submitting = ref(false)
const categories = ['慕斯', '果酱', '巧克力', '其他']
const units = ['盒', '瓶', '箱', '个']

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
