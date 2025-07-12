<script setup lang="ts">
import { onMounted, ref } from 'vue'
import axios from 'axios'

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
  const res = await axios.get(localhost + 'api/users')
  staff.value = res.data as Staff[]
}

onMounted(fetchStaff)

const saveUser = async (user: Staff) => {
  await axios.post(localhost + 'api/updateUser', user)
  fetchStaff()
}
</script>

<template>
  <div>
    <h1>Manage Staff</h1>
    <table>
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
        <tr v-for="u in staff" :key="u.id">
          <td>{{ u.id }}</td>
          <td>{{ u.username }}</td>
          <td>
            <select v-model="u.role">
              <option value="admin">admin</option>
              <option value="staff">staff</option>
            </select>
          </td>
          <td>
            <select v-model="u.status">
              <option value="active">active</option>
              <option value="inactive">inactive</option>
            </select>
          </td>
          <td>{{ u.company_id }}</td>
          <td><button @click="saveUser(u)">Save</button></td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
table {
  width: 100%;
}
th,
td {
  padding: 0.5rem;
  text-align: left;
}
</style>
