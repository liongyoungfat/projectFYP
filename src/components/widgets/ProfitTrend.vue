<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { Bar } from 'vue-chartjs'
import { Chart, registerables } from 'chart.js'
import axios from 'axios'

Chart.register(...registerables)

const revenueChart = ref<HTMLCanvasElement | null>(null)
const profitChart = ref<HTMLCanvasElement | null>(null)
const localhost = 'http://localhost:5000/'

const revenueData = ref<RevenueItem[]>([])
const expensesData = ref<ExpenseItem[]>([])

interface RevenueItem {
  amount: number
  dateTime: string
}

interface ExpenseItem {
  amount: number
  dateTime: string
}

const fetchExpenseData = async () => {
  try {
    const res = await axios.get(localhost + 'api/expenses')
    expensesData.value = res.data
    renderProfitChart()
  } catch (err) {
    console.error('Failed to fetch expense data:', err)
  }
}

const renderProfitChart = () => {
  if (!profitChart.value || revenueData.value.length === 0 || expensesData.value.length === 0)
    return

  const revenueByMonth: Record<string, number> = {}
  revenueData.value.forEach((item) => {
    if (!item.dateTime) return
    const dateObj = new Date(item.dateTime)
    const m = `${dateObj.getFullYear()}-${String(dateObj.getMonth() + 1).padStart(2, '0')}`
    revenueByMonth[m] = (revenueByMonth[m] || 0) + Number(item.amount)
  })
  console.log('rBM', revenueByMonth)
  const expenseByMonth: Record<string, number> = {}
  expensesData.value.forEach((item) => {
    if (!item.dateTime) return
    const dateObj = new Date(item.dateTime)
    const m = `${dateObj.getFullYear()}-${String(dateObj.getMonth() + 1).padStart(2, '0')}`
    expenseByMonth[m] = (expenseByMonth[m] || 0) + Number(item.amount)
  })
  console.log('eBM', expenseByMonth)

  const months = Array.from(
    new Set([...Object.keys(revenueByMonth), ...Object.keys(expenseByMonth)]),
  ).sort()
  const profitValues = months.map((m) => (revenueByMonth[m] || 0) - (expenseByMonth[m] || 0))
  const monthsLabels = months.map((m) => getMonthLabel(m))

  new Chart(profitChart.value, {
    type: 'line',
    data: {
      labels: monthsLabels,
      datasets: [
        {
          label: 'Net Profit (RM)',
          data: profitValues,
          borderColor: '#ff6384',
          fill: false,
        },
      ],
    },
    options: {
      responsive: true,
      plugins: {
        title: { display: true, text: 'Net Profit Trend' },
      },
      scales: {
        y: {
          beginAtZero: true,
          title: { display: true, text: 'Amount (RM)' },
        },
        x: {
          title: { display: true, text: 'Month' },
        },
      },
    },
  })
}

function getMonthLabel(ym: string) {
  if (!ym) return ''
  return new Date(ym + '-01').toLocaleString('default', { month: 'short', year: '2-digit' })
}

const fetchRevenueData = async () => {
  try {
    const res = await axios.get(localhost + '/api/revenues')
    revenueData.value = res.data
    console.log('revenueData.value', revenueData.value)
    renderRevenueChart()
    renderProfitChart()
  } catch (err) {
    console.error('Failed to fetch revenue data:', err)
  }
}

const renderRevenueChart = () => {
  if (!revenueChart.value) return
  const monthlyTotals: Record<string, number> = {}
  revenueData.value.forEach((item) => {
    if (!item.dateTime) return
    const dateObj = new Date(item.dateTime)
    const month = `${dateObj.getFullYear()}-${String(dateObj.getMonth() + 1).padStart(2, '0')}`
    if (!monthlyTotals[month]) monthlyTotals[month] = 0
    monthlyTotals[month] += Number(item.amount)
  })

  const ymList = Object.keys(monthlyTotals).sort()
  const labels = ymList.map((m) => getMonthLabel(m))
  const values = ymList.map((month) => monthlyTotals[month])
  console.log('labelsss', labels)

  new Chart(revenueChart.value, {
    type: 'bar',
    data: {
      labels,
      datasets: [
        {
          label: 'Revenue (RM)',
          data: values,
          backgroundColor: '#36A2EB',
        },
      ],
    },
    options: {
      responsive: true,
      plugins: {
        title: {
          display: true,
          text: `Monthly Revenue Trend`,
        },
      },
      scales: {
        y: {
          beginAtZero: true,
          title: {
            display: true,
            text: 'Amount (RM)',
          },
        },
        x: {
          title: {
            display: true,
            text: 'Month',
          },
        },
      },
    },
  })
}

onMounted(() => {
  fetchRevenueData()
  fetchExpenseData()
})

</script>
<template>
  <div class="dashboard-chart mb-3">
    <h3>Net Profit Trend</h3>
    <canvas ref="profitChart" height="90"></canvas>
  </div>
</template>

<style scoped>
.widget {
  padding: 1rem;
}
</style>
