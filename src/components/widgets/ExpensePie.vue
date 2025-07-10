<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { Chart, registerables } from 'chart.js'
Chart.register(...registerables)

interface ExpenseItem {
  date: string
  category: string
  amount: number
}

const props = defineProps<{ data: ExpenseItem[] }>()
const canvasRef = ref<HTMLCanvasElement | null>(null)
let chart: Chart | null = null

const renderChart = () => {
  if (!canvasRef.value) return
  const byCat: Record<string, number> = {}
  props.data.forEach((d) => {
    byCat[d.category] = (byCat[d.category] || 0) + d.amount
  })
  const labels = Object.keys(byCat)
  const values = labels.map((l) => byCat[l])

  if (chart) chart.destroy()
  chart = new Chart(canvasRef.value, {
    type: 'pie',
    data: {
      labels,
      datasets: [
        {
          data: values,
          backgroundColor: ['#f87171', '#60a5fa', '#34d399', '#fbbf24'],
        },
      ],
    },
    options: {
      responsive: true,
      plugins: { title: { display: true, text: 'Expenses by Category' } },
    },
  })
}

watch(
  () => props.data,
  () => renderChart(),
  { deep: true, immediate: true },
)

onMounted(renderChart)
</script>
<template>
  <div class="widget">
    <canvas ref="canvasRef"></canvas>
  </div>
</template>

<style scoped>
.widget {
  padding: 1rem;
}
</style>
