<script setup lang="ts">
import { onMounted, ref } from 'vue'
import axios from 'axios'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
const companyId = userStore.company_id

interface Staff {
  id: number
  username: string
  role: string
  status: string
  company_id: number | null
}

const staff = ref<Staff[]>([])
const editingId = ref<number | null>(null)
const localhost = 'http://localhost:5000/'

const fetchStaff = async () => {
  const res = await axios.get(localhost + 'api/users', {
    params: { company_id: companyId },
  })
  staff.value = res.data as Staff[]
}

onMounted(fetchStaff)

const saveUser = async (user: Staff) => {
  const payload = {
    id: user.id,
    role: user.role,
    status: user.status,
  }
  console.log('Sending:', payload)
  await axios.post(localhost + 'api/updateUser', payload)
  editingId.value = null
  fetchStaff()
}

const startEditing = (id: number) => {
  editingId.value = id
}
</script>

<template>
  <div class="container">
    <h1>Manage Staff</h1>
    <table>
      <thead>
        <tr>
          <th>ID</th>
          <th>Username</th>
          <th>Role</th>
          <th>Status</th>
          <th>Company</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="user in staff" :key="user.id" class="table-row">
          <td>{{ user.id }}</td>
          <td>{{ user.username }}</td>
          <td>
            <template v-if="editingId === user.id">
              <select v-model="user.role" class="input-select">
                <option value="admin">Admin</option>
                <option value="staff">Staff</option>
              </select>
            </template>
            <template v-else>
              {{ user.role }}
            </template>
          </td>
          <td>
            <template v-if="editingId === user.id">
              <select v-model="user.status" class="input-select">
                <option value="active">Active</option>
                <option value="inactive">Inactive</option>
              </select>
            </template>
            <template v-else>
              <span
                :class="['badge', user.status === 'active' ? 'badge-active' : 'badge-inactive']"
              >
                {{ user.status }}
              </span>
            </template>
          </td>
          <td>{{ user.company_id }}</td>
          <td>
            <button v-if="editingId === user.id" class="btn save-btn" @click="saveUser(user)">
              Save
            </button>
            <button v-else class="btn edit-btn" @click="startEditing(user.id)">Edit</button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
<style scoped>
.container {
  width: 90%;
  margin: 40px auto;
  background-color: #fff;
  border: 1px solid #ddd;
  border-radius: 10px;
  padding: 30px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  font-family: Arial, sans-serif;
}

h1 {
  margin-bottom: 20px;
  color: #333;
}

table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

th,
td {
  padding: 12px 16px;
  text-align: center;
  vertical-align: middle;
  border-bottom: 1px solid #e5e5e5;
}

th {
  background-color: #f9f9f9;
  color: #666;
  font-weight: bold;
}

.table-row {
  background-color: #fff;
  transition: background-color 0.2s ease-in-out;
}

.table-row:hover {
  background-color: #f2f2f2;
}

.input-select {
  padding: 6px 10px;
  font-size: 14px;
  border: 1px solid #ccc;
  border-radius: 6px;
  background-color: #fff;
}

.btn {
  padding: 6px 12px;
  font-size: 14px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.edit-btn {
  background-color: #eee;
  color: #333;
}

.edit-btn:hover {
  background-color: #ddd;
}

.save-btn {
  background-color: #007bff;
  color: #fff;
}

.save-btn:hover {
  background-color: #0069d9;
}

.badge {
  display: inline-block;
  padding: 4px 8px;
  font-size: 12px;
  font-weight: 600;
  border-radius: 12px;
  text-transform: capitalize;
}

.badge-admin {
  background-color: #007bff;
  color: white;
}

.badge-staff {
  background-color: #6c757d;
  color: white;
}

.badge-active {
  background-color: #28a745;
  color: white;
}

.badge-inactive {
  background-color: #dc3545;
  color: white;
}
</style>
