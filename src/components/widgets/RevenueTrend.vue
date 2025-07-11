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

const startDate = ref<string>('')
const endDate = ref<string>('')
const filteredRevenueData = ref<RevenueItem[]>([])

const fetchRevenueData = async () => {
  try {
    const res = await axios.get(localhost + 'api/revenues')
    revenueData.value = res.data
    filteredRevenueData.value = [...revenueData.value]
    // console.log('Fetched revenue data:', revenueData.value)
    renderRevenueChart()
  } catch (err) {
    console.error('Failed to fetch revenue data:', err)
  }
}
function getMonthLabel(ym: string) {
  if (!ym) return ''
  return new Date(ym + '-01').toLocaleString('default', { month: 'short', year: '2-digit' })
}

const applyDateFilter = () => {
  if (!startDate.value || !endDate.value) {
    filteredRevenueData.value = [...revenueData.value]
  } else {
    const start = new Date(startDate.value)
    const end = new Date(endDate.value)

    filteredRevenueData.value = revenueData.value.filter((item) => {
      const itemDate = new Date(item.dateTime)
      return itemDate >= start && itemDate <= end
    })
  }
  renderRevenueChart()
}

const resetDateFilter = () => {
  startDate.value = ''
  endDate.value = ''
  filteredRevenueData.value = [...revenueData.value]
  renderRevenueChart()
}

const renderRevenueChart = () => {
  if (!revenueChart.value) return

  if (window.revenueChartInstance) {
    window.revenueChartInstance.destroy()
  }

  const monthlyTotals: Record<string, number> = {}
  filteredRevenueData.value.forEach((item) => {
    if (!item.dateTime) return
    const dateObj = new Date(item.dateTime)
    const month = `${dateObj.getFullYear()}-${String(dateObj.getMonth() + 1).padStart(2, '0')}`
    if (!monthlyTotals[month]) monthlyTotals[month] = 0
    monthlyTotals[month] += Number(item.amount)
  })

  const ymList = Object.keys(monthlyTotals).sort()
  const labels = ymList.map((m) => getMonthLabel(m))
  const values = ymList.map((month) => monthlyTotals[month])
  // console.log('labelsss', labels)

  window.revenueChartInstance = new Chart(revenueChart.value, {
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
    <div class="chart-header">
      <h3>Revenue Over Time</h3>
      <div class="date-range-picker">
        <label>Start Date:</label>
        <input type="date" v-model="startDate" />
        <label>End Date:</label>
        <input type="date" v-model="endDate" />
        <button @click="applyDateFilter">Apply</button>
        <button @click="resetDateFilter">Reset</button>
      </div>
    </div>
    <canvas ref="revenueChart" height="90"></canvas>
  </div>
</template>

<style scoped>
.dashboard-chart {
  background: #f4fafe;
  border-radius: 18px;
  box-shadow: 0 4px 14px #0001;
  padding: 20px 30px 16px 30px;
  margin-bottom: 30px;
  color: black;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}

.date-range-picker {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.date-range-picker label {
  font-weight: bold;
}

.date-range-picker input[type="date"] {
  padding: 5px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.date-range-picker button {
  padding: 5px 10px;
  background-color: #36A2EB;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.date-range-picker button:hover {
  background-color: #2a8acb;
}

</style>