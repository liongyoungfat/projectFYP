import { createRouter, createWebHistory } from 'vue-router'

import PublicLayout from '@/layouts/PublicLayout.vue'
import AuthLayout from '@/layouts/AuthLayout.vue'

import HomePage from '../views/HomePage.vue'
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
      { path: '', name: 'Home', component: HomePage },
      { path: 'login', name: 'LoginPage', component: Login },
      { path: 'register', name: 'Register', component: Register },
    ],
  },
  {
    path: '/',
    component: AuthLayout,
    children: [
      {
        path: 'dashboard',
        name: 'FinancialDashboard',
        component: Dashboard,
        meta: { title: 'Financial Dashboard', requiresAuth: true },
      },
      {
        path: 'expenses',
        name: 'ExpensesTable',
        component: Expenses,
        meta: { title: 'Expenses Table', requiresAuth: true },
      },
      {
        path: 'revenue',
        name: 'RevenueTable',
        component: Revenue,
        meta: { title: 'Revenue Table', requiresAuth: true },
      },
      {
        path: 'tax',
        name: 'TaxPage',
        component: TaxPage,
        meta: { title: 'Tax Management', requiresAuth: true },
      },
      {
        path: 'staff',
        name: 'ManageStaff',
        component: ManageStaff,
        meta: { title: 'Staff Management', requiresAuth: true },
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

router.beforeEach((to, from, next) => {
  const authToken = localStorage.getItem('authToken')
  // If route requires auth and no token, redirect to login
  if (to.matched.some((record) => record.meta.requiresAuth)) {
    if (!authToken) {
      return next('/login')
    }
  }
  // If already logged in and trying to access login/register, redirect to dashboard
  if ((to.path === '/login' || to.path === '/register') && authToken) {
    return next('/dashboard')
  }
  next()
})

export default router
