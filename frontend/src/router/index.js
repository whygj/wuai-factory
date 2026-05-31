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
      { path: 'products', name: 'Products', component: () => import('../views/Products.vue') },
      { path: 'production', name: 'ProductionList', component: () => import('../views/ProductionList.vue') },
      { path: 'production/new', name: 'ProductionNew', component: () => import('../views/ProductionNew.vue') },
      { path: 'shipments', name: 'Shipments', component: () => import('../views/ShipmentList.vue') },
      { path: 'shipments/new', name: 'ShipmentNew', component: () => import('../views/ShipmentNew.vue') },
      { path: 'sales-orders', name: 'SalesOrders', component: () => import('../views/SalesOrders.vue') },
      { path: 'purchases', name: 'Purchases', component: () => import('../views/Purchases.vue') },
      { path: 'receivables', name: 'Receivables', component: () => import('../views/Receivables.vue') },
      { path: 'lab', name: 'LabRecords', component: () => import('../views/LabRecords.vue') },
      { path: 'reports', name: 'Reports', component: () => import('../views/Reports.vue') },
      { path: 'users', name: 'Users', component: () => import('../views/UserManage.vue') },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  // 强制退出：访问 /login?force=1 清除所有登录状态
  if (to.path === '/login' && to.query.force === '1') {
    localStorage.removeItem('displayName')
    localStorage.removeItem('roles')
    localStorage.removeItem('currentRole')
    document.cookie = 'access_token=; path=/; max-age=0'
    next('/login')
    return
  }
  const loggedIn = localStorage.getItem('displayName')
  if (to.path !== '/login' && to.path !== '/select-role' && !loggedIn) {
    next('/login')
  } else if ((to.path === '/login') && loggedIn) {
    next('/')
  } else {
    next()
  }
})

export default router
