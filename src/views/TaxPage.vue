<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import axios from 'axios'
import html2pdf from 'html2pdf.js'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
const companyId = userStore.company_id || localStorage.getItem('userCompanyId')

const localhost = 'http://localhost:5000/'
const selectedYear = ref(new Date().getFullYear())

const expenses = ref<any[]>([])
const revenues = ref<any[]>([])

const years = computed(() => {
  const range: number[] = []
  const current = new Date().getFullYear()
  for (let y = current; y >= current - 5; y--) range.push(y)
  return range
})

const fetchData = async () => {
  try {
    const [expRes, revRes] = await Promise.all([
      axios.get(localhost + 'api/expenses', { params: { company_id: companyId } }),
      axios.get(localhost + 'api/revenues', { params: { company_id: companyId } }),
    ])
    expenses.value = expRes.data
    revenues.value = revRes.data
  } catch (e) {
    console.error('Failed to fetch data:', e)
  }
}

onMounted(fetchData)
watch(selectedYear, fetchData)

const filteredExpenses = computed(() =>
  expenses.value.filter((e) => new Date(e.dateTime).getFullYear() === selectedYear.value),
)

const filteredRevenues = computed(() =>
  revenues.value.filter((r) => new Date(r.dateTime).getFullYear() === selectedYear.value),
)

const totalExpenses = computed(() =>
  filteredExpenses.value.reduce((sum, e) => sum + Number(e.amount), 0),
)

const totalRevenues = computed(() =>
  filteredRevenues.value.reduce((sum, r) => sum + Number(r.amount), 0),
)

const profit = computed(() => totalRevenues.value - totalExpenses.value)

const band1 = computed(() => Math.min(Math.max(profit.value, 0), 150000))
const band2 = computed(() => Math.min(Math.max(profit.value - 150000, 0), 450000))
const band3 = computed(() => Math.max(profit.value - 600000, 0))

const taxBand1 = computed(() => band1.value * 0.15)
const taxBand2 = computed(() => band2.value * 0.17)
const taxBand3 = computed(() => band3.value * 0.24)
const totalTax = computed(() => taxBand1.value + taxBand2.value + taxBand3.value)

const exportTaxPDF = () => {
  const el = document.getElementById('tax-report-content')
  if (!el) return
  html2pdf()
    .from(el)
    .set({
      margin: 0.5,
      filename: `Tax_Summary_${selectedYear.value}.pdf`,
      image: { type: 'jpeg', quality: 0.98 },
      html2canvas: { scale: 2 },
      jsPDF: { unit: 'in', format: 'a4', orientation: 'portrait' },
      pagebreak: { mode: ['avoid-all', 'css', 'legacy'] },
    })
    .save()
}
</script>

<template>
  <div class="tax-container">
    <div class="page-header">
      <div class="title-section">
        <h1 class="page-title">💵💵 🧾💸 Tax Calculation</h1>
      </div>
      <div class="action-section no-print">
        <label class="year-select-label">
          Year:
          <select v-model="selectedYear" class="year-select">
            <option v-for="y in years" :key="y" :value="y">{{ y }}</option>
          </select>
        </label>
        <button @click="exportTaxPDF" class="export-btn">Export PDF</button>
      </div>
    </div>

    <div id="tax-report-content" class="table-container">
      <div class="summary">
        <p>Total Revenue: RM {{ totalRevenues.toFixed(2) }}</p>
        <p>Total Expenses: RM {{ totalExpenses.toFixed(2) }}</p>
        <p>Profit: RM {{ profit.toFixed(2) }}</p>
      </div>

      <table class="table">
        <thead>
          <tr>
            <th>Band</th>
            <th>Rate</th>
            <th>Amount (RM)</th>
            <th>Tax (RM)</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>First RM150,000</td>
            <td>15%</td>
            <td>{{ band1.toFixed(2) }}</td>
            <td>{{ taxBand1.toFixed(2) }}</td>
          </tr>
          <tr>
            <td>Next RM450,000</td>
            <td>17%</td>
            <td>{{ band2.toFixed(2) }}</td>
            <td>{{ taxBand2.toFixed(2) }}</td>
          </tr>
          <tr>
            <td>Above RM600,000</td>
            <td>24%</td>
            <td>{{ band3.toFixed(2) }}</td>
            <td>{{ taxBand3.toFixed(2) }}</td>
          </tr>
        </tbody>
        <tfoot>
          <tr>
            <th colspan="3">Total Tax</th>
            <th>{{ totalTax.toFixed(2) }}</th>
          </tr>
        </tfoot>
      </table>

      <p class="note">Rates may change; always check official LHDN site.</p>
    </div>
  </div>
</template>

<style scoped>
.tax-container {
  padding: 20px;
  color: #2c3e50;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #f9fafb;
  padding: 1rem 1.5rem;
  border-radius: 8px;
  margin-bottom: 1rem;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
}

.title-section {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.title-icon {
  width: 28px;
  height: 28px;
}

.page-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: #1e293b;
}

.action-section {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.year-select-label {
  font-size: 0.95rem;
  color: #374151;
}

.year-select {
  margin-left: 0.5rem;
  padding: 0.4rem 0.6rem;
  border: 1px solid #cbd5e1;
  border-radius: 5px;
  background: white;
  font-size: 0.95rem;
}

.export-btn {
  background: #2563eb;
  color: white;
  padding: 0.45rem 1rem;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  font-weight: 500;
  transition: background 0.2s ease;
}

.export-btn:hover {
  background: #1d4ed8;
}

.year-label {
  font-weight: 600;
  color: #34495e;
}

.year-select {
  margin-left: 10px;
  padding: 8px 12px;
  border: 1px solid #ccc;
  border-radius: 4px;
}

.new-expense-btn {
  background: #3498db;
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 4px;
  cursor: pointer;
  transition: background 0.3s;
}

.new-expense-btn:hover {
  background: #2980b9;
}

.table-container {
  overflow-x: auto;
  background: white;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.summary {
  margin-bottom: 20px;
  font-weight: 500;
  color: #2c3e50;
}

.table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
}

.table th,
.table td {
  padding: 12px 16px;
  border-bottom: 1px solid #eee;
}

.table th {
  background-color: #f5f5f5;
  font-weight: 600;
}

.note {
  margin-top: 1rem;
  font-size: 0.9rem;
  color: #7f8c8d;
}
</style>
