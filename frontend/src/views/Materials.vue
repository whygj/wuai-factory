<template>
  <div class="materials-page">
    <div class="page-header">
      <h2 class="page-title">原料管理</h2>
      <div class="page-actions">
        <el-input v-model="search" placeholder="搜索原料..." clearable style="width: 200px" @clear="loadMaterials" @keyup.enter="loadMaterials" />
        <el-button :loading="exporting" @click="handleExport">导出Excel</el-button>
        <el-button type="primary" @click="showAddDialog">新增原料</el-button>
      </div>
    </div>

    <!-- Materials Table -->
    <el-card>
      <el-table :data="materials" stripe style="width: 100%" class="hidden-mobile">
        <el-table-column prop="name" label="原料名称" min-width="120" />
        <el-table-column prop="category" label="分类" width="120" />
        <el-table-column prop="current_stock" label="当前库存" width="120">
          <template #default="{ row }">
            <span :class="{ 'low-stock': row.current_stock <= row.safety_stock && row.safety_stock > 0 }">
              {{ row.current_stock }} {{ row.unit }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="safety_stock" label="安全线" width="100">
          <template #default="{ row }">{{ row.safety_stock }} {{ row.unit }}</template>
        </el-table-column>
        <el-table-column prop="supplier" label="供应商" width="120" />
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="openInbound(row)">入库</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="card-list visible-mobile">
        <div class="record-card" v-for="item in materials" :key="item.id">
          <div class="card-main">
            <div class="card-title">{{ item.name }}</div>
            <el-tag v-if="item.category" size="small">{{ item.category }}</el-tag>
          </div>
          <div class="card-info">
            <span>库存: <span :class="{ 'low-stock': item.current_stock <= item.safety_stock && item.safety_stock > 0 }">{{ item.current_stock }}</span> {{ item.unit }}</span>
            <span>安全线: {{ item.safety_stock }} {{ item.unit }}</span>
          </div>
          <div class="card-info" v-if="item.supplier">
            <span>供应商: {{ item.supplier }}</span>
          </div>
          <div class="card-actions">
            <el-button size="small" type="primary" @click="openInbound(item)">入库</el-button>
          </div>
        </div>
      </div>
    </el-card>

    <!-- Add Material Dialog -->
    <el-dialog v-model="addDialogVisible" title="新增原料" :width="isMobile ? '90%' : '500px'">
      <el-form :model="addForm" label-width="80px">
        <el-form-item label="名称">
          <el-input v-model="addForm.name" placeholder="原料名称" />
        </el-form-item>
        <el-form-item label="分类">
          <el-select v-model="addForm.category" placeholder="选择分类" style="width: 100%">
            <el-option v-for="c in categories" :key="c" :label="c" :value="c" />
          </el-select>
        </el-form-item>
        <el-form-item label="单位">
          <el-select v-model="addForm.unit" placeholder="选择单位" style="width: 100%">
            <el-option v-for="u in units" :key="u" :label="u" :value="u" />
          </el-select>
        </el-form-item>
        <el-form-item label="安全线">
          <el-input-number v-model="addForm.safety_stock" :min="0" style="width: 100%" />
        </el-form-item>
        <el-form-item label="供应商">
          <el-input v-model="addForm.supplier" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="addDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleAdd">确认新增</el-button>
      </template>
    </el-dialog>

    <!-- Inbound Dialog -->
    <el-dialog v-model="inboundDialogVisible" :title="`入库 - ${currentMaterial?.name || ''}`" :width="isMobile ? '90%' : '500px'">
      <el-form :model="inboundForm" label-width="80px">
        <el-form-item label="入库数量">
          <el-input-number v-model="inboundForm.quantity" :min="0.01" :precision="2" style="width: 100%" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="inboundForm.notes" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="inboundDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleInbound">确认入库</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getMaterials, createMaterial, inboundMaterial, downloadExport } from '../api'
import { ElMessage } from 'element-plus'

const isMobile = ref(window.innerWidth <= 768)
window.addEventListener('resize', () => { isMobile.value = window.innerWidth <= 768 })

const search = ref('')
const materials = ref([])
const addDialogVisible = ref(false)
const inboundDialogVisible = ref(false)
const currentMaterial = ref(null)
const exporting = ref(false)

const categories = ['巧克力类', '油脂类', '果酱类', '乳制品', '粉类', '糖浆类', '添加剂']
const units = ['kg', '桶', '件', '袋', '瓶']

const addForm = ref({ name: '', category: '', unit: 'kg', safety_stock: 0, supplier: '' })
const inboundForm = ref({ quantity: 0, notes: '' })

async function loadMaterials() {
  try {
    const res = await getMaterials({ search: search.value })
    materials.value = res.items
  } catch (e) {}
}

function showAddDialog() {
  addForm.value = { name: '', category: '', unit: 'kg', safety_stock: 0, supplier: '' }
  addDialogVisible.value = true
}

async function handleAdd() {
  if (!addForm.value.name) {
    ElMessage.warning('请输入原料名称')
    return
  }
  try {
    await createMaterial(addForm.value)
    ElMessage.success('新增成功')
    addDialogVisible.value = false
    loadMaterials()
  } catch (e) {}
}

async function handleExport() {
  exporting.value = true
  try {
    await downloadExport('inventory', {}, '库存快照')
    ElMessage.success('导出成功')
  } catch (e) {} finally {
    exporting.value = false
  }
}

function openInbound(row) {
  currentMaterial.value = row
  inboundForm.value = { quantity: 0, notes: '' }
  inboundDialogVisible.value = true
}

async function handleInbound() {
  if (!inboundForm.value.quantity || inboundForm.value.quantity <= 0) {
    ElMessage.warning('请输入入库数量')
    return
  }
  try {
    await inboundMaterial(currentMaterial.value.id, {
      quantity: inboundForm.value.quantity,
      notes: inboundForm.value.notes,
    })
    ElMessage.success('入库成功')
    inboundDialogVisible.value = false
    loadMaterials()
  } catch (e) {}
}

onMounted(loadMaterials)
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

.low-stock {
  color: var(--danger);
  font-weight: 700;
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
  .page-header {
    flex-direction: column;
    align-items: stretch;
  }
  .page-actions {
    flex-direction: column;
  }
  .page-actions .el-input { width: 100% !important; }
  :deep(.el-form-item__label) { font-size: 13px; }
  :deep(.el-dialog) { margin: 8px auto; }
}
</style>
