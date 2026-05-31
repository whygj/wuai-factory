<template>
  <div class="page">
    <h2 class="page-title">产品库存</h2>

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
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getProducts } from '../api'

const products = ref([])
const search = ref('')

async function load() {
  try {
    const res = await getProducts({ search: search.value })
    products.value = res.items || []
  } catch (e) {}
}

onMounted(load)
</script>

<style scoped>
.page-title { font-size: 24px; font-weight: 700; color: var(--primary); margin-bottom: 16px; }
.toolbar { margin-bottom: 16px; }
.low-stock { color: #F44336; font-weight: 700; }
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
