<script setup lang="ts">
import { ref, onMounted, watch, nextTick, computed } from 'vue'
import { Chart, registerables } from 'chart.js'
import axios from 'axios'
import html2pdf from 'html2pdf.js'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
const companyId = userStore.company_id
const isAdmin = computed(() => userStore.role === 'admin')

Chart.register(...registerables)

const monthlyChart = ref<HTMLCanvasElement | null>(null)
const chartInstance = ref<Chart | null>(null)
const localhost = 'http://18.232.124.137:8000/'

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

startDate.value = defaultStartDate
endDate.value = defaultEndDate
const threshold = ref<number | null>(null)
const tempThreshold = ref(0)

const fetchExpenseData = async () => {
  try {
    const response = await axios.get(localhost + 'api/expenses/certain/period', {
      params: {
        start_date: startDate.value,
        end_date: endDate.value,
        company_id: companyId,
      },
    })
    rawExpenseData.value = response.data
    processChartData()
  } catch (error) {
    console.error('Error fetching expense data:', error)
  }
}
const processChartData = async () => {
  // Group by month
  const monthlyTotals: Record<string, number> = {}

  rawExpenseData.value.forEach((expense) => {
    const date = new Date(expense.dateTime)
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
  await nextTick() // Ensure canvas is in DOM
  renderCharts(monthlyData)
}

const renderCharts = (monthlyData: MonthlyDataItem[]) => {
  if (!monthlyData || monthlyData.length === 0) return
  if (!monthlyChart.value) {
    console.warn('Chart canvas not ready.')
    return
  }

  const ctx = monthlyChart.value.getContext('2d')
  if (!ctx) {
    console.warn('Canvas context is null.')
    return
  }

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

const fetchThreshold = async () => {
  try {
    const response = await axios.get(localhost + 'api/companies/threshold', {
      params: {
        company_id: companyId,
      },
    })
    const parsed = parseFloat(response.data.threshold)
    threshold.value = parsed
    tempThreshold.value = parsed
  } catch (error) {
    console.error('Error fetching threshold:', error)
  }
}

const isEditingThreshold = ref(false)

const startEditing = () => {
  isEditingThreshold.value = true
  tempThreshold.value = threshold.value || 0
}

const submitThreshold = async () => {
  try {
    await axios.post(localhost + 'api/companies/threshold/update', {
      company_id: companyId,
      new_threshold: tempThreshold.value,
    })
    threshold.value = tempThreshold.value
    isEditingThreshold.value = false
    alert('Threshold updated!')
  } catch (error) {
    console.error('Failed to update threshold:', error)
  }
}

const applyDateFilter = () => {
  showDatePicker.value = false
  fetchExpenseData()
}

// Reset to default date range (current year)
const resetDateFilter = () => {
  startDate.value = defaultStartDate
  endDate.value = defaultEndDate
  showDatePicker.value = false
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

  // 🔧 Add slight delay to allow Chart.js to fully draw
  setTimeout(() => {
    html2pdf().set(opt).from(container).save()
  }, 300)
}

onMounted(async () => {
  fetchThreshold()
  await nextTick()
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
      <h3 class="chart-title">📊 Monthly Expenses</h3>

      <div class="toolbar-actions">
        <div class="date-button-wrapper">
          <button @click="showDatePicker = !showDatePicker" class="date-toggle-btn animated-btn">
            <span class="date-btn-icon">📅</span>
            <span>{{
              startDate && endDate ? `${startDate} → ${endDate}` : 'Select Date Range'
            }}</span>
          </button>

          <transition name="date-popup-fade">
            <div v-if="showDatePicker" class="date-popup attractive-popup">
              <div class="date-field">
                <label>Start Date:</label>
                <div class="date-input-wrapper">
                  <input type="date" v-model="startDate" class="animated-date-input" />
                </div>
              </div>
              <div class="date-field">
                <label>End Date:</label>
                <div class="date-input-wrapper">
                  <input type="date" v-model="endDate" class="animated-date-input" />
                </div>
              </div>
              <div class="popup-buttons">
                <button class="apply-btn attractive-btn animated-btn" @click="applyDateFilter">
                  Apply
                </button>
                <button class="reset-btn attractive-btn animated-btn" @click="resetDateFilter">
                  Reset
                </button>
              </div>
            </div>
          </transition>
        </div>

        <div class="export-controls">
          <button class="export-btn attractive-btn animated-btn" @click="exportChart">
            <span class="export-btn-icon">📤</span>
            <span>Export as PDF</span>
          </button>
        </div>
      </div>
    </div>

    <div class="toolbar-secondary">
      <div class="threshold-input">
        <p v-if="!isEditingThreshold">
          Expense Threshold (RM):
          <span class="threshold-value">RM {{ threshold?.toFixed(2) }}</span>
        </p>
        <!-- Edit mode -->
        <div v-if="isAdmin">
          <div v-if="isEditingThreshold">
            <input
              v-model="tempThreshold"
              type="number"
              placeholder="e.g. 10000"
              class="input-threshold"
            />
            <button @click="submitThreshold" class="btn-confirm">Submit</button>
          </div>
          <div v-else>
            <button @click="startEditing" class="btn-edit">Edit</button>
          </div>
        </div>
      </div>

      <div class="current-range">Current Range: {{ startDate }} → {{ endDate }}</div>
    </div>

    <div class="chart-wrapper" id="expenses-chart-container">
      <template v-if="chartData.length > 0">
        <canvas ref="monthlyChart"></canvas>
      </template>
      <template v-else>
        <div class="empty-chart-state">
          <span class="empty-icon">📉</span>
          <div class="empty-message">No expense data available for this period.</div>
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
.chart-container {
  background: #f9f9fc;
  border-radius: 14px;
  padding: 24px;
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.06);
  color: #1f2937;
  font-family: 'Segoe UI', sans-serif;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  flex-wrap: wrap;
  align-items: center;
  gap: 16px;
}

.chart-title {
  font-size: 1.5rem;
  font-weight: 700;
}

.toolbar-actions {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
}

.date-button-wrapper {
  position: relative;
}

.date-toggle-btn {
  background: linear-gradient(90deg, #6366f1 60%, #3b82f6 100%);
  color: white;
  padding: 10px 18px;
  border-radius: 8px;
  font-weight: 700;
  font-size: 1rem;
  display: flex;
  align-items: center;
  gap: 10px;
  border: none;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.09);
  transition:
    background 0.18s,
    color 0.18s,
    box-shadow 0.18s,
    transform 0.18s;
  will-change: transform, box-shadow;
}
.date-toggle-btn:hover {
  background: linear-gradient(90deg, #4f46e5 60%, #2563eb 100%);
  transform: scale(1.07) translateY(-2px) rotate(-1deg);
  box-shadow: 0 6px 18px rgba(99, 102, 241, 0.18);
}
.date-toggle-btn:active {
  transform: scale(0.95) rotate(1deg);
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.18);
}
.date-btn-icon {
  font-size: 1.2rem;
  margin-right: 4px;
  transition: transform 0.18s;
}

.export-btn {
  background: linear-gradient(90deg, #3b82f6 60%, #6366f1 100%);
  color: white;
  padding: 10px 18px;
  border-radius: 8px;
  font-weight: 700;
  font-size: 1rem;
  border: none;
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.09);
  transition:
    background 0.18s,
    color 0.18s,
    box-shadow 0.18s,
    transform 0.18s;
  will-change: transform, box-shadow;
}
.export-btn:hover {
  background: linear-gradient(90deg, #2563eb 60%, #4f46e5 100%);
  color: #fff;
  transform: scale(1.07) translateY(-2px) rotate(-1deg);
  box-shadow: 0 6px 18px rgba(59, 130, 246, 0.18);
}
.export-btn:active {
  transform: scale(0.95) rotate(1deg);
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.18);
}
.export-btn-icon {
  font-size: 1.2rem;
  margin-right: 4px;
  transition: transform 0.18s;
}

.date-popup-fade-enter-active,
.date-popup-fade-leave-active {
  transition:
    opacity 0.32s cubic-bezier(0.4, 0, 0.2, 1),
    transform 0.32s cubic-bezier(0.4, 0, 0.2, 1);
}
.date-popup-fade-enter-from,
.date-popup-fade-leave-to {
  opacity: 0;
  transform: translateY(-18px) scale(0.98);
}
.date-popup-fade-enter-to,
.date-popup-fade-leave-from {
  opacity: 1;
  transform: translateY(0) scale(1);
}
.attractive-popup {
  border: 2px solid #6366f1;
  box-shadow: 0 8px 24px rgba(99, 102, 241, 0.13);
  animation: popup-bounce 0.38s cubic-bezier(0.4, 0, 0.2, 1);
}
@keyframes popup-bounce {
  0% {
    transform: scale(0.95);
  }
  60% {
    transform: scale(1.04);
  }
  100% {
    transform: scale(1);
  }
}
.date-popup {
  position: absolute;
  top: 110%;
  left: 0;
  background: white;
  padding: 16px;
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(99, 102, 241, 0.13);
  z-index: 10;
  width: 260px;
}
.date-input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}
.animated-date-input {
  width: 100%;
  padding: 8px 36px 8px 12px;
  font-size: 1rem;
  border: 1.5px solid #d1d5db;
  border-radius: 8px;
  transition:
    border-color 0.18s,
    box-shadow 0.18s;
  box-shadow: 0 1px 4px rgba(99, 102, 241, 0.04);
  background: #f9fafb;
  color: #222;
}
.animated-date-input:focus {
  border-color: #6366f1;
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.13);
  background: #eef2ff;
}
.date-icon {
  position: absolute;
  right: 12px;
  font-size: 1.2rem;
  color: #6366f1;
  pointer-events: none;
  transition: color 0.18s;
}
.attractive-btn {
  font-size: 1rem;
  padding: 7px 16px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.09);
  transition:
    background 0.18s,
    color 0.18s,
    box-shadow 0.18s,
    transform 0.18s;
}
.attractive-btn:active {
  transform: scale(0.95);
}
.attractive-btn:hover {
  background: #eef2ff;
  color: #6366f1;
  box-shadow: 0 6px 18px rgba(99, 102, 241, 0.18);
}

.date-field {
  margin-bottom: 12px;
}

.date-field label {
  display: block;
  font-weight: 600;
  margin-bottom: 5px;
  font-size: 0.85rem;
}

.date-field input {
  width: 100%;
  padding: 8px 10px;
  border: 1px solid #ccc;
  border-radius: 6px;
  font-size: 0.9rem;
}

.popup-buttons {
  display: flex;
  justify-content: space-between;
  gap: 10px;
}

.apply-btn {
  background: #10b981;
  color: white;
  padding: 6px 12px;
  border-radius: 6px;
  font-weight: 600;
  border: none;
  flex: 1;
  cursor: pointer;
}

.apply-btn:hover {
  background: #059669;
}

.reset-btn {
  background: #f3f4f6;
  color: #374151;
  padding: 6px 12px;
  border-radius: 6px;
  font-weight: 600;
  border: none;
  flex: 1;
  cursor: pointer;
}

.reset-btn:hover {
  background: #e5e7eb;
}

.btn-confirm {
  margin-left: 8px;
  padding: 5px 10px;
  background-color: #0099cc;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.25s ease-in-out;
}

.btn-confirm:hover {
  background-color: #0077aa;
  transform: scale(1.05);
}

.btn-edit {
  background-color: #6b7280;
  color: white;
  padding: 6px 12px;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  transition: all 0.25s ease-in-out;
}

.btn-edit:hover {
  background: #4b5563;
  transform: scale(1.05);
}

.input-threshold {
  padding: 6px 10px;
  margin-right: 8px;
  font-size: 0.9rem;
  border: 1px solid #ccc;
  border-radius: 6px;
  width: 120px;
}

/* No duplicate .export-btn styles; only gradient version remains above. */

.toolbar-secondary {
  display: flex;
  justify-content: space-between;
  flex-wrap: wrap;
  align-items: center;
  margin: 20px 0;
  gap: 14px;
}

.threshold-input {
  display: flex;
  align-items: center;
  gap: 10px;
}

.threshold-input label {
  font-weight: 600;
}

.threshold-input input {
  padding: 6px 10px;
  border-radius: 6px;
  border: 1px solid #d1d5db;
  font-size: 0.9rem;
  max-width: 140px;
}

.threshold-value {
  font-weight: 600;
  font-size: 1.1rem;
  color: #111827;
}

.current-range {
  background: #eef2ff;
  color: #4338ca;
  padding: 6px 12px;
  border-radius: 6px;
  font-weight: 600;
  font-size: 0.9rem;
}

.chart-wrapper {
  background: white;
  padding: 24px;
  max-height: 75%;
  border-radius: 16px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.04);
}

.empty-chart-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 120px;
  color: #888;
  font-size: 1.1rem;
  padding: 24px 0;
}
.empty-icon {
  font-size: 2.5rem;
  margin-bottom: 8px;
}
.empty-message {
  font-size: 1.1rem;
  color: #888;
}
</style>
