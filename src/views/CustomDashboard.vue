<script setup lang="ts">
import { ref, computed } from 'vue'
import RevenueTrend from '@/components/widgets/RevenueTrend.vue'
import ExpensePie from '@/components/widgets/ExpensePie.vue'
import ProfitTrend from '@/components/widgets/ProfitTrend.vue'

interface Item {
  date: string
  category: string
  branch: string
  amount: number
}

const revenueData = ref<Item[]>([
  { date: '2024-05-02', category: 'Service', branch: 'Main', amount: 1200 },
  { date: '2024-05-15', category: 'Sales', branch: 'East', amount: 800 },
  { date: '2024-06-05', category: 'Service', branch: 'West', amount: 950 },
  { date: '2024-06-21', category: 'Sales', branch: 'Main', amount: 1100 },
  { date: '2024-07-03', category: 'Service', branch: 'East', amount: 700 },
])

const expenseData = ref<Item[]>([
  { date: '2024-05-03', category: 'Meals', branch: 'Main', amount: 50 },
  { date: '2024-05-20', category: 'Travel', branch: 'East', amount: 120 },
  { date: '2024-06-08', category: 'Office', branch: 'West', amount: 200 },
  { date: '2024-06-25', category: 'Meals', branch: 'Main', amount: 90 },
  { date: '2024-07-05', category: 'Travel', branch: 'East', amount: 150 },
])

const categories = ['Meals', 'Travel', 'Office', 'Sales', 'Service']
const branches = ['Main', 'East', 'West']

const startDate = ref('')
const endDate = ref('')
const selectedCategory = ref('')
const selectedBranch = ref('')

const widgetVisible = ref({
  revenue: true,
  expenses: true,
  profit: true,
})

const showWidgetDropdown = ref(false)

const filterItem = (item: Item) => {
  if (startDate.value && new Date(item.date) < new Date(startDate.value)) return false
  if (endDate.value && new Date(item.date) > new Date(endDate.value)) return false
  if (selectedCategory.value && item.category !== selectedCategory.value) return false
  if (selectedBranch.value && item.branch !== selectedBranch.value) return false
  return true
}

const filteredRevenue = computed(() => revenueData.value.filter(filterItem))
const filteredExpenses = computed(() => expenseData.value.filter(filterItem))
</script>

<template>
  <div class="dashboard">
    <div class="settings-bar">
      <div class="filters">
        <input type="date" v-model="startDate" />
        <input type="date" v-model="endDate" />
        <select v-model="selectedCategory">
          <option value="">All Categories</option>
          <option v-for="c in categories" :key="c" :value="c">{{ c }}</option>
        </select>
        <select v-model="selectedBranch">
          <option value="">All Branches</option>
          <option v-for="b in branches" :key="b" :value="b">{{ b }}</option>
        </select>
      </div>
      <div class="toggle-dropdown">
        <button @click="showWidgetDropdown = !showWidgetDropdown">
          Select Widgets ▾
        </button>
        <div v-if="showWidgetDropdown" class="dropdown-menu">
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
      </div>
    </div>

    <div class="widgets">
      <RevenueTrend v-if="widgetVisible.revenue" :data="filteredRevenue" />
      <ExpensePie v-if="widgetVisible.expenses" :data="filteredExpenses" />
      <ProfitTrend
        v-if="widgetVisible.profit"
        :revenue="filteredRevenue"
        :expenses="filteredExpenses"
      />
    </div>
  </div>
</template>

<style scoped>
.dashboard {
  padding: 1rem;
}
.settings-bar {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
  background: #f4f4f5;
  padding: 0.5rem 1rem;
  margin-bottom: 1rem;
  border-radius: 6px;
}
.filters > * {
  margin-right: 0.5rem;
}
.toggle-dropdown {
  position: relative;
}
.toggle-dropdown button {
  background: #e5e7eb;
  border: none;
  padding: 0.5rem 0.75rem;
  border-radius: 4px;
  cursor: pointer;
}
.dropdown-menu {
  position: absolute;
  left: 0;
  top: 100%;
  margin-top: 0.25rem;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 4px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
  padding: 0.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  z-index: 10;
}
.dropdown-menu label {
  display: flex;
  align-items: center;
  gap: 0.25rem;
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
</style>
