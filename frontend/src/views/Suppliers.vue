<template>
  <div class="page">
    <div class="page-header">
      <h2>供应商管理</h2>
      <el-button v-if="canEdit('supplier')" type="primary" @click="openDialog()" size="large">
        + 新增供应商
      </el-button>
    </div>

    <div class="filter-bar">
      <el-input v-model="search" placeholder="搜索供应商名称/联系人/电话" clearable style="width: 280px;" size="large" @clear="loadData" @keyup.enter="loadData" />
      <el-button type="primary" plain @click="loadData" size="large">查询</el-button>
    </div>

    <el-table :data="suppliers" stripe style="width: 100%" size="large">
      <el-table-column prop="name" label="供应商名称" min-width="160" />
      <el-table-column prop="contact" label="联系人" width="120" />
      <el-table-column prop="phone" label="电话" width="140" />
      <el-table-column prop="category" label="供应类别" width="140">
        <template #default="{ row }">
          <el-tag v-if="row.category" size="small">{{ row.category }}</el-tag>
          <span v-else>-</span>
        </template>
      </el-table-column>
      <el-table-column prop="address" label="地址" min-width="180" show-overflow-tooltip />
      <el-table-column prop="notes" label="备注" min-width="140" show-overflow-tooltip />
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <el-button v-if="canEdit('supplier')" link type="primary" @click="openDialog(row)">编辑</el-button>
          <el-button v-if="currentRole === 'boss'" link type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination" v-if="total > pageSize">
      <el-pagination
        background
        layout="prev, pager, next"
        :total="total"
        :page-size="pageSize"
        v-model:current-page="page"
        @current-change="loadData"
      />
    </div>

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑供应商' : '新增供应商'" width="500px" destroy-on-close>
      <el-form :model="form" label-width="80px" size="large">
        <el-form-item label="供应商名称" required>
          <el-input v-model="form.name" placeholder="请输入供应商名称" />
        </el-form-item>
        <el-form-item label="联系人">
          <el-input v-model="form.contact" placeholder="联系人姓名" />
        </el-form-item>
        <el-form-item label="电话">
          <el-input v-model="form.phone" placeholder="联系电话" />
        </el-form-item>
        <el-form-item label="供应类别">
          <el-input v-model="form.category" placeholder="如：巧克力类、乳制品等" />
        </el-form-item>
        <el-form-item label="地址">
          <el-input v-model="form.address" placeholder="地址" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.notes" type="textarea" :rows="2" placeholder="备注信息" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false" size="large">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting" size="large">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { getSuppliers, createSupplier, updateSupplier, deleteSupplier, canEdit } from '../api'
import { ElMessage, ElMessageBox } from 'element-plus'

const suppliers = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = 50
const search = ref('')
const dialogVisible = ref(false)
const isEdit = ref(false)
const editId = ref(null)
const submitting = ref(false)

const currentRole = computed(() => localStorage.getItem('currentRole') || '')

const defaultForm = { name: '', contact: '', phone: '', category: '', address: '', notes: '' }
const form = ref({ ...defaultForm })

async function loadData() {
  const res = await getSuppliers({ search: search.value, page: page.value, page_size: pageSize })
  suppliers.value = res.items
  total.value = res.total
}

function openDialog(row) {
  if (row) {
    isEdit.value = true
    editId.value = row.id
    form.value = { name: row.name, contact: row.contact || '', phone: row.phone || '', category: row.category || '', address: row.address || '', notes: row.notes || '' }
  } else {
    isEdit.value = false
    editId.value = null
    form.value = { ...defaultForm }
  }
  dialogVisible.value = true
}

async function handleSubmit() {
  if (!form.value.name) {
    ElMessage.warning('请输入供应商名称')
    return
  }
  submitting.value = true
  try {
    if (isEdit.value) {
      await updateSupplier(editId.value, form.value)
      ElMessage.success('修改成功')
    } else {
      await createSupplier(form.value)
      ElMessage.success('新增成功')
    }
    dialogVisible.value = false
    loadData()
  } catch (e) {} finally {
    submitting.value = false
  }
}

async function handleDelete(row) {
  await ElMessageBox.confirm(`确定删除供应商「${row.name}」？`, '确认删除', { type: 'warning' })
  await deleteSupplier(row.id)
  ElMessage.success('已删除')
  loadData()
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
.filter-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}
.pagination {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}
</style>
