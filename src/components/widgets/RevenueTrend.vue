<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Chart, registerables } from 'chart.js'
import axios from 'axios'
Chart.register(...registerables)

interface RevenueItem {
  dateTime: string
  amount: number
}

const revenueChart = ref<HTMLCanvasElement | null>(null)
const revenueData = ref<RevenueItem[]>([])
const localhost = 'http://localhost:5000/'

const fetchRevenueData = async () => {
  try {
    const res = await axios.get(localhost + '/api/revenues')
    revenueData.value = res.data
    console.log('revenueData.value', revenueData.value)
    renderRevenueChart()
  } catch (err) {
    console.error('Failed to fetch revenue data:', err)
  }
}
function getMonthLabel(ym: string) {
  if (!ym) return ''
  return new Date(ym + '-01').toLocaleString('default', { month: 'short', year: '2-digit' })
}

const renderRevenueChart = () => {
  if (!revenueChart.value) return

  // Group by month for visualization
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

onMounted(fetchRevenueData)
</script>
<template>
  <div class="dashboard-chart mb-3">
    <h3>Revenue Over Time</h3>
    <canvas ref="revenueChart" height="90"></canvas>
  </div>
</template>

<style scoped>
.widget {
  padding: 1rem;
}
</style>
