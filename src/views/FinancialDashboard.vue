<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { Bar } from 'vue-chartjs'
import { Chart, registerables } from 'chart.js'
import axios from 'axios'
import html2pdf from 'html2pdf.js'

Chart.register(...registerables)

const categoryChart = ref<HTMLCanvasElement | null>(null)
const monthlyChart = ref<HTMLCanvasElement | null>(null)
const revenueChart = ref<HTMLCanvasElement | null>(null)
const profitChart = ref<HTMLCanvasElement | null>(null)
const currentYear = new Date().getFullYear()
const currentMonth = new Date().getMonth() + 1
const showForecastModal = ref(false)
const localhost = 'http://localhost:5000/'

const forecastResponse = ref<ForecastReport | null>(null)
const revenueData = ref<RevenueItem[]>([])
const expensesData = ref<ExpenseItem[]>([])

interface CategoryDataItem {
  category: string
  total_amount: number
}

interface MonthlyDataItem {
  month_name: string
  total_amount: number
}

interface ForecastReport {
  executive_summary: string
  category_analysis: Record<string, string>
  forecast_table: { headers: string[]; rows: any[][] }
  insights: string[]
  visualization_suggestions: string[]
}

interface RevenueItem {
  amount: number
  dateTime: string
}

interface ExpenseItem {
  amount: number
  dateTime: string
}

const widgetVisible = ref({
  revenue: true,
  expenses: true,
  profit: true,
})

const totalRevenue = computed(() => revenueData.value.reduce((sum, r) => sum + Number(r.amount), 0))
const totalExpenses = computed(() =>
  expensesData.value.reduce((sum, e) => sum + Number(e.amount), 0),
)
const netProfit = computed(() => totalRevenue.value - totalExpenses.value)

const fetchExpenseData = async () => {
  try {
    const res = await axios.get(localhost + 'api/expenses')
    expensesData.value = res.data
    renderProfitChart()
  } catch (err) {
    console.error('Failed to fetch expense data:', err)
  }
}

const renderProfitChart = () => {
  if (!profitChart.value || revenueData.value.length === 0 || expensesData.value.length === 0)
    return

  const revenueByMonth: Record<string, number> = {}
  revenueData.value.forEach((item) => {
    if (!item.dateTime) return
    const dateObj = new Date(item.dateTime)
    const m = `${dateObj.getFullYear()}-${String(dateObj.getMonth() + 1).padStart(2, '0')}`
    revenueByMonth[m] = (revenueByMonth[m] || 0) + Number(item.amount)
  })
  console.log('rBM', revenueByMonth)
  const expenseByMonth: Record<string, number> = {}
  expensesData.value.forEach((item) => {
    if (!item.dateTime) return
    const dateObj = new Date(item.dateTime)
    const m = `${dateObj.getFullYear()}-${String(dateObj.getMonth() + 1).padStart(2, '0')}`
    expenseByMonth[m] = (expenseByMonth[m] || 0) + Number(item.amount)
  })
  console.log('eBM', expenseByMonth)

  const months = Array.from(
    new Set([...Object.keys(revenueByMonth), ...Object.keys(expenseByMonth)]),
  ).sort()
  const profitValues = months.map((m) => (revenueByMonth[m] || 0) - (expenseByMonth[m] || 0))
  const monthsLabels = months.map((m) => getMonthLabel(m))

  new Chart(profitChart.value, {
    type: 'line',
    data: {
      labels: monthsLabels,
      datasets: [
        {
          label: 'Net Profit (RM)',
          data: profitValues,
          borderColor: '#ff6384',
          fill: false,
        },
      ],
    },
    options: {
      responsive: true,
      plugins: {
        title: { display: true, text: 'Net Profit Trend' },
      },
      scales: {
        y: {
          beginAtZero: true,
          title: { display: true, text: 'Amount (RM)' },
        },
        x: {
          title: { display: true, text: 'Month' },
        },
      },
    },
  })
}

function getMonthLabel(ym: string) {
  if (!ym) return ''
  return new Date(ym + '-01').toLocaleString('default', { month: 'short', year: '2-digit' })
}

