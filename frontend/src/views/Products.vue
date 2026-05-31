<template>
  <div class="page">
    <h2 class="page-title">产品库存</h2>

    <div class="toolbar">
      <el-input v-model="search" placeholder="搜索产品" clearable @input="load" style="max-width:300px" />
    </div>

    <el-card>
      <el-table :data="products" stripe>
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
</style>
