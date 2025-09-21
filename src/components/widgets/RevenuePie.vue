<script setup lang="ts">
import { ref, onMounted, computed, watch, nextTick } from 'vue'
import { Chart, registerables } from 'chart.js'
import axios from 'axios'
import { useUserStore } from '@/stores/user'
import html2pdf from 'html2pdf.js'

Chart.register(...registerables)

const userStore = useUserStore()
const companyId = userStore.company_id
const localhost = 'http://18.232.124.137:8000/'

const chartRef = ref<HTMLCanvasElement | null>(null)
const revenueData = ref<any[]>([])
const isLoading = ref(false)

const currentYear = new Date().getFullYear()
const currentMonth = new Date().getMonth() + 1

const availableDates = ref<{ year: number; month: number }[]>([])
const selectedYear = ref(currentYear)
const selectedMonth = ref(currentMonth)
const noDataMessage = ref('')

const fetchRevenueData = async () => {
  isLoading.value = true
  try {
    const res = await axios.get(localhost + 'api/revenues/summary/category', {
      params: {
        company_id: companyId,
        year: selectedYear.value,
        month: selectedMonth.value,
      },
    })
    revenueData.value = res.data
    if (revenueData.value.length === 0) {
      noDataMessage.value = 'No revenue data available for this period.'
    } else {
      noDataMessage.value = ''
      renderChart()
    }
    console.log('Revenue data fetched:', revenueData.value)
  } catch (err) {
    console.error('Failed to fetch revenue data:', err)
    noDataMessage.value = 'Failed to fetch revenue data.'
  } finally {
    isLoading.value = false
  }
}

const months = [
  { label: 'January', value: 1 },
  { label: 'February', value: 2 },
  { label: 'March', value: 3 },
  { label: 'April', value: 4 },
  { label: 'May', value: 5 },
  { label: 'June', value: 6 },
  { label: 'July', value: 7 },
  { label: 'August', value: 8 },
  { label: 'September', value: 9 },
  { label: 'October', value: 10 },
  { label: 'November', value: 11 },
  { label: 'December', value: 12 },
]

const fetchAvailableDates = async () => {
  const res = await axios.get(localhost + 'api/revenues/available-months', {
    params: { company_id: companyId },
  })
  availableDates.value = res.data
  if (availableYears.value.length > 0) {
    selectedYear.value = availableYears.value.includes(currentYear)
      ? currentYear
      : availableYears.value[0]

    const monthsForYear = availableDates.value
      .filter((item) => item.year === selectedYear.value)
      .map((item) => item.month)
      .sort((a, b) => b - a)
    selectedMonth.value = monthsForYear[0]
  }
}

const availableYears = computed(() =>
  [...new Set(availableDates.value.map((item) => item.year))].sort((a, b) => b - a),
)

const availableMonths = computed(() =>
  availableDates.value.filter((item) => item.year === selectedYear.value).map((item) => item.month),
)

const categoryTotals = computed(() => {
  const totals: Record<string, number> = {}
  revenueData.value.forEach((item) => {
    const cat = item.category || 'Other'
    if (!totals[cat]) totals[cat] = 0
    totals[cat] += Number(item.total_amount)
  })
  return totals
})

const renderChart = () => {
  if (!chartRef.value) return
  if ((window as any).revenuePieInstance) {
    ;(window as any).revenuePieInstance.destroy()
  }
  const data = categoryTotals.value
  const labels = Object.keys(data)
  const values = Object.values(data)
  const colors = [
    '#6366f1',
    '#fca311',
    '#36A2EB',
    '#f87171',
    '#34d399',
    '#fbbf24',
    '#a78bfa',
    '#f472b6',
    '#60a5fa',
    '#f59e42',
  ]
  ;(window as any).revenuePieInstance = new Chart(chartRef.value, {
    type: 'pie',
    data: {
      labels,
      datasets: [
        {
          data: values,
          backgroundColor: colors,
        },
      ],
    },
    options: {
      responsive: true,
      plugins: {
        legend: {
          display: true,
          position: 'bottom',
        },
        title: {
          display: true,
          text: 'Revenue by Category',
        },
      },
    },
  })
}

const exportRevenuePieChart = () => {
  const container = document.getElementById('revenue-pie-chart-container')
  if (!container) return
  const now = new Date()
  const timestamp =
    now.toISOString().split('T')[0] + '_' + now.toTimeString().split(' ')[0].replace(/:/g, '-')
  const filename = `RevenuePie_${timestamp}.pdf`

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
  fetchAvailableDates()
  fetchRevenueData()
})

