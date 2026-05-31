import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '../router'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
  withCredentials: true,
})

api.interceptors.response.use(
  response => response.data,
  error => {
    const msg = error.response?.data?.detail || '请求失败'
    if (error.response?.status === 401) {
      router.push('/login')
    }
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
export const getTransactions = (params) => api.get('/materials/transactions', { params })

// Products
export const getProducts = (params) => api.get('/products', { params })
export const createProduct = (data) => api.post('/products', data)
export const updateProduct = (id, data) => api.put(`/products/${id}`, data)

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
export const shipSalesOrder = (id) => api.put(`/sales-orders/${id}/ship`)
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

// Permission helper
export function canEdit(module) {
  const role = localStorage.getItem('currentRole')
  if (role === 'boss') return true
  if (role === 'clerk') return ['customer', 'supplier', 'purchase', 'inbound', 'production', 'sales', 'shipment', 'lab'].includes(module)
  if (role === 'leader') return ['production', 'lab'].includes(module)
  return false
}

export default api
