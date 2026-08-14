<template>
  <div class="page">
    <div class="page-header">
      <h2>批次追溯</h2>
    </div>

    <el-tabs v-model="activeTab" size="large">
      <!-- 批次台账 -->
      <el-tab-pane label="批次台账" name="batches">
        <div class="filter-bar">
          <el-select v-model="materialFilter" placeholder="按原料筛选" clearable filterable style="width: 200px;" size="large" @change="loadBatches">
            <el-option v-for="m in materialList" :key="m.id" :label="m.name" :value="m.id" />
          </el-select>
          <el-select v-model="statusFilter" placeholder="状态" clearable style="width: 130px;" size="large" @change="loadBatches">
            <el-option label="在库" value="在库" />
            <el-option label="耗尽" value="耗尽" />
            <el-option label="报废" value="报废" />
          </el-select>
        </div>
        <el-table :data="batches" stripe size="large" class="hidden-mobile">
          <el-table-column prop="material_name" label="原料" min-width="110" />
          <el-table-column prop="batch_no" label="批次号" min-width="130">
            <template #default="{ row }">
              <span class="batch-link" @click="doForwardTrace(row.id)">{{ row.batch_no }}</span>
            </template>
          </el-table-column>
          <el-table-column label="入库/剩余" width="120">
            <template #default="{ row }">{{ row.quantity_in }} / {{ row.quantity_remaining }} {{ row.unit }}</template>
          </el-table-column>
          <el-table-column label="进价" width="80" align="right">
            <template #default="{ row }">{{ row.unit_price != null ? '¥' + row.unit_price : '-' }}</template>
          </el-table-column>
          <el-table-column prop="supplier_name" label="供应商" min-width="100" />
          <el-table-column label="保质期到" width="110">
            <template #default="{ row }">
              <span v-if="row.expiry_date" :class="{ 'expired-text': isExpired(row.expiry_date) }">{{ row.expiry_date }}</span>
              <span v-else style="color:#999;">不管理</span>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="80" align="center">
            <template #default="{ row }">
              <el-tag size="small" :type="row.status === '在库' ? 'success' : row.status === '耗尽' ? 'info' : 'danger'">{{ row.status }}</el-tag>
            </template>
          </el-table-column>
        </el-table>
        <div class="card-list visible-mobile">
          <div class="record-card" v-for="b in batches" :key="b.id">
            <div class="card-main">
              <div class="card-title" @click="doForwardTrace(b.id)" style="color:#E65100;">{{ b.batch_no }}</div>
              <el-tag size="small" :type="b.status === '在库' ? 'success' : b.status === '耗尽' ? 'info' : 'danger'">{{ b.status }}</el-tag>
            </div>
            <div class="card-info">
              <span>{{ b.material_name }}</span>
              <span>余 {{ b.quantity_remaining }}/{{ b.quantity_in }} {{ b.unit }}</span>
            </div>
            <div class="card-info" v-if="b.expiry_date">
              <span :class="{ 'expired-text': isExpired(b.expiry_date) }">保质期至 {{ b.expiry_date }}</span>
            </div>
          </div>
        </div>
        <el-empty v-if="batches.length === 0" description="暂无批次——采购入库时填写批次信息即可建立追溯" />
      </el-tab-pane>

      <!-- 临期预警 -->
      <el-tab-pane :label="`临期预警${expiring.length ? '(' + expiring.length + ')' : ''}`" name="expiring">
        <el-table :data="expiring" stripe size="large" class="hidden-mobile">
          <el-table-column prop="material_name" label="原料" min-width="120" />
          <el-table-column prop="batch_no" label="批次号" min-width="130" />
          <el-table-column label="剩余量" width="110">
            <template #default="{ row }">{{ row.quantity_remaining }} {{ row.unit }}</template>
          </el-table-column>
          <el-table-column prop="expiry_date" label="保质期到" width="120" />
          <el-table-column label="剩余天数" width="110" align="center">
            <template #default="{ row }">
              <el-tag v-if="row.expired" type="danger" size="small">已过期{{ -row.remain_days }}天</el-tag>
              <el-tag v-else-if="row.remain_days <= 7" type="danger" size="small">剩{{ row.remain_days }}天</el-tag>
              <el-tag v-else type="warning" size="small">剩{{ row.remain_days }}天</el-tag>
            </template>
          </el-table-column>
        </el-table>
        <div class="card-list visible-mobile">
          <div class="record-card" v-for="e in expiring" :key="e.id">
            <div class="card-main">
              <div class="card-title">{{ e.material_name }}</div>
              <el-tag v-if="e.expired" type="danger" size="small">已过期{{ -e.remain_days }}天</el-tag>
              <el-tag v-else :type="e.remain_days <= 7 ? 'danger' : 'warning'" size="small">剩{{ e.remain_days }}天</el-tag>
            </div>
            <div class="card-info">
              <span>{{ e.batch_no }}</span>
              <span>余 {{ e.quantity_remaining }} {{ e.unit }}</span>
            </div>
          </div>
        </div>
        <el-empty v-if="expiring.length === 0" description="30天内无临期批次" />
      </el-tab-pane>

      <!-- 反向追溯 -->
      <el-tab-pane label="反向追溯(原料→客户)" name="forward">
        <div class="filter-bar">
          <el-select v-model="forwardBatchId" placeholder="选择原料批次" filterable style="width: 260px;" size="large" @change="doForwardTrace">
            <el-option v-for="b in batches" :key="b.id" :label="`${b.material_name} / ${b.batch_no}`" :value="b.id" />
          </el-select>
        </div>
        <template v-if="forwardResult">
          <el-descriptions :column="3" border size="large" class="trace-desc">
            <el-descriptions-item label="原料">{{ forwardResult.batch.material_name }}</el-descriptions-item>
            <el-descriptions-item label="批次号">{{ forwardResult.batch.batch_no }}</el-descriptions-item>
            <el-descriptions-item label="供应商">{{ forwardResult.batch.supplier_name || '-' }}</el-descriptions-item>
            <el-descriptions-item label="入库量">{{ forwardResult.batch.quantity_in }} {{ forwardResult.batch.unit }}</el-descriptions-item>
            <el-descriptions-item label="剩余">{{ forwardResult.batch.quantity_remaining }} {{ forwardResult.batch.unit }}</el-descriptions-item>
            <el-descriptions-item label="保质期到">{{ forwardResult.batch.expiry_date || '不管理' }}</el-descriptions-item>
          </el-descriptions>
          <h4 class="section-title">用于生产（{{ forwardResult.productions.length }} 笔）→ 发往客户</h4>
          <el-table :data="forwardResult.productions" stripe size="large">
            <el-table-column prop="date" label="生产日期" width="110" />
            <el-table-column prop="product_name" label="产品" min-width="120" />
            <el-table-column label="产量" width="90">
              <template #default="{ row }">{{ row.quantity }} {{ row.unit }}</template>
            </el-table-column>
            <el-table-column label="本批用量" width="90">
              <template #default="{ row }">{{ row.used_in_this_production }}</template>
            </el-table-column>
            <el-table-column prop="operator" label="操作人" width="90" />
            <el-table-column label="发往客户" min-width="200">
              <template #default="{ row }">
                <template v-if="row.shipments.length">
                  <div v-for="(d, i) in row.shipments" :key="i" class="dest-line">
                    {{ d.customer }}（{{ d.date }} 发 {{ d.quantity }}{{ d.order_no ? '，' + d.order_no : '' }}）
                  </div>
                </template>
                <span v-else style="color:#999;">未发货</span>
              </template>
            </el-table-column>
          </el-table>
        </template>
        <el-empty v-else description="选择批次查看：该批原料用于哪些生产、发给了哪些客户" />
      </el-tab-pane>

      <!-- 正向追溯 -->
      <el-tab-pane label="正向追溯(生产→原料)" name="backward">
        <div class="filter-bar">
          <el-select v-model="backwardProdId" placeholder="选择生产记录" filterable style="width: 300px;" size="large" @change="doBackwardTrace">
            <el-option v-for="p in productionList" :key="p.id" :label="`${p.date} ${p.product_name} ×${p.quantity}`" :value="p.id" />
          </el-select>
        </div>
        <template v-if="backwardResult">
          <el-descriptions :column="4" border size="large" class="trace-desc">
            <el-descriptions-item label="生产日期">{{ backwardResult.production.date }}</el-descriptions-item>
            <el-descriptions-item label="产品">{{ backwardResult.production.product_name }}</el-descriptions-item>
            <el-descriptions-item label="产量">{{ backwardResult.production.quantity }} {{ backwardResult.production.unit }}</el-descriptions-item>
            <el-descriptions-item label="操作人">{{ backwardResult.production.operator }}</el-descriptions-item>
          </el-descriptions>
          <h4 class="section-title">消耗的原料批次（{{ backwardResult.batches.length }} 个）</h4>
          <el-table :data="backwardResult.batches" stripe size="large">
            <el-table-column prop="material_name" label="原料" min-width="110" />
            <el-table-column prop="batch_no" label="批次号" min-width="130" />
            <el-table-column label="用量" width="90">
              <template #default="{ row }">{{ row.used_quantity }} {{ row.unit }}</template>
            </el-table-column>
            <el-table-column prop="supplier_name" label="供应商" min-width="100" />
            <el-table-column prop="production_date" label="原料生产日期" width="110">
              <template #default="{ row }">{{ row.production_date || '-' }}</template>
            </el-table-column>
            <el-table-column prop="expiry_date" label="保质期到" width="110">
              <template #default="{ row }">{{ row.expiry_date || '-' }}</template>
            </el-table-column>
          </el-table>
          <el-alert v-if="backwardResult.unbatched.length" type="warning" :closable="false" class="unbatched-alert"
            :title="`未分批原料（无法追溯批次）：${backwardResult.unbatched.map(u => u.material_name + ' ×' + u.used_quantity).join('、')}`" />
        </template>
        <el-empty v-else description="选择生产记录查看：该批产品用了哪些原料批次" />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getBatches, getExpiringBatches, traceBatchForward, traceProductionBackward, getMaterials, getProduction } from '../api'

