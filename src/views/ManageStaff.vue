<script setup lang="ts">
import { onMounted, ref } from 'vue'
import axios from 'axios'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
const companyId = userStore.company_id
const userId = userStore.user_id

interface Staff {
  id: number
  username: string
  role: string
  status: string
  company_id: number | null
}

const staff = ref<Staff[]>([])
const localhost = 'http://localhost:5000/'

const fetchStaff = async () => {
  const res = await axios.get(localhost + 'api/users', {
    params: { company_id: companyId },
  })
  staff.value = res.data as Staff[]
  console.log('staff', staff.value)
}

onMounted(fetchStaff)

const saveUser = async (user: Staff) => {
  await axios.post(localhost + 'api/updateUser', user)
  fetchStaff()
}
</script>

<template>
  <div class="container text-white bg-gray-800 p-4">
    <h1>Manage Staff</h1>
    <table class="text-white">
      <thead>
        <tr>
          <th>ID</th>
          <th>Username</th>
          <th>Role</th>
          <th>Status</th>
          <th>Company</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="user in staff" :key="user.id">
          <td>{{ user.id }}</td>
          <td>{{ user.username }}</td>
          <td>
            <select v-model="user.role">
              <option value="admin">admin</option>
              <option value="staff">staff</option>
            </select>
          </td>
          <td>
            <select v-model="user.status">
              <option value="active">active</option>
              <option value="inactive">inactive</option>
            </select>
          </td>
          <td>{{ user.company_id }}</td>
          <td><button @click="saveUser(user)">Save</button></td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
.container {
  color: white !important;
}
table {
  width: 100%;
}
th,
td {
  padding: 0.5rem;
  text-align: left;
}
</style>
