<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { Chart, registerables } from 'chart.js'
import axios from 'axios'
import html2pdf from 'html2pdf.js'

Chart.register(...registerables)

const monthlyChart = ref<HTMLCanvasElement | null>(null)
const chartInstance = ref<Chart | null>(null)
const localhost = 'http://localhost:5000/'

interface MonthlyDataItem {
  month_name: string
  total_amount: number
}

interface ExpenseItem {
  id: number
  dateTime: string
  payment_method: string
  user_id: number
  category: string
  amount: number
}

const startDate = ref<string>('')
const endDate = ref<string>('')
const showDatePicker = ref(false)
const rawExpenseData = ref<ExpenseItem[]>([])
const chartData = ref<MonthlyDataItem[]>([])

const currentYear = new Date().getFullYear()
const defaultStartDate = `${currentYear}-01-01`
const defaultEndDate = `${currentYear}-12-31`

// Initialize with current year dates
startDate.value = defaultStartDate
endDate.value = defaultEndDate
const threshold = ref<number | null>(null)

const fetchExpenseData = async () => {
  try {
    const response = await axios.get(localhost + '/api/expenses/certain/period', {
      params: {
        start_date: startDate.value,
        end_date: endDate.value,
      },
    })
    rawExpenseData.value = response.data
    processChartData()
  } catch (error) {
    console.error('Error fetching expense data:', error)
  }
}
const processChartData = () => {
  // Group by month
  const monthlyTotals: Record<string, number> = {}

  rawExpenseData.value.forEach((expense) => {
    const date = new Date(expense.dateTime)
    const month = date.toLocaleString('default', { month: 'short' })
    const year = date.getFullYear()
    const monthKey = `${year}-${date.getMonth() + 1}`

    if (!monthlyTotals[monthKey]) {
      monthlyTotals[monthKey] = 0
    }
    monthlyTotals[monthKey] += expense.amount
  })

  // Convert to array and sort by date
  const monthlyData = Object.keys(monthlyTotals)
    .map((key) => {
      const [year, month] = key.split('-')
      const date = new Date(parseInt(year), parseInt(month) - 1, 1)
      return {
        month_name: date.toLocaleString('default', { month: 'short' }) + ' ' + year,
        total_amount: monthlyTotals[key],
      }
    })
    .sort((a, b) => {
      return new Date(a.month_name).getTime() - new Date(b.month_name).getTime()
    })
  chartData.value = monthlyData
  renderCharts(monthlyData)
}

// const fetchChartData = async () => {
//   try {
//     const res = await axios.get(localhost + '/api/expenses/summary/monthly', {
//       params: {
//         year: selectedYear.value,
//       },
//     })
//     monthlyExpenses.value = res.data
//     renderCharts(res.data)
//   } catch (error) {
//     console.error('Fetch error:', error)
//   }
// }

const monthlyExpenses = ref<Array<{ month_name: string; total_amount: number }>>([])

const renderCharts = (monthlyData: MonthlyDataItem[]) => {
  if (!monthlyData || monthlyData.length === 0) return
  if (!monthlyChart.value) return

  // Destroy existing chart instance if it exists
  if (chartInstance.value) {
    chartInstance.value.destroy()
  }
  console.log('mon data', monthlyData)

  const title =
    monthlyData.length > 0
      ? `Monthly Expenses (${startDate.value} to ${endDate.value})`
      : `No Expense Data (${startDate.value} to ${endDate.value})`

  const backgroundColors = monthlyData.map((item) => {
    if (threshold.value && item.total_amount > threshold.value) {
      return 'rgba(255, 99, 132, 0.8)' // red alert color
    }
    return 'rgba(75, 192, 192, 0.6)' // default bar color
  })

  chartInstance.value = new Chart(monthlyChart.value, {
    type: 'bar',
    data: {
      labels: monthlyData.map((item) => item.month_name),
      datasets: [
        {
          label: 'Monthly Expenses (RM)',
          data: monthlyData.map((item) => item.total_amount),
          backgroundColor: backgroundColors,
          borderColor: '#4BC0C0',
          borderWidth: 1,
        },
      ],
    },
    options: {
      responsive: true,
      scales: {
        y: {
          beginAtZero: true,
          title: {
            display: true,
            text: 'Amount',
          },
        },
        x: {
          title: {
            display: true,
            text: 'Month',
          },
        },
      },
      plugins: {
        title: {
          display: true,
          text: title,
        },
      },
    },
  })
}
// const renderCharts = (monthlyData: MonthlyDataItem[]) => {
//   if (!monthlyChart.value) return
//   new Chart(monthlyChart.value, {
//     type: 'bar',
//     data: {
//       labels: monthlyData.map((item) => item.month_name),
//       datasets: [
//         {
//           label: 'Monthly Expenses',
//           data: monthlyData.map((item) => item.total_amount),
//           backgroundColor: '#4BC0C0',
//           borderColor: '#4BC0C0',
//           borderWidth: 1,
//         },
//       ],
//     },
//     options: {
//       responsive: true,
//       scales: {
//         y: {
//           beginAtZero: true,
//           title: {
//             display: true,
//             text: 'Amount',
//           },
//         },
//         x: {
//           title: {
//             display: true,
//             text: 'Month',
//           },
//         },
//       },
//       plugins: {
//         title: {
//           display: true,
//           text: `Monthly Expenses Trend (${currentYear})`,
//         },
//       },
//     },
//   })
// }

