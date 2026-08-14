<template>
  <div class="page">
    <div class="page-header">
      <h2>生产成本</h2>
      <el-date-picker v-model="monthVal" type="month" placeholder="选择月份" value-format="YYYY-MM" @change="loadData" style="width: 150px;" size="large" />
    </div>

    <el-row :gutter="16" class="kpi-row">
      <el-col :xs="24" :sm="8">
        <KpiCard label="生产次数" :value="data.total_count || 0" :icon="Calendar" color="#E65100" />
      </el-col>
      <el-col :xs="24" :sm="8">
        <KpiCard label="总产量" :value="data.total_quantity || 0" :icon="Box" color="#4CAF50" />
      </el-col>
      <el-col :xs="24" :sm="8">
        <KpiCard label="原料消耗总额" :value="'¥' + (data.total_cost || 0)" :icon="Wallet" color="#F44336" />
      </el-col>
    </el-row>

    <el-alert v-if="data.uncosted_count > 0" type="warning" :closable="false" style="margin-bottom: 16px;"
      :title="`${data.uncosted_count} 笔生产无成本快照（登记时原料无进价，未计入汇总）`" />

    <el-card class="section-card">
      <template #header><span class="card-title">产品维度汇总（{{ data.year }}-{{ String(data.month).padStart(2, '0') }}）</span></template>
      <el-table :data="data.by_product || []" stripe size="large">
        <el-table-column prop="product_name" label="产品" min-width="150" />
        <el-table-column prop="count" label="生产次数" width="100" align="center" />
        <el-table-column label="产量合计" width="120" align="right">
          <template #default="{ row }">{{ row.quantity }}</template>
        </el-table-column>
        <el-table-column label="原料成本合计" width="140" align="right">
          <template #default="{ row }">
            <span style="color: #E65100; font-weight: 600;">¥{{ row.cost.toFixed(2) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="单位成本" width="120" align="right">
          <template #default="{ row }">
            <span v-if="row.quantity > 0">¥{{ (row.cost / row.quantity).toFixed(3) }}</span>
            <span v-else>-</span>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!(data.by_product || []).length" description="本月暂无生产记录" />
    </el-card>

    <el-card class="section-card">
      <template #header><span class="card-title">生产明细</span></template>
      <el-table :data="data.details || []" stripe size="large" class="hidden-mobile">
        <el-table-column prop="date" label="日期" width="110" />
        <el-table-column prop="product_name" label="产品" min-width="130" />
        <el-table-column label="产量" width="100" align="right">
          <template #default="{ row }">{{ row.quantity }} {{ row.unit }}</template>
        </el-table-column>
        <el-table-column label="原料成本" width="120" align="right">
          <template #default="{ row }">
            <span v-if="row.material_cost != null">¥{{ row.material_cost.toFixed(2) }}</span>
            <span v-else style="color:#999;">无进价</span>
          </template>
        </el-table-column>
        <el-table-column label="单位成本" width="110" align="right">
          <template #default="{ row }">
            <span v-if="row.unit_cost != null">¥{{ row.unit_cost.toFixed(3) }}</span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="operator" label="操作人" width="90" />
      </el-table>
      <div class="card-list visible-mobile">
        <div class="record-card" v-for="d in (data.details || [])" :key="d.id">
          <div class="card-main">
            <div class="card-title">{{ d.product_name }}</div>
            <span v-if="d.material_cost != null" style="color:#E65100; font-weight:600;">¥{{ d.material_cost.toFixed(2) }}</span>
          </div>
          <div class="card-info">
            <span>{{ d.date }}</span>
            <span>产 {{ d.quantity }} {{ d.unit }}</span>
            <span v-if="d.unit_cost != null">¥{{ d.unit_cost.toFixed(3) }}/单位</span>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Calendar, Box, Wallet } from '@element-plus/icons-vue'
import KpiCard from '../components/KpiCard.vue'
import { getCostReport } from '../api'

const data = ref({})
const monthVal = ref('')

async function loadData() {
  let params = {}
  if (monthVal.value) {
    const [y, m] = monthVal.value.split('-')
    params = { year: y, month: m }
  }
  data.value = await getCostReport(params)
}

onMounted(loadData)
</script>

<style scoped>
.page { max-width: 1200px; }
.page-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; }
.page-header h2 { font-size: 22px; color: #333; margin: 0; }
.kpi-row { margin-bottom: 20px; }
.kpi-row .el-col { margin-bottom: 12px; }
.section-card { margin-bottom: 16px; }
.card-title { font-size: 16px; font-weight: 600; }
.visible-mobile { display: none; }
.hidden-mobile { display: block; }
.card-list { display: flex; flex-direction: column; gap: 8px; }
.record-card { background: white; border-radius: 8px; padding: 12px; box-shadow: 0 1px 4px rgba(0,0,0,0.08); }
.card-main { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.card-title { font-size: 15px; font-weight: 600; color: #212121; }
.card-info { display: flex; gap: 16px; font-size: 13px; color: #666; margin-bottom: 6px; flex-wrap: wrap; }
@media (max-width: 768px) {
  .visible-mobile { display: block; }
  .hidden-mobile { display: none; }
}
</style>
