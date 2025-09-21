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
const originalUser = ref<Staff | null>(null)
const localhost = 'http://18.232.124.137:8000/'

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
  originalUser.value = null
  fetchStaff()
}

const cancelEdit = () => {
  if (editingId.value !== null && originalUser.value) {
    // Restore original values
    const idx = staff.value.findIndex((u) => u.id === originalUser.value!.id)
    if (idx !== -1) {
      staff.value[idx].role = originalUser.value.role
      staff.value[idx].status = originalUser.value.status
    }
  }
  editingId.value = null
  originalUser.value = null
}
const startEditing = (id: number) => {
  editingId.value = id
  const user = staff.value.find((u) => u.id === id)
  if (user) {
    // Save original values for cancel
    originalUser.value = { ...user }
  }
}
</script>

<template>
  <div class="container">
    <h1>🏢👨‍💼👩‍💼 Manage Staff</h1>
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
            <template v-if="editingId === user.id">
              <button
                class="btn save-btn"
                @click="saveUser(user)"
                :disabled="user.role === originalUser?.role && user.status === originalUser?.status"
              >
                Save
              </button>
              <button class="btn cancel-btn" @click="cancelEdit" style="margin-left: 8px">
                Cancel
              </button>
            </template>
            <template v-else>
              <button
                class="btn edit-btn"
                @click="startEditing(user.id)"
                :disabled="user.id === userStore.user_id"
                :title="user.id === userStore.user_id ? 'You cannot edit your own account' : ''"
              >
                Edit
              </button>
            </template>
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
  padding: 6px 16px;
  font-size: 15px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.07);
  transition:
    background 0.18s,
    color 0.18s,
    box-shadow 0.18s,
    transform 0.18s;
  will-change: transform, box-shadow;
}

.edit-btn {
  background-color: #eee;
  color: #333;
  font-weight: 600;
}
.edit-btn[disabled] {
  cursor: not-allowed;
  opacity: 0.7;
  background-color: #eee;
  color: #aaa;
  box-shadow: none;
}
.edit-btn:hover:enabled {
  background-color: #ddd;
  color: #007bff;
  transform: scale(1.07) translateY(-2px) rotate(-1deg);
  box-shadow: 0 6px 18px rgba(0, 123, 255, 0.13);
}
.edit-btn:active:enabled {
  transform: scale(0.95) rotate(1deg);
  box-shadow: 0 2px 8px rgba(0, 123, 255, 0.13);
}

.save-btn {
  background-color: #007bff;
  color: #fff;
  font-weight: 700;
  transition:
    background-color 0.2s,
    color 0.2s,
    opacity 0.2s;
}
.save-btn:not(:disabled):hover {
  background-color: #0069d9;
  color: #fff;
  transform: scale(1.07) translateY(-2px) rotate(-1deg);
  box-shadow: 0 6px 18px rgba(0, 123, 255, 0.18);
}
.save-btn:not(:disabled):active {
  transform: scale(0.95) rotate(1deg);
  box-shadow: 0 2px 8px rgba(0, 123, 255, 0.18);
}
.save-btn:disabled {
  background-color: #bfc8d8;
  color: #888;
  cursor: not-allowed;
  opacity: 0.7;
  box-shadow: none;
  transform: none;
}

.cancel-btn {
  background-color: #f3f4f6;
  color: #dc3545;
  font-weight: 600;
}
.cancel-btn:hover {
  background-color: #ffeaea;
  color: #fff;
  transform: scale(1.07) translateY(-2px) rotate(-1deg);
  box-shadow: 0 6px 18px rgba(220, 53, 69, 0.13);
}
.cancel-btn:active {
  transform: scale(0.95) rotate(1deg);
  box-shadow: 0 2px 8px rgba(220, 53, 69, 0.13);
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
