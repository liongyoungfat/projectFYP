<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Chart, registerables } from 'chart.js'
import axios from 'axios'
import html2pdf from 'html2pdf.js'
import RevenueTrend from '@/components/widgets/RevenueTrend.vue'
import ExpensePie from '@/components/widgets/ExpensePie.vue'
import ProfitTrend from '@/components/widgets/ProfitTrend.vue'
import MonthlyExpensesChart from '@/components/widgets/MonthlyExpensesChart.vue'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
const companyId = userStore.company_id

Chart.register(...registerables)

const showForecastModal = ref(false)
const localhost = 'http://localhost:5000/'

const forecastResponse = ref<ForecastReport | null>(null)
const revenueData = ref<RevenueItem[]>([])
const expensesData = ref<ExpenseItem[]>([])

const isGenerating = ref(false)
const showWidgetDropdown = ref(false)

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
  monthlyExpensesChart: true,
})

const totalRevenue = computed(() => revenueData.value.reduce((sum, r) => sum + Number(r.amount), 0))
const totalExpenses = computed(() =>
  expensesData.value.reduce((sum, e) => sum + Number(e.amount), 0),
)
const netProfit = computed(() => totalRevenue.value - totalExpenses.value)

const fetchRevenueData = async () => {
  try {
    const res = await axios.get(localhost + 'api/revenues', { params: { company_id: companyId } })
    revenueData.value = res.data
    // console.log('Fetched revenue data:', revenueData.value)
  } catch (err) {
    console.error('Failed to fetch revenue data:', err)
  }
}

const fetchExpenseData = async () => {
  try {
    const res = await axios.get(localhost + 'api/expenses', { params: { company_id: companyId } })
    expensesData.value = res.data
  } catch (err) {
    console.error('Failed to fetch expense data:', err)
  }
}

const generateFinancialReport = async () => {
  try {
    isGenerating.value = true
    const fr = await axios.post(localhost + '/api/ai/generate/forecast')
    // console.log('fr', fr.data)
    forecastResponse.value = fr.data
    // console.log('fr.value', forecastResponse.value['executive_summary'])
    showForecastModal.value = true
  } catch (err) {
    console.error('Failed to generate report', err)
  } finally {
    isGenerating.value = false
  }
}

const exportForecastPDF = () => {
  const report = document.getElementById('forecast-report-content')
  if (!report) return

  // Wait until DOM/render finishes
  setTimeout(() => {
    html2pdf()
      .from(report)
      .set({
        margin: 0.5,
        filename: 'Financial_Forecast_Report.pdf',
        image: { type: 'jpeg', quality: 0.98 },
        html2canvas: { scale: 2, useCORS: true }, // enable CORS for external images if any
        jsPDF: { unit: 'in', format: 'a4', orientation: 'portrait' },
        pagebreak: { mode: ['avoid-all', 'css', 'legacy'] },
      })
      .save()
  }, 200) // small delay allows Vue to update DOM
}

onMounted(() => {
  fetchRevenueData()
  fetchExpenseData()
})
</script>

<template>
  <div class="dashboard-container">
    <div class="chart-header">
      <div class="chart-header-left">📊 Financial Dashboard</div>
      <div class="chart-header-right">
        <div class="toggle-dropdown">
          <button @click="showWidgetDropdown = !showWidgetDropdown">
            Select Widgets {{ showWidgetDropdown ? '▴' : '▾' }}
          </button>
          <div v-if="showWidgetDropdown" class="dropdown-menu">
            <label> <input type="checkbox" v-model="widgetVisible.revenue" /> Revenue Trend </label>
            <label> <input type="checkbox" v-model="widgetVisible.profit" /> Profit Trend </label>
            <label>
              <input type="checkbox" v-model="widgetVisible.monthlyExpensesChart" /> Monthly
              Expenses
            </label>
            <label> <input type="checkbox" v-model="widgetVisible.expenses" /> Expense Pie </label>
          </div>
        </div>
        <button @click="generateFinancialReport" class="report-btn" :disabled="isGenerating">
          <i class="fas fa-file-alt"></i>
          <span v-if="isGenerating" class="jumping-text">Generating... Forecasting takes time</span>
          <span v-else>Generate Financial Report</span>
        </button>
      </div>
    </div>
    <div class="summary-row">
      <div class="summary-card">
        <h4>Total Revenue</h4>
        <p class="summary-green">{{ totalRevenue.toFixed(2) }}</p>
      </div>
      <div class="summary-card">
        <h4>Total Expenses</h4>
        <p class="summary-red">{{ totalExpenses.toFixed(2) }}</p>
      </div>
      <div class="summary-card">
        <h4>Net Profit</h4>
        <p :class="netProfit >= 0 ? 'summary-green' : 'summary-red'">{{ netProfit.toFixed(2) }}</p>
      </div>
    </div>
    <div v-if="showForecastModal" class="modal-overlay">
      <div class="forecast-modal">
        <div class="forecast-content" id="forecast-report-content">
          <h3>Financial Forecast Report</h3>
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
    <div class="full-width-widget">
      <div class="widgets">
        <div class="widgets">
          <RevenueTrend v-if="widgetVisible.revenue" />
          <ProfitTrend v-if="widgetVisible.profit" />
          <MonthlyExpensesChart v-if="widgetVisible.monthlyExpensesChart" />
          <ExpensePie v-if="widgetVisible.expenses" />
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.dashboard-container {
  height: 91vh;
  padding: 28px 16px 32px 16px;
  overflow-y: scroll;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: #f7f9fb;
  padding: 16px 20px;
  border-radius: 10px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.06);
  margin-bottom: 24px;
  flex-wrap: wrap;
  gap: 12px;
}

