import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '../router'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
})

api.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  response => response.data,
  error => {
    const msg = error.response?.data?.detail || '请求失败'
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      router.push('/login')
    }
    ElMessage.error(msg)
    return Promise.reject(error)
  }
)

// Auth
export const loginPhone = (data) => api.post('/auth/login', data)
export const selectRoleApi = (data) => api.post('/auth/select-role', data)
export const getRoles = () => api.get('/auth/roles')
export const getMe = () => api.get('/auth/me')

// Dashboard
export const getDashboard = () => api.get('/dashboard/overview')

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

// Stats
export const getMaterialDistribution = () => api.get('/stats/material-distribution')
export const getProductRanking = () => api.get('/stats/product-ranking')
export const getProductionTrend = (days = 7) => api.get('/stats/production-trend', { params: { days } })

// Permission helper
export function canEdit(module) {
  const role = localStorage.getItem('currentRole')
  if (role === 'boss') return true
  if (role === 'clerk') return ['customer', 'supplier', 'purchase', 'inbound', 'production', 'sales', 'shipment', 'lab'].includes(module)
  if (role === 'leader') return ['production', 'lab'].includes(module)
  return false
}

export default api