const fetchRevenueData = async () => {
  try {
    const res = await axios.get(localhost + '/api/revenues')
    revenueData.value = res.data
    console.log('revenueData.value', revenueData.value)
    renderRevenueChart()
    renderProfitChart()
  } catch (err) {
    console.error('Failed to fetch revenue data:', err)
  }
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

const fetchChartData = async () => {
  try {
    // Category data for pie chart
    const categoryResponse = await axios.get(localhost + '/api/expenses/summary/category', {
      params: { year: currentYear, month: currentMonth },
    })

    // Monthly data for bar chart
    const monthlyResponse = await axios.get(localhost + '/api/expenses/summary/monthly', {
      params: { year: currentYear },
    })
    console.log(
      'categoryResponse.data, monthlyResponse.data',
      categoryResponse.data,
      monthlyResponse.data,
    )
    renderCharts(categoryResponse.data, monthlyResponse.data)
  } catch (error) {
    console.error('Error fetching chart data:', error)
  }
}

const renderCharts = (categoryData: CategoryDataItem[], monthlyData: MonthlyDataItem[]) => {
  if (!categoryChart.value || !monthlyChart.value) return

  // Pie Chart (By Category)
  new Chart(categoryChart.value, {
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
          text: `Expenses by Category (${new Date().toLocaleString('default', { month: 'long' })})`,
        },
      },
    },
  })

  // Bar Chart (Monthly Trends)
  new Chart(monthlyChart.value, {
    type: 'bar',
    data: {
      labels: monthlyData.map((item) => item.month_name),
      datasets: [
        {
          label: 'Monthly Expenses',
          data: monthlyData.map((item) => item.total_amount),
          backgroundColor: '#4BC0C0',
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
          text: `Monthly Expenses Trend (${currentYear})`,
        },
      },
    },
  })
}

const generateFinancialReport = async () => {
  try {
    const fr = await axios.post(localhost + '/api/ai/generate/forecast')
    console.log('fr', fr.data)
    forecastResponse.value = fr.data
    console.log('fr.value', forecastResponse.value['executive_summary'])
    showForecastModal.value = true
  } catch (err) {
    console.error('Failed to generate report', err)
  }
}

const exportForecastPDF = () => {
  const report = document.getElementById('forecast-report-content')
  if (!report) return
  html2pdf()
    .from(report)
    .set({
      margin: 0.5,
      filename: 'Financial_Forecast_Report.pdf',
      image: { type: 'jpeg', quality: 0.98 },
      html2canvas: { scale: 2 },
      jsPDF: { unit: 'in', format: 'a4', orientation: 'portrait' },
      pagebreak: { mode: ['avoid-all', 'css', 'legacy'] },
    })
    .save()
}

onMounted(() => {
  fetchChartData()
  fetchRevenueData()
  fetchExpenseData()
})
</script>

<template>
  <div class="dashboard-container">
    <div class="toggles">
      <label>
        <input type="checkbox" v-model="widgetVisible.revenue" /> Revenue Trend
      </label>
      <label>
        <input type="checkbox" v-model="widgetVisible.expenses" /> Expense Pie
      </label>
      <label>
        <input type="checkbox" v-model="widgetVisible.profit" /> Profit Trend
      </label>
    </div>

    <div class="chart-header">
      <h2>Financial Dashboard</h2>
      <button @click="generateFinancialReport" class="report-btn">
        <i class="fas fa-file-alt"></i> Generate Financial Report
      </button>
    </div>
    <div class="summary-row">
      <div class="summary-card">
        <h4>Total Revenue</h4>
        <p>{{ totalRevenue.toFixed(2) }}</p>
      </div>
      <div class="summary-card">
        <h4>Total Expenses</h4>
        <p>{{ totalExpenses.toFixed(2) }}</p>
      </div>
      <div class="summary-card">
        <h4>Net Profit</h4>
        <p>{{ netProfit.toFixed(2) }}</p>
      </div>
    </div>
    <div class="widgets">
      <div v-if="widgetVisible.revenue"/>
    </div>
    <div class="dashboard-chart mb-3">
      <h3>Revenue Over Time</h3>
      <canvas ref="revenueChart" height="90"></canvas>
    </div>
    <div class="dashboard-chart mb-3">
      <h3>Net Profit Trend</h3>
      <canvas ref="profitChart" height="90"></canvas>
    </div>
    <div class="chart-container">
      <div class="chart-wrapper">
        <canvas ref="categoryChart"></canvas>
      </div>
      <div class="chart-wrapper">
        <canvas ref="monthlyChart"></canvas>
      </div>
    </div>
    <div v-if="showForecastModal" class="modal-overlay">
      <div class="forecast-modal">
        <h3>Financial Forecast Report</h3>
        <div class="forecast-content" id="forecast-report-content">
          <div v-if="forecastResponse">
            <h4>Executive Summary</h4>
            <p>{{ forecastResponse.executive_summary }}</p>
            <div class="pdf-page-break"></div>
            <h4>Category Analysis</h4>
            <ul>
              <li v-for="(desc, cat) in forecastResponse.category_analysis" :key="cat">
                <strong>{{ cat }}</strong
                >: {{ desc }}
              </li>
            </ul>

            <div class="pdf-page-break"></div>
            <h4>Forecast Table</h4>
            <table>
              <thead>
                <tr>
                  <th v-for="header in forecastResponse.forecast_table.headers" :key="header">
                    {{ header }}
                  </th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in forecastResponse.forecast_table.rows" :key="row[0]">
                  <td v-for="cell in row" :key="cell">{{ cell }}</td>
                </tr>
              </tbody>
            </table>

            <div class="pdf-page-break"></div>
            <h4>Insights</h4>
            <ul>
              <li v-for="insight in forecastResponse.insights" :key="insight">{{ insight }}</li>
            </ul>

            <div class="pdf-page-break"></div>
            <h4>Visualization Suggestions</h4>
            <ul>
              <li
                v-for="suggestion in forecastResponse.visualization_suggestions"
                :key="suggestion"
              >
                {{ suggestion }}
              </li>
            </ul>
          </div>
        </div>
        <button @click="exportForecastPDF" class="export-btn no-print">Export PDF</button>
        <button @click="showForecastModal = false" class="close-btn no-print">Close</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.summary-row {
  display: flex;
  gap: 20px;
  margin: 1em 0;
}

