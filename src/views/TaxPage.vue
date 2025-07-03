<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import axios from 'axios'

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
      axios.get(localhost + 'api/expenses'),
      axios.get(localhost + 'api/revenues'),
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
  expenses.value.filter(
    (e) => new Date(e.dateTime).getFullYear() === selectedYear.value,
  ),
)

const filteredRevenues = computed(() =>
  revenues.value.filter(
    (r) => new Date(r.dateTime).getFullYear() === selectedYear.value,
  ),
)

const totalExpenses = computed(() =>
  filteredExpenses.value.reduce((sum, e) => sum + Number(e.amount), 0),
)

const totalRevenues = computed(() =>
  filteredRevenues.value.reduce((sum, r) => sum + Number(r.amount), 0),
)

const profit = computed(() => totalRevenues.value - totalExpenses.value)

const band1 = computed(() => Math.min(Math.max(profit.value, 0), 150000))
const band2 = computed(() =>
  Math.min(Math.max(profit.value - 150000, 0), 450000),
)
const band3 = computed(() => Math.max(profit.value - 600000, 0))

const taxBand1 = computed(() => band1.value * 0.15)
const taxBand2 = computed(() => band2.value * 0.17)
const taxBand3 = computed(() => band3.value * 0.24)
const totalTax = computed(
  () => taxBand1.value + taxBand2.value + taxBand3.value,
)
</script>

<template>
  <div class="tax-page">
    <h1>Tax Calculation</h1>
    <label>
      Year:
      <select v-model="selectedYear">
        <option v-for="y in years" :key="y" :value="y">{{ y }}</option>
      </select>
    </label>

    <div class="summary">
      <p>Total Revenue: RM {{ totalRevenues.toFixed(2) }}</p>
      <p>Total Expenses: RM {{ totalExpenses.toFixed(2) }}</p>
      <p>Profit: RM {{ profit.toFixed(2) }}</p>
    </div>

    <table class="tax-breakdown">
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
    <p class="note">
      Rates may change; always check official LHDN site.
    </p>
  </div>
</template>

<style scoped>
.tax-page {
  color: #ecf0f1;
}
.summary {
  margin: 1rem 0;
}
.tax-breakdown {
  width: 100%;
  border-collapse: collapse;
  background: #fafafa;
  color: #333;
}
.tax-breakdown th,
.tax-breakdown td {
  border: 1px solid #e0e0e0;
  padding: 0.5rem 0.75rem;
  text-align: left;
}
.tax-breakdown th {
  background: #e3f2fd;
}
.note {
  margin-top: 1rem;
  font-size: 0.9rem;
  color: #ccc;
}
</style>
