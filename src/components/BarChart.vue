<template>
  <Bar :data="data" :options="options" />
</template>

<script setup lang="ts">
import { Bar } from 'vue-chartjs'
import { Chart, registerables } from 'chart.js'
Chart.register(...registerables)

// props
interface Point { x: string; y: number }
interface Series { name: string; data: Point[] }

const props = defineProps<{
  series: Series[],
  categories: string[]
}>()

// build chartjs dataset object
const data = {
  labels: props.categories,
  datasets: props.series.map(s => ({
    label: s.name,
    data: s.data.map(pt => pt.y)
  }))
}

const options = { responsive: true }
</script>