// Refetch data when year or month changes
watch([selectedYear, selectedMonth], () => {
  fetchRevenueData()
})

// Watch for noDataMessage changes: if it becomes empty, render the chart after DOM update
watch(noDataMessage, async (val) => {
  if (!val) {
    await nextTick()
    renderChart()
  }
})
</script>

<template>
  <div class="chart-container">
    <transition name="filter-bar-fade">
      <div class="filter-controls" v-show="true">
        <label>
          Year:
          <select v-model="selectedYear">
            <option v-for="year in availableYears" :key="year" :value="year">
              {{ year }}
            </option>
          </select>
        </label>

        <label>
          Month:
          <select v-model="selectedMonth">
            <option v-for="monthNum in availableMonths" :key="monthNum" :value="monthNum">
              {{ months[monthNum - 1].label }}
            </option>
          </select>
        </label>
        <div class="export-controls">
          <button class="export-btn attractive-btn animated-btn" @click="exportRevenuePieChart">
            <span class="export-btn-icon">📤</span>
            <span>Export as PDF</span>
          </button>
        </div>
      </div>
    </transition>
    <div class="chart-wrapper" id="revenue-pie-chart-container">
      <template v-if="!noDataMessage">
        <canvas ref="chartRef"></canvas>
      </template>
      <template v-else>
        <div class="empty-chart-state">
          <span class="empty-icon">📉</span>
          <div class="empty-message">{{ noDataMessage }}</div>
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
.chart-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
  margin-bottom: 30px;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  color: #333;
}

.filter-controls {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  align-items: center;
  background: #fff;
  padding: 12px 20px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  justify-content: flex-start;
}
.filter-controls .export-controls {
  margin-left: auto;
  display: flex;
  align-items: center;
}

.filter-controls label {
  display: flex;
  flex-direction: column;
  font-weight: 600;
  font-size: 15px;
  color: #374151;
  min-width: 140px;
}

.filter-controls select {
  padding: 10px 36px 10px 14px;
  border-radius: 8px;
  border: 1.5px solid #d1d5db;
  background-color: #f9fafb;
  font-size: 15px;
  font-weight: 500;
  color: #222;
  appearance: none;
  outline: none;
  transition:
    border-color 0.18s,
    box-shadow 0.18s;
  box-shadow: 0 1px 4px rgba(59, 130, 246, 0.04);
  cursor: pointer;
  position: relative;
}
.filter-controls select:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.13);
  background-color: #f0f7ff;
}
.filter-controls select:hover {
  border-color: #60a5fa;
  background-color: #f3f6fa;
}
.filter-controls label {
  position: relative;
}
.filter-controls label:after {
  content: '\25BC';
  position: absolute;
  right: 18px;
  top: 38px;
  font-size: 13px;
  color: #888;
  pointer-events: none;
  transition:
    color 0.18s,
    transform 0.18s;
}
.filter-controls select:focus + .filter-controls label:after,
.filter-controls select:active + .filter-controls label:after {
  color: #3b82f6;
  transform: rotate(180deg);
}

/* Export PDF button UI from MonthlyExpensesChart.vue */
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
  outline: none;
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

.chart-wrapper {
  background: #f4fafe;
  border-radius: 18px;
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.05);
  padding: 20px;
  max-width: 95%;
  max-height: 75%;
  display: flex;
  justify-content: center;
  align-items: center;
}

#revenue-pie-chart-container {
  background: #ffffff;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.06);
  margin-top: 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

canvas {
  max-width: 100%;
  height: auto;
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

@media print {
  * {
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }

  body {
    font-family: Arial, sans-serif;
    font-size: 12px;
    color: #000;
  }

  .chart-container,
  .chart-wrapper,
  #revenue-pie-chart-container {
    background: white !important;
    color: black !important;
    box-shadow: none !important;
  }

  .export-controls {
    display: none;
  }
}
/* Smooth transition for filter-controls bar */
.filter-bar-fade-enter-active,
.filter-bar-fade-leave-active {
  transition:
    opacity 0.35s cubic-bezier(0.4, 0, 0.2, 1),
    transform 0.35s cubic-bezier(0.4, 0, 0.2, 1);
}
.filter-bar-fade-enter-from,
.filter-bar-fade-leave-to {
  opacity: 0;
  transform: translateY(-18px) scale(0.98);
}
.filter-bar-fade-enter-to,
.filter-bar-fade-leave-from {
  opacity: 1;
  transform: translateY(0) scale(1);
}
</style>
