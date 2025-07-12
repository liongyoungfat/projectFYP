<script setup lang="ts">
import { computed } from 'vue'
import { useUserStore } from '@/stores/user'
import { useRouter } from 'vue-router'

const userStore = useUserStore()
const isAdmin = computed(() => userStore.role === 'admin')
console.log('userStore', userStore)
console.log('isAdmin', isAdmin.value)

const router = useRouter()

function logout() {
  localStorage.removeItem('authToken')
  router.push('/login')
}
</script>

<template>
  <div class="container">
    <!-- Sidebar -->
    <div class="sidebar">
      <h2 class="sidebar-title">Finance Dashboard</h2>
      <nav class="nav">
        <router-link to="/" class="nav-link" active-class="active"> Dashboard </router-link>
        <router-link to="/expenses" class="nav-link" active-class="active"> Expenses </router-link>
        <router-link to="/revenue" class="nav-link" active-class="active"> Revenue </router-link>
        <router-link to="/tax" class="nav-link" active-class="active"> Tax </router-link>
        <router-link v-if="isAdmin" to="/staff" class="nav-link" active-class="active">
          Manage Staff
        </router-link>
      </nav>
      <button @click="logout" class="btn btn-danger">Logout</button>
    </div>
  </div>
</template>

<style lang="css" scoped>
.sidebar {
  width: 250px;
  background: #2c3e50;
  color: white;
  padding: 20px;
  position: fixed;
  height: 100%;
}

.sidebar-title {
  margin-bottom: 30px;
  font-size: 1.5rem;
}

.nav {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.nav-link {
  color: #ecf0f1;
  text-decoration: none;
  padding: 10px;
  border-radius: 4px;
  transition: background 0.3s;
}

.nav-link:hover {
  background: #34495e;
}

.nav-link.active {
  background: #3498db;
}
</style>
