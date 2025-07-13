<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { Chart, registerables } from 'chart.js'
import axios from 'axios'
import html2pdf from 'html2pdf.js'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
const companyId = userStore.company_id

Chart.register(...registerables)

const categoryChart = ref<HTMLCanvasElement | null>(null)
const currentYear = new Date().getFullYear()
const currentMonth = new Date().getMonth() + 1
const localhost = 'http://localhost:5000/'

interface CategoryDataItem {
  category: string
  total_amount: number
}

const availableDates = ref<{ year: number; month: number }[]>([])
const selectedYear = ref(currentYear)
const selectedMonth = ref(currentMonth)
const noDataMessage = ref('')

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

let pieChartInstance: Chart | null = null

const fetchAvailableDates = async () => {
  const res = await axios.get(localhost + 'api/expenses/available-months', {
    params: { company_id: companyId },
  })
  availableDates.value = res.data
}

const availableYears = computed(() =>
  [...new Set(availableDates.value.map((item) => item.year))].sort((a, b) => b - a),
)

const availableMonths = computed(() =>
  availableDates.value.filter((item) => item.year === selectedYear.value).map((item) => item.month),
)

const fetchChartData = async () => {
  try {
    // Category data for pie chart
    const categoryResponse = await axios.get(localhost + '/api/expenses/summary/category', {
      params: { year: selectedYear.value, month: selectedMonth.value, company_id: companyId },
    })
    const data = categoryResponse.data

    if (!data || data.length === 0) {
      noDataMessage.value =
        'No expense data available for this period. Please choose another month.'
      if (pieChartInstance) {
        pieChartInstance.destroy()
        pieChartInstance = null
      }
      return
    }

    // console.log('categoryResponse.data', categoryResponse.data)
    renderCharts(data)
  } catch (error) {
    console.error('Error fetching chart data:', error)
  }
}

const renderCharts = (categoryData: CategoryDataItem[]) => {
  if (!categoryChart.value) return

  if (pieChartInstance) {
    pieChartInstance.destroy()
  }
  const selectedMonthLabel = months[selectedMonth.value - 1]?.label || 'Unknown'
  // Pie Chart (By Category)
  pieChartInstance = new Chart(categoryChart.value, {
    type: 'pie',
    data: {
      labels: categoryData.map((item) => item.category),
      datasets: [
        {
          data: categoryData.map((item) => item.total_amount),
          backgroundColor: [
            '#FF6384',
            '#36A2EB',
            '#FFCE56',
            '#4BC0C0',
            '#9966FF',
            '#FF9F40',
            '#8AC926',
            '#1982C4',
          ],
        },
      ],
    },
    options: {
      responsive: true,
      plugins: {
        title: {
          display: true,
          text: `Expenses by Category (${selectedMonthLabel})`,
        },
      },
    },
  })
}

const exportExpensePieChart = () => {
  const container = document.getElementById('expense-pie-chart-container')
  if (!container) return

  const now = new Date()
  const timestamp =
    now.toISOString().split('T')[0] + '_' + now.toTimeString().split(' ')[0].replace(/:/g, '-')
  const filename = `ExpensePie_${timestamp}.pdf`

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
  fetchChartData()
})

watch([selectedYear, selectedMonth], fetchChartData)
</script>
<template>
  <div class="chart-container">
    <div class="filter-controls">
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
    </div>
    <div class="export-controls">
      <button @click="exportExpensePieChart">Export as PDF</button>
    </div>
    <div class="chart-wrapper" id="expense-pie-chart-container">
      <canvas ref="categoryChart"></canvas>
    </div>
    <div v-if="noDataMessage" class="no-data-message">
      {{ noDataMessage }}
    </div>
  </div>
</template>

<style scoped>
.chart-container {
  display: flex;
  gap: 22px;
  margin-bottom: 30px;
  flex-direction: column;
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

.filter-controls {
  display: flex;
  gap: 16px;
  align-items: center;
  justify-content: flex-start;
  margin: 16px 0;
  padding: 10px 16px;
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.filter-controls label {
  display: flex;
  flex-direction: column;
  font-weight: 500;
  font-size: 14px;
  color: #333;
}

.filter-controls select {
  padding: 6px 10px;
  border-radius: 6px;
  border: 1px solid #ccc;
  font-size: 14px;
  margin-top: 4px;
  min-width: 120px;
}

.no-data-message {
  padding: 16px;
  color: #555;
  background: #fff3cd;
  border: 1px solid #ffeeba;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 16px;
}

#expense-pie-chart-container {
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
  background-color: #f97316;
  color: white;
  cursor: pointer;
}

.export-controls button:hover {
  background-color: #ea580c;
}
</style>
