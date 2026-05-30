import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
  },
  {
    path: '/',
    component: () => import('../components/Layout.vue'),
    children: [
      { path: '', name: 'Dashboard', component: () => import('../views/Dashboard.vue') },
      { path: 'materials', name: 'Materials', component: () => import('../views/Materials.vue') },
      { path: 'production', name: 'ProductionList', component: () => import('../views/ProductionList.vue') },
      { path: 'production/new', name: 'ProductionNew', component: () => import('../views/ProductionNew.vue') },
      { path: 'shipments', name: 'Shipments', component: () => import('../views/ShipmentList.vue') },
      { path: 'shipments/new', name: 'ShipmentNew', component: () => import('../views/ShipmentNew.vue') },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  if (to.path !== '/login' && !token) {
    next('/login')
  } else if (to.path === '/login' && token) {
    next('/')
  } else {
    next()
  }
})

export default router
