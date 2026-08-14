import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '../router'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
  withCredentials: true,
})

api.interceptors.response.use(
  response => {
    // blob 导出不走 response.data 解包（返回原始 Blob 供下载）
    if (response.config?.responseType === 'blob') return response
    return response.data
  },
  error => {
    let msg = '请求失败'
    if (error.response?.status === 401) {
      // 先清登录态再跳转，否则 router.beforeEach 看到 displayName 还在会把 /login 弹回 /，形成死循环
      localStorage.removeItem('displayName')
      localStorage.removeItem('currentRole')
      localStorage.removeItem('userRoles')
      if (router.currentRoute.value.path !== '/login') {
        router.push('/login')
      }
    }
    // blob 请求的错误体也是 blob，读出来给提示
    if (error.response?.data instanceof Blob) {
      error.response.data.text().then(text => {
        try { msg = JSON.parse(text).detail || msg } catch { /* 保持默认 */ }
        ElMessage.error(msg)
      })
      return Promise.reject(error)
    }
    msg = error.response?.data?.detail || msg
    ElMessage.error(msg)
    return Promise.reject(error)
  }
)

// Auth
export const sendVerifyCode = (data) => api.post('/auth/send-code', data)
export const loginWithCode = (data) => api.post('/auth/login', data)
export const register = (data) => api.post('/auth/register', data)
export const selectRoleApi = (data) => api.post('/auth/select-role', data)
export const getRoles = () => api.get('/auth/roles')
export const getMe = () => api.get('/auth/me')
export const logoutApi = () => api.post('/auth/logout')

// User Management
export const getPendingUsersApi = () => api.get('/users/pending')
export const getAllUsersApi = () => api.get('/users')
export const approveUserApi = (id) => api.post(`/users/${id}/approve`)
export const rejectUserApi = (id) => api.post(`/users/${id}/reject`)
export const updateUserApi = (id, data) => api.put(`/users/${id}`, data)

// Dashboard
export const getDashboard = () => api.get('/dashboard/overview')
export const getBossDashboard = () => api.get('/dashboard/boss')
export const getBossDashboardExtended = () => api.get('/dashboard/boss-extended')
export const getClerkDashboard = () => api.get('/dashboard/clerk')
export const getLeaderDashboard = () => api.get('/dashboard/leader')

// Materials
export const getMaterials = (params) => api.get('/materials', { params })
export const createMaterial = (data) => api.post('/materials', data)
export const updateMaterial = (id, data) => api.put(`/materials/${id}`, data)
export const inboundMaterial = (id, data) => api.post(`/materials/${id}/inbound`, data)
export const adjustMaterial = (id, data) => api.post(`/materials/${id}/adjust`, data)
export const getTransactions = (params) => api.get('/materials/transactions', { params })

// Products
export const getProducts = (params) => api.get('/products', { params })
export const createProduct = (data) => api.post('/products', data)
export const updateProduct = (id, data) => api.put(`/products/${id}`, data)
export const adjustProduct = (id, data) => api.post(`/products/${id}/adjust`, data)

// Production
export const getProduction = (params) => api.get('/production', { params })
export const createProduction = (data) => api.post('/production', data)
export const getProductionDetail = (id) => api.get(`/production/${id}`)

// Shipments
export const getShipments = (params) => api.get('/shipments', { params })
export const createShipment = (data) => api.post('/shipments', data)
export const updateShipmentStatus = (id, data) => api.put(`/shipments/${id}/status`, data)

// Customers
export const getCustomers = (params) => api.get('/customers', { params })
export const createCustomer = (data) => api.post('/customers', data)
export const updateCustomer = (id, data) => api.put(`/customers/${id}`, data)
export const deleteCustomer = (id) => api.delete(`/customers/${id}`)
export const getCustomerSummary = (id) => api.get(`/customers/${id}/summary`)

// Suppliers
export const getSuppliers = (params) => api.get('/suppliers', { params })
export const createSupplier = (data) => api.post('/suppliers', data)
export const updateSupplier = (id, data) => api.put(`/suppliers/${id}`, data)
export const deleteSupplier = (id) => api.delete(`/suppliers/${id}`)

