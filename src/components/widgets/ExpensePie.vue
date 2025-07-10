<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Chart, registerables } from 'chart.js'
import axios from 'axios'

Chart.register(...registerables)

const categoryChart = ref<HTMLCanvasElement | null>(null)
const currentYear = new Date().getFullYear()
const currentMonth = new Date().getMonth() + 1
const localhost = 'http://localhost:5000/'

interface CategoryDataItem {
  category: string
  total_amount: number
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
    console.log('categoryResponse.data', categoryResponse.data, monthlyResponse.data)
    renderCharts(categoryResponse.data)
  } catch (error) {
    console.error('Error fetching chart data:', error)
  }
}

const renderCharts = (categoryData: CategoryDataItem[]) => {
  if (!categoryChart.value) return

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
}

onMounted(() => {
  fetchChartData()
})
</script>
<template>
  <div class="chart-container">
    <div class="chart-wrapper">
      <canvas ref="categoryChart"></canvas>
    </div>
  </div>
</template>

<style scoped>
.chart-container {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 22px;
  margin-bottom: 30px;
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
</style>
