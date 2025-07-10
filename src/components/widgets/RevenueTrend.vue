<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { Chart, registerables } from 'chart.js'
Chart.register(...registerables)

interface RevenueItem {
  date: string
  amount: number
}

const props = defineProps<{ data: RevenueItem[] }>()
const canvasRef = ref<HTMLCanvasElement | null>(null)
let chart: Chart | null = null

const renderChart = () => {
  if (!canvasRef.value) return
  const monthly: Record<string, number> = {}
  props.data.forEach((d) => {
    const m = d.date.slice(0, 7)
    monthly[m] = (monthly[m] || 0) + d.amount
  })
  const labels = Object.keys(monthly).sort()
  const values = labels.map((l) => monthly[l])

  if (chart) chart.destroy()
  chart = new Chart(canvasRef.value, {
    type: 'bar',
    data: {
      labels,
      datasets: [
        {
          label: 'Revenue',
          data: values,
          backgroundColor: '#3b82f6',
        },
      ],
    },
    options: {
      responsive: true,
      plugins: { title: { display: true, text: 'Revenue Trend' } },
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