// Sales Orders
export const getSalesOrders = (params) => api.get('/sales-orders', { params })
export const createSalesOrder = (data) => api.post('/sales-orders', data)
export const getSalesOrder = (id) => api.get(`/sales-orders/${id}`)
export const updateSalesOrderStatus = (id, data) => api.put(`/sales-orders/${id}/status`, data)
export const getOrderShipmentProgress = (id) => api.get(`/sales-orders/${id}/shipment-progress`)
export const recordPayment = (id, data) => api.put(`/sales-orders/${id}/payment`, data)
export const getSalesStats = () => api.get('/sales-orders/stats')

// Purchases
export const getPurchases = (params) => api.get('/purchases', { params })
export const createPurchase = (data) => api.post('/purchases', data)
export const getPurchase = (id) => api.get(`/purchases/${id}`)
export const updatePurchaseStatus = (id, data) => api.put(`/purchases/${id}/status`, data)
export const confirmInbound = (id) => api.put(`/purchases/${id}/inbound`)

// Receivables
export const getReceivables = (params) => api.get('/receivables', { params })
export const getOverdueReceivables = (params) => api.get('/receivables/overdue', { params })
export const getReceivablesSummary = () => api.get('/receivables/summary')

// Stats
export const getMaterialDistribution = () => api.get('/stats/material-distribution')
export const getProductRanking = () => api.get('/stats/product-ranking')
export const getProductionTrend = (days = 7) => api.get('/stats/production-trend', { params: { days } })

// Lab Records
export const getLabRecords = (params) => api.get('/lab', { params })
export const createLabRecord = (data) => api.post('/lab', data)
export const updateLabRecord = (id, data) => api.put(`/lab/${id}`, data)

// Reports
export const getSalesReport = (params) => api.get('/reports/sales', { params })
export const getProductionReport = (params) => api.get('/reports/production', { params })
export const getInventoryReport = () => api.get('/reports/inventory')

// Quick Search
export const quickSearch = (params) => api.get('/quick-search', { params })

// Batches (v3.1)
export const getBatches = (params) => api.get('/batches', { params })
export const getExpiringBatches = (days = 30) => api.get('/batches/expiring', { params: { days } })
export const previewBatchUsage = (materialId, quantity) => api.get('/batches/preview-usage', { params: { material_id: materialId, quantity } })
export const traceBatchForward = (batchId) => api.get(`/batches/${batchId}/trace-forward`)
export const traceProductionBackward = (productionId) => api.get(`/production/${productionId}/trace-backward`)

// Purchase Payments & Payables (v3.2)
export const addPurchasePayment = (orderId, data) => api.post(`/purchases/${orderId}/payments`, data)
export const getPurchasePayments = (orderId) => api.get(`/purchases/${orderId}/payments`)
export const voidPurchasePayment = (paymentId) => api.put(`/purchase-payments/${paymentId}/void`)
export const getPayablesSummary = () => api.get('/payables/summary')
export const getPayables = (params) => api.get('/payables', { params })

// Sales Returns (v3.2)
export const createReturn = (data) => api.post('/returns', data)
export const voidReturn = (id) => api.put(`/returns/${id}/void`)
export const getOrderReturns = (orderId) => api.get(`/sales-orders/${orderId}/returns`)

// Operation Logs
export const getOperationLogs = (params) => api.get('/operation-logs', { params })
export const getOperationLogFilters = () => api.get('/operation-logs/filters')

// Export (Excel) — blob 下载，独立实例避免响应拦截器把二进制当 JSON
export function exportExcel(module, params = {}) {
  return api.get(`/export/${module}`, { params, responseType: 'blob', timeout: 30000 })
}

export async function downloadExport(module, params = {}, filenamePrefix = module) {
  const res = await exportExcel(module, params)
  const url = window.URL.createObjectURL(new Blob([res]))
  const link = document.createElement('a')
  link.href = url
  const today = new Date().toISOString().slice(0, 10)
  link.download = `${filenamePrefix}_${today}.xlsx`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  window.URL.revokeObjectURL(url)
}

// Permission helper
export function canEdit(module) {
  const role = localStorage.getItem('currentRole')
  if (role === 'boss') return true
  if (role === 'clerk') return ['customer', 'supplier', 'purchase', 'inbound', 'production', 'product', 'sales', 'shipment', 'lab'].includes(module)
  if (role === 'leader') return ['production', 'lab'].includes(module)
  return false
}

export default api
