<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Chart, registerables } from 'chart.js'
import axios from 'axios'

Chart.register(...registerables)

const monthlyChart = ref<HTMLCanvasElement | null>(null)
const currentYear = new Date().getFullYear()
const localhost = 'http://localhost:5000/'

interface MonthlyDataItem {
  month_name: string
  total_amount: number
}

const fetchChartData = async () => {
  try {
    const monthlyResponse = await axios.get(localhost + '/api/expenses/summary/monthly', {
      params: { year: currentYear },
    })
    console.log(' monthlyResponse.data', monthlyResponse.data)
    renderCharts(monthlyResponse.data)
  } catch (error) {
    console.error('Error fetching chart data:', error)
  }
}

const renderCharts = (monthlyData: MonthlyDataItem[]) => {
  if (!monthlyChart.value) return
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

onMounted(() => {
  fetchChartData()
})
</script>
<template>
  <div class="chart-container">
    <div class="chart-wrapper">
      <canvas ref="monthlyChart"></canvas>
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

canvas {
  width: 100% !important;
  max-width: 100%;
  height: 340px !important;
  display: block;
}

</style>
