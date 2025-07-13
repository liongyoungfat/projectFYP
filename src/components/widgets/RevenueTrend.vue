<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Chart, registerables } from 'chart.js'
import axios from 'axios'
import html2pdf from 'html2pdf.js'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
const companyId = userStore.company_id

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
    const res = await axios.get(localhost + 'api/revenues', { params: { company_id: companyId } })
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

const exportRevenueChart = () => {
  const container = document.getElementById('revenue-chart-container')
  if (!container) return

  const now = new Date()
  const timestamp =
    now.toISOString().split('T')[0] + '_' + now.toTimeString().split(' ')[0].replace(/:/g, '-')
  const filename = `RevenueTrend_${timestamp}.pdf`

  const opt = {
    margin: 0.3,
    filename: filename,
    image: { type: 'jpeg', quality: 0.98 },
    html2canvas: { scale: 2 },
    jsPDF: { unit: 'in', format: 'letter', orientation: 'landscape' },
  }

  html2pdf().set(opt).from(container).save()
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
    <div class="export-controls">
      <button @click="exportRevenueChart">Export as PDF</button>
    </div>
    <div id="revenue-chart-container">
      <canvas ref="revenueChart" height="90"></canvas>
    </div>
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

.date-range-picker input[type='date'] {
  padding: 5px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.date-range-picker button {
  padding: 5px 10px;
  background-color: #36a2eb;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.date-range-picker button:hover {
  background-color: #2a8acb;
}

#revenue-chart-container {
  background: #ffffff;
  padding: 16px;
  border-radius: 12px;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.05);
  margin-top: 16px;
}

.export-controls {
  margin-bottom: 12px;
  display: flex;
  justify-content: flex-end;
}

.export-controls button {
  padding: 6px 12px;
  font-weight: 500;
  border-radius: 6px;
  border: none;
  background-color: #3b82f6;
  color: white;
  cursor: pointer;
}

.export-controls button:hover {
  background-color: #2563eb;
}
</style>
