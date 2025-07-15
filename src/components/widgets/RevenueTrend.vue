<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
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

const currentYear = new Date().getFullYear()
const defaultStartDate = `${currentYear}-01-01`
const defaultEndDate = `${currentYear}-12-31`

startDate.value = defaultStartDate
endDate.value = defaultEndDate
const filteredRevenueData = ref<RevenueItem[]>([])
const isExporting = ref(false)
const showDatePicker = ref(false)
const showHoverTip = ref(false)

const fetchRevenueData = async () => {
  try {
    const res = await axios.get(localhost + 'api/revenues', { params: { company_id: companyId } })
    revenueData.value = res.data
    filteredRevenueData.value = [...revenueData.value]
    // console.log('Fetched revenue data:', revenueData.value)
    await nextTick()
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

const exportRevenueChart = async () => {
  if (isExporting.value) return
  isExporting.value = true

  try {
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

    await html2pdf().set(opt).from(container).save()
  } catch (err) {
    console.error('Export failed:', err)
  } finally {
    isExporting.value = false
  }
}

onMounted(fetchRevenueData)
</script>
<template>
  <div class="dashboard-chart">
    <div class="chart-toolbar">
      <h3 class="chart-title">📊 Revenue Over Time</h3>

      <div class="toolbar-actions">
        <div class="date-button-wrapper" @mouseleave="showHoverTip = false">
          <button
            @click="showDatePicker = !showDatePicker"
            @mouseenter="showHoverTip = true"
            class="date-toggle-btn"
          >
            <span class="date-btn-icon">📅</span>
            {{ startDate && endDate ? `${startDate} → ${endDate}` : 'Select Date Range' }}
          </button>
          <div v-if="showHoverTip" class="hover-tip">Choose a date range to filter revenue</div>
        </div>

        <button
          :disabled="isExporting"
          class="export-btn attractive-btn animated-btn"
          @click="exportRevenueChart"
        >
          <span class="export-btn-icon">📤</span>
          <span>{{ isExporting ? 'Generating PDF...' : 'Export as PDF' }}</span>
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

    <div id="revenue-chart-container">
      <div v-if="revenueData.length > 0">
        <canvas ref="revenueChart" height="120"></canvas>
      </div>
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
/* Export PDF button UI from MonthlyExpensesChart.vue */
.export-btn {
  background: linear-gradient(90deg, #3b82f6 60%, #6366f1 100%);
  color: white;
  padding: 6px 16px;
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

.date-toggle-btn {
  background-color: #2563eb;
  color: white;
  padding: 10px 16px;
  font-size: 0.95rem;
  font-weight: 600;
  border: none;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  transition:
    background 0.2s,
    transform 0.2s;
}

.date-toggle-btn:hover {
  background-color: #1d4ed8;
  transform: translateY(-1px);
}

.date-toggle-btn:focus {
  outline: 3px solid #93c5fd;
  outline-offset: 2px;
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
  transition:
    background 0.18s,
    color 0.18s,
    box-shadow 0.18s,
    transform 0.18s;
}
.animated-btn:active {
  transform: scale(0.95);
}
.animated-btn:hover {
  transform: scale(1.04);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

#revenue-chart-container {
  background: white;
  padding: 24px;
  border-radius: 16px;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.06);
}
</style>
