<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { Chart, registerables } from 'chart.js'
Chart.register(...registerables)

interface Item {
  date: string
  amount: number
}

const props = defineProps<{ revenue: Item[]; expenses: Item[] }>()
const canvasRef = ref<HTMLCanvasElement | null>(null)
let chart: Chart | null = null

const renderChart = () => {
  if (!canvasRef.value) return
  const byMonth: Record<string, number> = {}
  props.revenue.forEach((r) => {
    const m = r.date.slice(0, 7)
    byMonth[m] = (byMonth[m] || 0) + r.amount
  })
  props.expenses.forEach((e) => {
    const m = e.date.slice(0, 7)
    byMonth[m] = (byMonth[m] || 0) - e.amount
  })
  const labels = Object.keys(byMonth).sort()
  const values = labels.map((l) => byMonth[l])

  if (chart) chart.destroy()
  chart = new Chart(canvasRef.value, {
    type: 'line',
    data: {
      labels,
      datasets: [
        {
          label: 'Net Profit',
          data: values,
          borderColor: '#10b981',
          fill: false,
        },
      ],
    },
    options: {
      responsive: true,
      plugins: { title: { display: true, text: 'Profit Trend' } },
    },
  })
}

watch(
  () => [props.revenue, props.expenses],
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
