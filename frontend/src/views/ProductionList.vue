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
      <el-table :data="records" stripe style="width: 100%" class="hidden-mobile">
        <el-table-column prop="date" label="日期" width="120" />
        <el-table-column prop="product_name" label="产品" min-width="140" />
        <el-table-column prop="quantity" label="数量" width="100">
          <template #default="{ row }">{{ row.quantity }} {{ row.unit }}</template>
        </el-table-column>
        <el-table-column prop="sugar_degree" label="糖度" width="80" />
        <el-table-column prop="operator" label="操作人" width="80" />
        <el-table-column prop="notes" label="备注" min-width="120" show-overflow-tooltip />
      </el-table>

      <div class="card-list visible-mobile">
        <div class="record-card" v-for="item in records" :key="item.id">
          <div class="card-main">
            <div class="card-title">{{ item.product_name }}</div>
            <div class="card-sub">{{ item.date }}</div>
          </div>
          <div class="card-info">
            <span>数量: {{ item.quantity }} {{ item.unit }}</span>
            <span v-if="item.sugar_degree">糖度: {{ item.sugar_degree }}</span>
          </div>
          <div class="card-info">
            <span v-if="item.operator">操作人: {{ item.operator }}</span>
            <span v-if="item.notes" class="card-sub">{{ item.notes }}</span>
          </div>
        </div>
      </div>
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
  .page-actions {
    flex-direction: column;
    width: 100%;
  }
}
</style>
