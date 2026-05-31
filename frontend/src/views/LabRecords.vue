<template>
  <div class="page">
    <div class="page-header">
      <h2 class="page-title">试验室管理</h2>
      <el-button v-if="canEdit('lab')" type="primary" size="large" @click="showDialog()">+ 新增试验</el-button>
    </div>

    <div class="filters">
      <el-select v-model="filters.result" placeholder="结果筛选" clearable @change="load">
        <el-option label="通过" value="通过" />
        <el-option label="不通过" value="不通过" />
        <el-option label="待测" value="待测" />
      </el-select>
    </div>

    <el-card>
      <el-table :data="records" stripe>
        <el-table-column prop="date" label="日期" width="110" />
        <el-table-column prop="name" label="试验名称" min-width="140" />
        <el-table-column label="结果" width="100">
          <template #default="{ row }">
            <el-tag :type="resultType(row.result)" size="large">{{ row.result || '待测' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="评分" width="80">
          <template #default="{ row }">
            <span v-if="row.score" class="score">{{ row.score }}/10</span>
            <span v-else class="no-score">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="process_params" label="工艺参数" min-width="140" show-overflow-tooltip />
        <el-table-column prop="operator" label="操作人" width="90" />
        <el-table-column prop="notes" label="备注" min-width="120" show-overflow-tooltip />
        <el-table-column v-if="canEdit('lab')" label="操作" width="80" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="showDialog(row)">编辑</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="pagination">
        <el-pagination background layout="prev, pager, next" :total="total" :page-size="pageSize" v-model:current-page="page" @current-change="load" />
      </div>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="editing ? '编辑试验' : '新增试验'" width="560px">
      <el-form :model="form" label-width="90px" size="large">
        <el-form-item label="日期" required>
          <el-date-picker v-model="form.date" type="date" value-format="YYYY-MM-DD" style="width:100%" />
        </el-form-item>
        <el-form-item label="试验名称" required>
          <el-input v-model="form.name" placeholder="如：草莓慕斯配方调整" />
        </el-form-item>
        <el-form-item label="配方">
          <el-input v-model="form.recipe" type="textarea" :rows="3" placeholder="配方原料及用量（JSON格式或自由文本）" />
        </el-form-item>
        <el-form-item label="工艺参数">
          <el-input v-model="form.process_params" type="textarea" :rows="2" placeholder="温度、时间、搅拌速度等" />
        </el-form-item>
        <el-form-item label="结果">
          <el-select v-model="form.result" style="width:100%">
            <el-option label="待测" value="待测" />
            <el-option label="通过" value="通过" />
            <el-option label="不通过" value="不通过" />
          </el-select>
        </el-form-item>
        <el-form-item label="评分">
          <el-input-number v-model="form.score" :min="1" :max="10" :step="0.5" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.notes" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getLabRecords, createLabRecord, updateLabRecord, canEdit } from '../api'

const records = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = 50
const filters = ref({ result: '' })
const dialogVisible = ref(false)
const editing = ref(null)

const defaultForm = () => ({
  date: new Date().toISOString().slice(0, 10),
  name: '', recipe: '', process_params: '', result: '待测', score: null, notes: '',
})
const form = ref(defaultForm())

function resultType(r) {
  if (r === '通过') return 'success'
  if (r === '不通过') return 'danger'
  return 'warning'
}

async function load() {
  try {
    const params = { page: page.value, page_size: pageSize }
    if (filters.value.result) params.result = filters.value.result
    const res = await getLabRecords(params)
    records.value = res.items || []
    total.value = res.total || 0
  } catch (e) {}
}

function showDialog(row) {
  if (row) {
    editing.value = row.id
    form.value = { date: row.date, name: row.name || '', recipe: row.recipe || '', process_params: row.process_params || '', result: row.result || '待测', score: row.score, notes: row.notes || '' }
  } else {
    editing.value = null
    form.value = defaultForm()
  }
  dialogVisible.value = true
}

async function submit() {
  if (!form.value.date || !form.value.name) {
    ElMessage.warning('请填写日期和试验名称')
    return
  }
  try {
    if (editing.value) {
      await updateLabRecord(editing.value, form.value)
      ElMessage.success('更新成功')
    } else {
      await createLabRecord(form.value)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    load()
  } catch (e) {}
}

onMounted(load)
</script>

<style scoped>
.page { padding: 0; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-title { font-size: 24px; font-weight: 700; color: var(--primary); margin: 0; }
.filters { margin-bottom: 16px; }
.score { font-weight: 700; color: var(--primary); }
.no-score { color: #ccc; }
.pagination { margin-top: 16px; display: flex; justify-content: center; }
</style>
