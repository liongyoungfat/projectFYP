<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { Chart, registerables } from 'chart.js'
import axios from 'axios'
import html2pdf from 'html2pdf.js'

Chart.register(...registerables)

const profitChart = ref<HTMLCanvasElement | null>(null)
const profitChartInstance = ref<Chart | null>(null)
const localhost = 'http://localhost:5000/'

const revenueData = ref<RevenueItem[]>([])
const expensesData = ref<ExpenseItem[]>([])

const startDate = ref<string>('')
const endDate = ref<string>('')
const showDatePicker = ref(false)
const isFilterApplied = ref(false)

const currentYear = new Date().getFullYear()
const defaultStartDate = `${currentYear}-01-01`
const defaultEndDate = `${currentYear}-12-31`

// Initialize with current year dates
startDate.value = defaultStartDate
endDate.value = defaultEndDate
isFilterApplied.value = true

interface RevenueItem {
  amount: number
  dateTime: string
}

interface ExpenseItem {
  amount: number
  dateTime: string
}

// const fetchExpenseData = async () => {
//   try {
//     const res = await axios.get(localhost + 'api/expenses')
//     expensesData.value = res.data
//     renderProfitChart()
//   } catch (err) {
//     console.error('Failed to fetch expense data:', err)
//   }
// }

const fetchExpenseData = async () => {
  try {
    const params: Record<string, string> = {}
    if (isFilterApplied.value) {
      params.start_date = startDate.value
      params.end_date = endDate.value
    }
    console.log('params', params)
    const res = await axios.get(localhost + 'api/expenses/certain/period', { params })
    expensesData.value = res.data
    renderProfitChart()
  } catch (err) {
    console.error('Failed to fetch expense data:', err)
  }
}

// Fetch revenue data with date range filtering
const fetchRevenueData = async () => {
  try {
    const params: Record<string, string> = {}
    if (isFilterApplied.value) {
      params.start_date = startDate.value
      params.end_date = endDate.value
    }
    console.log('params1', params)
    const res = await axios.get(localhost + 'api/revenues/certain/period', { params })
    revenueData.value = res.data
  } catch (err) {
    console.error('Failed to fetch revenue data:', err)
  }
}

// Apply date filter
const applyDateFilter = () => {
  isFilterApplied.value = true
  showDatePicker.value = false
  fetchRevenueData()
  fetchExpenseData()
}

// Reset date filter
const resetDateFilter = () => {
  startDate.value = defaultStartDate
  endDate.value = defaultEndDate
  isFilterApplied.value = true // Still using a date range
  showDatePicker.value = false
  fetchRevenueData()
  fetchExpenseData()
}

const renderProfitChart = () => {
  if (!profitChart.value || revenueData.value.length === 0 || expensesData.value.length === 0)
    return

  // Group data by month
  const revenueByMonth: Record<string, number> = {}
  revenueData.value.forEach((item) => {
    if (!item.dateTime) return
    const dateObj = new Date(item.dateTime)
    const m = `${dateObj.getFullYear()}-${String(dateObj.getMonth() + 1).padStart(2, '0')}`
    revenueByMonth[m] = (revenueByMonth[m] || 0) + Number(item.amount)
  })
  console.log('revenueBymonth in protit', revenueByMonth)
  console.log('Fetched expense data in profit:', expensesData.value)
  const expenseByMonth: Record<string, number> = {}
  expensesData.value.forEach((item) => {
    if (!item.dateTime) return
    const dateObj = new Date(item.dateTime)
    const m = `${dateObj.getFullYear()}-${String(dateObj.getMonth() + 1).padStart(2, '0')}`
    expenseByMonth[m] = (expenseByMonth[m] || 0) + Number(item.amount)
  })
  console.log('expensesBymonth in protit', expenseByMonth)

  const months = Array.from(
    new Set([...Object.keys(revenueByMonth), ...Object.keys(expenseByMonth)]),
  ).sort()
  console.log('months', months)

  // ✅ ADD GUARD: Skip rendering if no months (empty chart)
  if (months.length === 0) {
    console.warn('No data available for the selected date range.')
    return
  }

  const profitValues = months.map((m) => (revenueByMonth[m] || 0) - (expenseByMonth[m] || 0))
  const monthsLabels = months.map((m) => getMonthLabel(m))
  console.log('profitValues', profitValues)
  console.log('monthsLabels', monthsLabels)
  if (profitChartInstance.value) {
    profitChartInstance.value.destroy()
    profitChartInstance.value = null
  }
  console.log('prchart', profitChartInstance)
  const title = isFilterApplied.value
    ? `Net Profit Trend (${startDate.value} to ${endDate.value})`
    : 'Net Profit Trend'
  try {
    profitChartInstance.value = new Chart(profitChart.value, {
      type: 'line',
      data: {
        labels: monthsLabels,
        datasets: [
          {
            label: 'Net Profit (RM)',
            data: profitValues,
            borderColor: '#ff6384',
            backgroundColor: 'rgba(255, 99, 132, 0.1)',
            fill: {
              target: 'origin', // Safe structure
              above: 'rgba(255,99,132,0.1)',
              below: 'rgba(255,99,132,0.1)',
            },
            tension: 0.3,
            clip: false,
          },
        ],
      },
      options: {
        responsive: true,
        plugins: {
          title: {
            display: true,
            text: title,
            font: {
              size: 16,
              weight: 'bold',
            },
          },
          tooltip: {
            mode: 'index',
            intersect: false,
          },
          legend: {
            position: 'top',
          },
        },
        scales: {
          y: {
            beginAtZero: true,
            title: {
              display: true,
              text: 'Amount (RM)',
              font: {
                weight: 'bold',
              },
            },
            grid: {
              color: 'rgba(0, 0, 0, 0.05)',
            },
          },
          x: {
            title: {
              display: true,
              text: 'Month',
              font: {
                weight: 'bold',
              },
            },
            grid: {
              display: false,
            },
          },
        },
        interaction: {
          intersect: false,
          mode: 'nearest',
        },
      },
    })
  } catch (err) {
    console.error('Chart rendering error:', err)
  }
}