const activeTab = ref('batches')
const materialFilter = ref('')
const statusFilter = ref('')
const batches = ref([])
const expiring = ref([])
const materialList = ref([])
const productionList = ref([])
const forwardBatchId = ref('')
const forwardResult = ref(null)
const backwardProdId = ref('')
const backwardResult = ref(null)

function isExpired(d) {
  return new Date(d) < new Date(new Date().toDateString())
}

async function loadBatches() {
  const params = {}
  if (materialFilter.value) params.material_id = materialFilter.value
  if (statusFilter.value) params.status = statusFilter.value
  const res = await getBatches(params)
  batches.value = res.items
}

async function loadExpiring() {
  expiring.value = await getExpiringBatches(30)
}

async function doForwardTrace(batchId) {
  if (!batchId) return
  activeTab.value = 'forward'
  forwardBatchId.value = batchId
  forwardResult.value = await traceBatchForward(batchId)
}

async function doBackwardTrace(prodId) {
  if (!prodId) return
  backwardResult.value = await traceProductionBackward(prodId)
}

onMounted(async () => {
  await Promise.all([loadBatches(), loadExpiring()])
  const [mRes, pRes] = await Promise.all([
    getMaterials({ page_size: 200 }),
    getProduction({ page_size: 100 }),
  ])
  materialList.value = mRes.items
  productionList.value = pRes.items
})
</script>

<style scoped>
.page { max-width: 1200px; }
.page-header { margin-bottom: 16px; }
.page-header h2 { font-size: 22px; color: #333; margin: 0; }
.filter-bar { display: flex; gap: 12px; margin-bottom: 16px; flex-wrap: wrap; }
.batch-link { color: #E65100; cursor: pointer; text-decoration: underline; }
.expired-text { color: #C62828; font-weight: 700; }
.section-title { font-size: 15px; color: #333; margin: 16px 0 8px; }
.trace-desc { margin-bottom: 4px; }
.dest-line { font-size: 14px; line-height: 1.7; }
.unbatched-alert { margin-top: 12px; }
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
  .filter-bar { flex-direction: column; }
  .filter-bar .el-select { width: 100% !important; }
}
</style>
