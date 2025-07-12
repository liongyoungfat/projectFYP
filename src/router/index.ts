import { createRouter, createWebHistory } from 'vue-router'

import PublicLayout from '@/layouts/PublicLayout.vue'
import AuthLayout from '@/layouts/AuthLayout.vue'

import Login from '@/views/UserLogin.vue'
import Register from '@/views/UserRegister.vue'
import Dashboard from '@/views/FinancialDashboard.vue'
import Expenses from '@/views/ExpensesTable.vue'
import Revenue from '@/views/RevenueTable.vue'
import TaxPage from '@/views/TaxPage.vue'
import ManageStaff from '@/views/ManageStaff.vue'

const routes = [
  {
    path: '/',
    component: PublicLayout,
    children: [
      { path: '', name: 'Login', component: Login },
      { path: 'login', name: 'LoginPage', component: Login },
      { path: 'register', name: 'Register', component: Register },
    ],
  },
  {
    path: '/',
    component: AuthLayout,
    children: [
      { path: 'dashboard', name: 'FinancialDashboard', component: Dashboard },
      { path: 'expenses', name: 'ExpensesTable', component: Expenses },
      { path: 'revenue', name: 'RevenueTable', component: Revenue },
      { path: 'tax', name: 'TaxPage', component: TaxPage },
      { path: 'staff', name: 'ManageStaff', component: ManageStaff },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')

  if (to.path !== '/' && to.path !== '/login' && !token) {
    next('/') // 🔒 Redirect to login if not authenticated
  } else {
    next() // ✅ Allow navigation
  }
})

export default router