.summary-card {
  flex: 1;
  background: #fff;
  color: #333;
  padding: 1em;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  text-align: center;
}

.summary-card h4 {
  margin-bottom: 0.5em;
  font-weight: 600;
}

.widgets {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
}
.widgets > * {
  flex: 1 1 300px;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
}

.chart-container {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
}

.chart-wrapper {
  flex: 1;
  min-width: 300px;
  height: 400px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  padding: 20px;
}

.dashboard-chart {
  margin: 1.5em 0;
  background: #f4fafe;
  padding: 1em 2em;
  border-radius: 14px;
  box-shadow: 0 4px 18px #0001;
}

/* Report Button */
.report-btn {
  background: linear-gradient(to right, #4a6fa5, #2c3e50);
  color: white;
  padding: 12px 25px;
  border: none;
  border-radius: 30px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 10px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
}

.report-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
}

.close-btn {
  background: #4a6fa5;
  color: white;
  padding: 10px 20px;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  float: right;
}
/* Place in your global stylesheet */
.forecast-modal {
  background: #fff;
  color: #222;
  padding: 2rem;
  border-radius: 24px;
  box-shadow: 0 6px 32px rgba(0, 0, 0, 0.12);
  width: 100%;
  max-width: 100%;
  margin: 3rem auto;
  font-family: 'Segoe UI', Arial, sans-serif;
}

#forecast-report-content h4 {
  color: #1565c0;
  margin-top: 1.2rem;
  margin-bottom: 0.5rem;
  border-bottom: 1px solid #e0e0e0;
  padding-bottom: 0.25rem;
}

#forecast-report-content ul,
#forecast-report-content p {
  color: #333;
  font-size: 1rem;
  line-height: 1.5;
}

#forecast-report-content table {
  width: 100%;
  border-collapse: collapse;
  margin: 24px 0;
  font-size: 16px;
  background: #fafafa;
}

#forecast-report-content th,
#forecast-report-content td {
  border: 1px solid #e0e0e0;
  padding: 0.5rem 0.75rem;
  text-align: center;
}

#forecast-report-content,
#forecast-report-content p,
#forecast-report-content li {
  text-align: justify;
}

#forecast-report-content th {
  background: #e3f2fd;
  color: #222;
  font-weight: 600;
}

.forecast-report-content td {
  color: #222;
  border: 1px solid #e0e0e0;
  padding: 0.5rem 0.75rem;
  text-align: left;
}

#forecast-report-content {
  overflow-x: visible !important;
}

.forecast-modal h3 {
  color: #1565c0;
  font-weight: 700;
  margin-bottom: 1.2rem;
}

.forecast-modal h4 {
  color: #222;
  margin-top: 1.5rem;
  font-size: 1.2rem;
  border-bottom: 1px solid #e0e0e0;
  padding-bottom: 0.4rem;
}

.forecast-modal ul,
.forecast-modal p {
  color: #333;
  font-size: 1rem;
  line-height: 1.5;
}

.forecast-modal table {
  width: 100%;
  border-collapse: collapse;
  margin: 1rem 0;
  background: #fafafa;
}

.forecast-modal th,
.forecast-modal td {
  border: 1px solid #e0e0e0;
  padding: 0.5rem 0.75rem;
  text-align: left;
}

.forecast-modal th {
  background: #e3f2fd;
}

.pdf-page-break {
  display: block;
  height: 0;
  page-break-before: always;
  break-before: page;
}

/* Hide .no-print elements in print/export */
@media print {
  .no-print {
    display: none !important;
  }
}

/* For html2pdf.js to honor it, you can also use: */
.no-pdf {
  display: none !important;
}
</style>