const applyDateFilter = () => {
  showDatePicker.value = false
  fetchExpenseData()
}

// Reset to default date range (current year)
const resetDateFilter = () => {
  startDate.value = defaultStartDate
  endDate.value = defaultEndDate
  fetchExpenseData()
}

const exportChart = () => {
  const container = document.getElementById('expenses-chart-container')
  if (!container) return

  const now = new Date()
  const timestamp =
    now.toISOString().split('T')[0] + '_' + now.toTimeString().split(' ')[0].replace(/:/g, '-')
  const filename = `MonthlyExpensesChart_${timestamp}.pdf`

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
  // fetchChartData()
  fetchExpenseData()
})

watch(threshold, () => {
  if (chartData.value.length > 0) {
    renderCharts(chartData.value)
  }
})
</script>
<template>
  <div class="chart-container">
    <div class="chart-header">
      <h3>Monthly Expenses</h3>
      <div class="date-range-controls">
        <button @click="showDatePicker = !showDatePicker" class="date-range-btn">
          <i class="fas fa-calendar-alt"></i> Select Date Range
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
        <div class="current-range">{{ startDate }} to {{ endDate }}</div>
      </div>
      <div class="threshold-input">
        <label>Set Monthly Expense Threshold (RM):</label>
        <input type="number" v-model="threshold" placeholder="e.g. 10000" />
      </div>
      <div class="export-controls">
        <button @click="exportChart">Export as PDF</button>
      </div>
    </div>
    <div class="chart-wrapper" id="expenses-chart-container">
      <canvas ref="monthlyChart"></canvas>
    </div>
  </div>
</template>

<style scoped>
.chart-container {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 22px;
  margin-bottom: 30px;
  color: black;
}

.chart-wrapper {
  background: #f4fafe;
  border-radius: 18px;
  box-shadow: 0 4px 14px #0001;
  padding: 25px 18px 20px 18px;
  min-width: 300px;
  height: 410px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

canvas {
  width: 100% !important;
  max-width: 100%;
  height: 340px !important;
  display: block;
}

.chart-container {
  background: white;
  border-radius: 10px;
  padding: 20px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  margin-bottom: 25px;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 15px;
}

.date-range-controls {
  position: relative;
  display: flex;
  align-items: center;
  gap: 15px;
}

.date-range-btn {
  background: #4bc0c0;
  color: white;
  border: none;
  padding: 8px 15px;
  border-radius: 5px;
  cursor: pointer;
  font-size: 0.9rem;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: background 0.3s;
}

.date-range-btn:hover {
  background: #3aa9a9;
}

.date-picker-popup {
  position: absolute;
  top: 100%;
  right: 0;
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
  z-index: 10;
  width: 280px;
  margin-top: 10px;
}

.date-input-group {
  margin-bottom: 15px;
}

.date-input-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: 500;
  color: #555;
}

.date-input-group input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
}

.date-picker-actions {
  display: flex;
  gap: 10px;
  margin-top: 10px;
}

.apply-btn,
.reset-btn {
  flex: 1;
  padding: 8px 12px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 500;
}

.apply-btn {
  background: #4bc0c0;
  color: white;
}

.apply-btn:hover {
  background: #3aa9a9;
}

.reset-btn {
  background: #f0f0f0;
  color: #555;
}

.reset-btn:hover {
  background: #e0e0e0;
}

.current-range {
  background: #f8f9fa;
  padding: 6px 12px;
  border-radius: 4px;
  font-size: 0.9rem;
  color: #666;
  border: 1px solid #eee;
}

.threshold-input {
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 500;
}

.threshold-input input {
  padding: 6px 12px;
  border-radius: 6px;
  border: 1px solid #ccc;
  font-size: 14px;
  max-width: 160px;
}
</style>