// const renderProfitChart = () => {
//   if (!profitChart.value || revenueData.value.length === 0 || expensesData.value.length === 0)
//     return

//   const revenueByMonth: Record<string, number> = {}
//   revenueData.value.forEach((item) => {
//     if (!item.dateTime) return
//     const dateObj = new Date(item.dateTime)
//     const m = `${dateObj.getFullYear()}-${String(dateObj.getMonth() + 1).padStart(2, '0')}`
//     revenueByMonth[m] = (revenueByMonth[m] || 0) + Number(item.amount)
//   })
//   console.log('rBM', revenueByMonth)
//   const expenseByMonth: Record<string, number> = {}
//   expensesData.value.forEach((item) => {
//     if (!item.dateTime) return
//     const dateObj = new Date(item.dateTime)
//     const m = `${dateObj.getFullYear()}-${String(dateObj.getMonth() + 1).padStart(2, '0')}`
//     expenseByMonth[m] = (expenseByMonth[m] || 0) + Number(item.amount)
//   })
//   console.log('eBM', expenseByMonth)

//   const months = Array.from(
//     new Set([...Object.keys(revenueByMonth), ...Object.keys(expenseByMonth)]),
//   ).sort()
//   const profitValues = months.map((m) => (revenueByMonth[m] || 0) - (expenseByMonth[m] || 0))
//   const monthsLabels = months.map((m) => getMonthLabel(m))

//   new Chart(profitChart.value, {
//     type: 'line',
//     data: {
//       labels: monthsLabels,
//       datasets: [
//         {
//           label: 'Net Profit (RM)',
//           data: profitValues,
//           borderColor: '#ff6384',
//           fill: false,
//         },
//       ],
//     },
//     options: {
//       responsive: true,
//       plugins: {
//         title: { display: true, text: 'Net Profit Trend' },
//       },
//       scales: {
//         y: {
//           beginAtZero: true,
//           title: { display: true, text: 'Amount (RM)' },
//         },
//         x: {
//           title: { display: true, text: 'Month' },
//         },
//       },
//     },
//   })
// }

function getMonthLabel(ym: string) {
  if (!ym) return ''
  return new Date(ym + '-01').toLocaleString('default', { month: 'short', year: '2-digit' })
}

const exportProfitChart = () => {
  const container = document.getElementById('profit-chart-container')
  if (!container) return

  const now = new Date()
  const timestamp =
    now.toISOString().split('T')[0] + '_' + now.toTimeString().split(' ')[0].replace(/:/g, '-')
  const filename = `ProfitTrend_${timestamp}.pdf`

  const opt = {
    margin: 0.3,
    filename: filename,
    image: { type: 'jpeg', quality: 0.98 },
    html2canvas: { scale: 2 },
    jsPDF: { unit: 'in', format: 'letter', orientation: 'landscape' },
  }

  html2pdf().set(opt).from(container).save()
}

onMounted(() => {
  fetchRevenueData()
  fetchExpenseData()
  renderProfitChart()
})
</script>
<template>
  <div class="profit-trend-container">
    <div class="chart-header">
      <h3>Net Profit Trend</h3>
      <div class="date-range-controls">
        <button @click="showDatePicker = !showDatePicker" class="date-range-btn">
          <i class="fas fa-calendar-alt"></i>
          {{ isFilterApplied ? 'Change Date Range' : 'Select Date Range' }}
        </button>
        <div v-if="showDatePicker" class="date-picker-popup">
          <div class="date-input-group">
            <label>Start Date:</label>
            <input type="date" v-model="startDate" />
          </div>
          <div class="date-input-group">
            <label>End Date:</label>
            <input type="date" v-model="endDate" />
          </div>
          <div class="date-picker-actions">
            <button @click="applyDateFilter" class="apply-btn">Apply</button>
            <button @click="resetDateFilter" class="reset-btn">Reset</button>
          </div>
        </div>
        <div v-if="isFilterApplied" class="current-range">
          {{ startDate }} to {{ endDate }}
          <button @click="resetDateFilter" class="clear-btn">
            <i class="fas fa-times"></i>
          </button>
        </div>
      </div>
      <div class="export-controls">
        <button @click="exportProfitChart">Export as PDF</button>
      </div>
    </div>

    <div class="chart-wrapper" id="profit-chart-container">
      <canvas ref="profitChart" height="250"></canvas>
    </div>
  </div>
</template>

<style scoped>
.widget {
  padding: 1rem;
}

#profit-chart-container {
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
  background-color: #22c55e;
  color: white;
  cursor: pointer;
}

.export-controls button:hover {
  background-color: #16a34a;
}
</style>