.chart-header-left {
  font-size: 20px;
  font-weight: 600;
  color: #2c3e50;
  display: flex;
  align-items: center;
}

.chart-header-right {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-left: auto;
}

/* Report Button */
.report-btn {
  padding: 10px 18px;
  background-color: #3498db;
  color: #fff;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition:
    background-color 0.2s ease,
    transform 0.5s ease;
}

.report-btn:hover {
  background-color: #2980b9;
  transform: scale(1.05);
}

.report-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.toggle-dropdown {
  position: relative;
  display: inline-block;
  transition: background-color 0.2s ease transform 0.5s ease;
}

.toggle-dropdown > button {
  padding: 8px 14px;
  background-color: #d1dfe6;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: background-color 0.2s ease transform 0.2s ease;
}

.toggle-dropdown > button:hover {
  background-color: #b7c9d4;
  transform: scale(1.1);
}

.toggle-dropdown > .dropdown-menu {
  position: absolute;
  top: 110%;
  left: 0;
  background-color: #ffffff;
  border: 1px solid #ccc;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  padding: 10px 14px;
  z-index: 99;
  min-width: 200px;
}

.dropdown-menu label {
  display: block;
  padding: 6px 0;
  cursor: pointer;
  font-size: 14px;
}

.dropdown-menu label:hover {
  background-color: #f4f7fb;
  border-radius: 4px;
  padding-left: 4px;
}

h2 {
  font-size: 2rem;
  font-weight: 700;
  margin-bottom: 0;
}

.summary-row {
  display: flex;
  gap: 20px;
  margin: 1em 0;
  flex-wrap: wrap;
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

.full-width-widget {
  grid-column: 1 / -1; /* take full row in grid */
  display: block;
  width: 100%;
}

.full-width-widget > * {
  width: 100%;
}

.widgets {
  gap: 32px;
  margin-bottom: 36px;
  padding: 10px 0;
}

.widgets > * {
  background: linear-gradient(to bottom, #ffffff, #f4fafe);
  border-radius: 16px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
  padding: 20px 24px;
  transition:
    transform 0.2s ease,
    box-shadow 0.2s ease;
  overflow: hidden;
}

.widgets > *:hover {
  transform: translateY(-4px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.1);
}

.widget canvas,
.widget > canvas {
  width: 100% !important;
  max-width: 100%;
  margin: 0 auto;
}

.dashboard-chart {
  background: #f4fafe;
  border-radius: 18px;
  box-shadow: 0 4px 14px #0001;
  padding: 20px 30px 16px 30px;
  margin-bottom: 30px;
}

.close-btn {
  background: #4a6fa5;
  color: white;
  padding: 10px 20px;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  float: right;
  transition:
    background-color 0.2s ease,
    transform 0.5s ease;
}

.close-btn:hover {
  background: #557fbe;
  transform: scale(1.05);
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
  margin-bottom: 20px;
}

.forecast-modal h3 {
  color: #1565c0;
  font-weight: 700;
  font-size: 1.75rem;
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

.export-btn {
  background-color: #2563eb;
  padding: 10px 20px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  color: white;
  transition:
    background-color 0.2s ease,
    transform 0.5s ease;
}

.export-btn:hover {
  background-color: #1d4ed8;
  transform: scale(1.05);
}

@media print {
  .no-print {
    display: none !important;
  }

  .forecast-modal {
    box-shadow: none !important;
    background: white !important;
    padding: 0 !important;
  }

  body {
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
    color: #000;
    font-family: Arial, sans-serif;
  }
}

/* For html2pdf.js to honor it, you can also use: */
.no-pdf {
  display: none !important;
}

/* Summary Card Colors */
.summary-green {
  color: #2ecc71;
  font-weight: bold;
}
.summary-red {
  color: #e74c3c;
  font-weight: bold;
}
</style>

@keyframes jump { 0%, 100% { transform: translateY(0); } 20% { transform: translateY(-8px); } 40% {
transform: translateY(0); } 60% { transform: translateY(-6px); } 80% { transform: translateY(0); } }
.jumping-text { display: inline-block; animation: jump 1.2s infinite; font-weight: 600;
letter-spacing: 0.5px; }
