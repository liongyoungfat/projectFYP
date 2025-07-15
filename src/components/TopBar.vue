<script setup lang="ts">
import { useUserStore } from '@/stores/user'
import { useRoute } from 'vue-router'

const route = useRoute()

const userStore = useUserStore()
const username = userStore.username || 'User'
console.log ('userstore',userStore.value)
</script>

<template>
  <div class="topbar">
    <h1 class="page-title">{{ route.meta.title || route.name }}</h1>
    <div class="right-section">
      <span class="username">{{ username }}</span>
      <i class="bi bi-person-circle icon"></i>
    </div>
  </div>
</template>

<style scoped>
.topbar {
  height: 60px;
  background-color: #ffffff;
  padding: 0 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.page-title {
  font-size: 20px;
  font-weight: 600;
  margin: 0;
}

.right-section {
  display: flex;
  align-items: center;
  gap: 10px;
}

.username {
  font-weight: 500;
  color: #2d3748;
}

.icon {
  font-size: 1.5rem;
  color: #2d3748;
}
</style>
