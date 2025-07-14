<script setup lang="ts">
import { computed } from 'vue'
import { useUserStore } from '@/stores/user'
import { useRouter } from 'vue-router'

const userStore = useUserStore()
const isAdmin = computed(() => userStore.role === 'admin')
// console.log('userStore', userStore)
// console.log('isAdmin', isAdmin.value)

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
      <nav class="nav">
        <router-link to="/dashboard" class="nav-link" active-class="active"> Overview </router-link>
        <router-link to="/expenses" class="nav-link" active-class="active"> Expenses </router-link>
        <router-link to="/revenue" class="nav-link" active-class="active"> Revenue </router-link>
        <router-link to="/tax" class="nav-link" active-class="active"> Tax </router-link>
        <router-link v-if="isAdmin" to="/staff" class="nav-link" active-class="active">
          Manage Staff
        </router-link>
      </nav>
      <div class="bottom">
        <button class="btn-danger" @click="logout">Logout</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.sidebar {
  width: 250px;
  background: #ffffff;
  color: #1e1e1e;
  padding: 20px;
  height: 91vh;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  border-right: 1px solid #e0e0e0;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

.nav {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.nav-link {
  color: #2c3e50;
  text-decoration: none;
  padding: 10px 15px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  transition: all 0.3s ease;
  font-weight: 500;
}

.nav-link:hover {
  background-color: #f0f4ff;
}

.nav-link.active {
  background-color: #e9f1ff;
  color: #2c3e50;
  border: 1px solid #4d8aff;
  font-weight: 600;
}

.bottom {
  display: flex;
  justify-content: center;
  align-items: center;
  padding-top: 20px;
  padding-bottom: 20px;
  width: 100%;
}

.btn-danger {
  align-self: flex-start;
  padding: 10px 20px;
  background-color: #ff4d4f;
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: bold;
  cursor: pointer;
  transition: background 0.3s;
  margin-top: auto;
  align-items: center;
  width: 80%;
}

.btn-danger:hover {
  background-color: #ff2e31;
  transform: scale(1.1);
}
</style>
