<template>
  <div class="production-list-page">
    <div class="page-header">
      <h2 class="page-title">生产记录</h2>
      <div class="page-actions">
        <el-date-picker v-model="dateRange" type="daterange" range-separator="至" start-placeholder="开始日期" end-placeholder="结束日期" value-format="YYYY-MM-DD" @change="loadRecords" style="max-width: 300px" />
        <el-button type="primary" @click="$router.push('/production/new')">新建记录</el-button>
      </div>
    </div>

    <el-card>
      <el-table :data="records" stripe style="width: 100%">
        <el-table-column prop="date" label="日期" width="120" />
        <el-table-column prop="product_name" label="产品" min-width="140" />
        <el-table-column prop="quantity" label="数量" width="100">
          <template #default="{ row }">{{ row.quantity }} {{ row.unit }}</template>
        </el-table-column>
        <el-table-column prop="sugar_degree" label="糖度" width="80" />
        <el-table-column prop="operator" label="操作人" width="80" />
        <el-table-column prop="notes" label="备注" min-width="120" show-overflow-tooltip />
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getProduction } from '../api'

const records = ref([])
const dateRange = ref(null)

async function loadRecords() {
  try {
    const params = { page: 1, page_size: 100 }
    if (dateRange.value && dateRange.value.length === 2) {
      params.start_date = dateRange.value[0]
      params.end_date = dateRange.value[1]
    }
    const res = await getProduction(params)
    records.value = res.items
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
