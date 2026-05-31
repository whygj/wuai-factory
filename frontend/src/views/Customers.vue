<template>
  <div class="page">
    <div class="page-header">
      <h2>客户管理</h2>
      <el-button v-if="canEdit('customer')" type="primary" @click="openDialog()" size="large">
        + 新增客户
      </el-button>
    </div>

    <div class="filter-bar">
      <el-input v-model="search" placeholder="搜索客户名称/联系人/电话" clearable style="width: 260px;" size="large" @clear="loadData" @keyup.enter="loadData" />
      <el-select v-model="typeFilter" placeholder="客户类型" clearable style="width: 140px;" size="large" @change="loadData">
        <el-option label="经销商" value="经销商" />
        <el-option label="直客" value="直客" />
        <el-option label="电商" value="电商" />
      </el-select>
      <el-button type="primary" plain @click="loadData" size="large">查询</el-button>
    </div>

    <el-table :data="customers" stripe style="width: 100%" size="large">
      <el-table-column prop="name" label="客户名称" min-width="140" />
      <el-table-column prop="contact" label="联系人" width="120" />
      <el-table-column prop="phone" label="电话" width="140" />
      <el-table-column prop="type" label="类型" width="100">
        <template #default="{ row }">
          <el-tag v-if="row.type" :type="row.type === 'VIP' ? 'warning' : 'info'" size="small">{{ row.type }}</el-tag>
          <span v-else>-</span>
        </template>
      </el-table-column>
      <el-table-column prop="level" label="等级" width="100">
        <template #default="{ row }">
          <el-tag v-if="row.level" :type="row.level === '核心' ? 'danger' : row.level === 'VIP' ? 'warning' : ''" size="small">{{ row.level }}</el-tag>
          <span v-else>-</span>
        </template>
      </el-table-column>
      <el-table-column prop="address" label="地址" min-width="160" show-overflow-tooltip />
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <el-button v-if="canEdit('customer')" link type="primary" @click="openDialog(row)">编辑</el-button>
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

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑客户' : '新增客户'" width="500px" destroy-on-close>
      <el-form :model="form" label-width="80px" size="large">
        <el-form-item label="客户名称" required>
          <el-input v-model="form.name" placeholder="请输入客户名称" />
        </el-form-item>
        <el-form-item label="联系人">
          <el-input v-model="form.contact" placeholder="联系人姓名" />
        </el-form-item>
        <el-form-item label="电话">
          <el-input v-model="form.phone" placeholder="联系电话" />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="form.type" placeholder="选择类型" style="width: 100%">
            <el-option label="经销商" value="经销商" />
            <el-option label="直客" value="直客" />
            <el-option label="电商" value="电商" />
          </el-select>
        </el-form-item>
        <el-form-item label="等级">
          <el-select v-model="form.level" placeholder="选择等级" style="width: 100%">
            <el-option label="普通" value="普通" />
            <el-option label="VIP" value="VIP" />
            <el-option label="核心" value="核心" />
          </el-select>
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
import { getCustomers, createCustomer, updateCustomer, deleteCustomer, canEdit } from '../api'
import { ElMessage, ElMessageBox } from 'element-plus'

const customers = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = 50
const search = ref('')
const typeFilter = ref('')
const dialogVisible = ref(false)
const isEdit = ref(false)
const editId = ref(null)
const submitting = ref(false)

const currentRole = computed(() => localStorage.getItem('currentRole') || '')

const defaultForm = { name: '', contact: '', phone: '', type: '', level: '普通', address: '', notes: '' }
const form = ref({ ...defaultForm })

async function loadData() {
  const res = await getCustomers({ search: search.value, type: typeFilter.value, page: page.value, page_size: pageSize })
  customers.value = res.items
  total.value = res.total
}

function openDialog(row) {
  if (row) {
    isEdit.value = true
    editId.value = row.id
    form.value = { name: row.name, contact: row.contact || '', phone: row.phone || '', type: row.type || '', level: row.level || '普通', address: row.address || '', notes: row.notes || '' }
  } else {
    isEdit.value = false
    editId.value = null
    form.value = { ...defaultForm }
  }
  dialogVisible.value = true
}

async function handleSubmit() {
  if (!form.value.name) {
    ElMessage.warning('请输入客户名称')
    return
  }
  submitting.value = true
  try {
    if (isEdit.value) {
      await updateCustomer(editId.value, form.value)
      ElMessage.success('修改成功')
    } else {
      await createCustomer(form.value)
      ElMessage.success('新增成功')
    }
    dialogVisible.value = false
    loadData()
  } catch (e) {} finally {
    submitting.value = false
  }
}

async function handleDelete(row) {
  await ElMessageBox.confirm(`确定删除客户「${row.name}」？`, '确认删除', { type: 'warning' })
  await deleteCustomer(row.id)
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
