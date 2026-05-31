import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
  },
  {
    path: '/select-role',
    name: 'RoleSelect',
    component: () => import('../views/RoleSelect.vue'),
  },
  {
    path: '/',
    component: () => import('../components/Layout.vue'),
    children: [
      { path: '', name: 'Dashboard', component: () => import('../views/Dashboard.vue') },
      { path: 'customers', name: 'Customers', component: () => import('../views/Customers.vue') },
      { path: 'suppliers', name: 'Suppliers', component: () => import('../views/Suppliers.vue') },
      { path: 'materials', name: 'Materials', component: () => import('../views/Materials.vue') },
      { path: 'production', name: 'ProductionList', component: () => import('../views/ProductionList.vue') },
      { path: 'production/new', name: 'ProductionNew', component: () => import('../views/ProductionNew.vue') },
      { path: 'shipments', name: 'Shipments', component: () => import('../views/ShipmentList.vue') },
      { path: 'shipments/new', name: 'ShipmentNew', component: () => import('../views/ShipmentNew.vue') },
      { path: 'sales-orders', name: 'SalesOrders', component: () => import('../views/SalesOrders.vue') },
      { path: 'purchases', name: 'Purchases', component: () => import('../views/Purchases.vue') },
      { path: 'receivables', name: 'Receivables', component: () => import('../views/Receivables.vue') },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  if (to.path !== '/login' && to.path !== '/select-role' && !token) {
    next('/login')
  } else if ((to.path === '/login') && token) {
    next('/')
  } else {
    next()
  }
})

export default router
