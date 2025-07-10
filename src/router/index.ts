import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '@/views/FinancialDashboard.vue'
import Expenses from '@/views/ExpensesTable.vue'
import Revenue from '@/views/RevenueTable.vue'
import TaxPage from '@/views/TaxPage.vue'
import CustomDashboard from '@/views/CustomDashboard.vue'

const routes = [
  { path: '/', name: 'FinancialDashboard', component: Dashboard },
  { path: '/expenses', name: 'ExpensesTable', component: Expenses },
  { path: '/revenue', name: 'RevenueTable', component: Revenue },
  { path: '/tax', name: 'TaxPage', component: TaxPage },
  { path: '/customizer', name: 'CustomDashboard', component: CustomDashboard },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

export default router
