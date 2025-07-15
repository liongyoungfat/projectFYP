<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { Chart, registerables } from 'chart.js'
import axios from 'axios'
import html2pdf from 'html2pdf.js'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
const companyId = userStore.company_id
const isComponentMounted = ref(true)

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
const showHoverTip = ref(false)

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

const fetchExpenseData = async () => {
  try {
    const params: Record<string, string> = {}
    if (isFilterApplied.value) {
      params.start_date = startDate.value
      params.end_date = endDate.value
      if (companyId !== null && companyId !== undefined) {
        params.company_id = String(companyId)
      }
    }
    console.log('params', params)
    const res = await axios.get(localhost + 'api/expenses/certain/period', { params })
    expensesData.value = res.data
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
      if (companyId !== null && companyId !== undefined) {
        params.company_id = String(companyId)
      }
    }
    console.log('params1', params)
    const res = await axios.get(localhost + 'api/revenues/certain/period', { params })
    await nextTick()
    revenueData.value = res.data
  } catch (err) {
    console.error('Failed to fetch revenue data:', err)
  }
}

// Apply date filter
const applyDateFilter = async () => {
  isFilterApplied.value = true
  showDatePicker.value = false
  await fetchData()
}

// Reset date filter
const resetDateFilter = async () => {
  startDate.value = defaultStartDate
  endDate.value = defaultEndDate
  isFilterApplied.value = true // Still using a date range
  showDatePicker.value = false

  await fetchData()
}

const renderProfitChart = () => {
  console.log('Canvas element is:', profitChart.value)
  console.log('Canvas context is:', profitChart.value?.getContext?.('2d'))
  if (!profitChart.value || revenueData.value.length === 0 || expensesData.value.length === 0)
    return

  if (!profitChart.value) {
    console.warn('❌ Canvas not yet mounted. Retrying in 100ms...')
    setTimeout(renderProfitChart, 100)
    return
  }
  const ctx = profitChart.value.getContext('2d')
  if (!ctx) {
    console.error('Canvas context is null')
    return
  }

  if (revenueData.value.length === 0 || expensesData.value.length === 0) {
    console.warn('❌ No data yet to render chart.')
    return
  }
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
            fill: false,
            tension: 0.3,
            clip: undefined,
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

const fetchData = async () => {
  try {
    await fetchRevenueData()
    await fetchExpenseData()
    if (isComponentMounted.value) {
      renderProfitChart()
    }
  } catch (error) {
    console.error('Data fetch failed', error)
  }
}

onMounted(fetchData)

onUnmounted(() => {
  isComponentMounted.value = false
  if (profitChartInstance.value) {
    profitChartInstance.value.destroy()
  }
})
</script>
<template>
  <div class="dashboard-chart">
    <div class="chart-toolbar">
      <h3 class="chart-title">📈 Net Profit Trend</h3>

      <div class="toolbar-actions">
        <div class="date-button-wrapper" @mouseleave="showHoverTip = false">
          <button
            @click="showDatePicker = !showDatePicker"
            @mouseenter="showHoverTip = true"
            class="date-toggle-btn"
          >
            <span class="date-btn-icon">📅</span>
            {{ startDate || 'Start Date' }} → {{ endDate || 'End Date' }}
          </button>
          <div v-if="showHoverTip" class="hover-tip">Choose a date range to filter profit</div>
        </div>

        <button class="export-btn attractive-btn animated-btn" @click="exportProfitChart">
          <span class="export-btn-icon">📤</span>
          <span>Export as PDF</span>
        </button>
      </div>

      <div v-if="showDatePicker" class="date-popup">
        <div class="date-field">
          <label>Start Date:</label>
          <input type="date" v-model="startDate" />
        </div>
        <div class="date-field">
          <label>End Date:</label>
          <input type="date" v-model="endDate" />
        </div>
        <div class="popup-buttons">
          <button class="animated-btn filter-btn" @click="applyDateFilter">Apply</button>
          <button class="animated-btn reset-btn" @click="resetDateFilter">Reset</button>
        </div>
      </div>
    </div>

    <div v-if="startDate && endDate" class="date-display">
      <span class="date-label">Current Range:</span>
      <span class="date-value">{{ startDate }} → {{ endDate }}</span>
    </div>

    <div class="chart-wrapper" id="profit-chart-container">
      <canvas
        ref="profitChart"
        height="250"
        v-if="revenueData.length > 0 && expensesData.length > 0"
      ></canvas>
      <div v-else>Loading chart data...</div>
    </div>
  </div>
</template>

<style scoped>
.dashboard-chart {
  background: #f4fafe;
  padding: 24px;
  border-radius: 18px;
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.08);
  font-family: 'Segoe UI', sans-serif;
  color: #111;
}

.chart-toolbar {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
  position: relative;
}

.chart-title {
  font-size: 1.5rem;
  font-weight: 700;
  margin: 0;
  color: #111827;
}

.toolbar-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.date-toggle-btn,
.export-btn {
  background-color: #6366f1;
  color: white;
  font-size: 0.95rem;
  padding: 8px 16px;
  font-weight: 600;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition:
    background 0.2s ease,
    transform 0.2s ease;
}

.date-toggle-btn:hover,
.export-btn:hover {
  background-color: #4f46e5;
  transform: scale(1.05);
}

.date-popup {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 10px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.1);
  padding: 16px;
  min-width: 240px;
  z-index: 100;
}

.date-popup .date-field {
  margin-bottom: 12px;
}

.date-popup label {
  font-size: 0.85rem;
  font-weight: 600;
  margin-bottom: 4px;
  display: block;
}

.date-popup input[type='date'] {
  width: 100%;
  padding: 8px;
  font-size: 0.9rem;
  border: 1px solid #d1d5db;
  border-radius: 6px;
}

.popup-buttons {
  display: flex;
  justify-content: space-between;
}

.date-button-wrapper {
  position: relative;
}

.hover-tip {
  position: absolute;
  top: 110%;
  left: 0;
  background-color: #fefefe;
  color: #333;
  font-size: 0.8rem;
  padding: 6px 10px;
  border-radius: 6px;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
  white-space: nowrap;
  z-index: 10;
}

.date-display {
  background: #eef2ff;
  color: #4338ca;
  padding: 6px 12px;
  border-radius: 6px;
  font-weight: 600;
  font-size: 0.9rem;
  margin-bottom: 20px;
  display: inline-block;
}

.filter-btn {
  background-color: #3b82f6;
  color: white;
  padding: 6px 12px;
  border-radius: 6px;
}

.reset-btn {
  background-color: #d1d5db;
  color: #333;
  padding: 6px 12px;
  border-radius: 6px;
}

.animated-btn {
  transition: all 0.2s ease;
}

.animated-btn:active {
  transform: scale(0.95);
}

.animated-btn:hover {
  transform: scale(1.04);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

#profit-chart-container {
  background: white;
  padding: 24px;
  border-radius: 16px;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.06);
}

.chart-wrapper {
  background: white;
  padding: 24px;
  border-radius: 16px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.04);
}
</style>
