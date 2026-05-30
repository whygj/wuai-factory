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
export const login = (data) => api.post('/auth/login', data)
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

// Stats
export const getMaterialDistribution = () => api.get('/stats/material-distribution')
export const getProductRanking = () => api.get('/stats/product-ranking')
export const getProductionTrend = (days = 7) => api.get('/stats/production-trend', { params: { days } })

export default api
