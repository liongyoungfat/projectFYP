<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import axios from 'axios'
import { useRouter } from 'vue-router'

const router = useRouter()

const isLoading = ref(false)
const role = ref('staff')
const localhost = 'http://localhost:5000/'

const form = reactive({
  username: '',
  email: '',
  password: '',
  role: 'staff',
  company_id: '',
})

const company = reactive({
  name: '',
  industry: '',
  address: '',
})

const companies = ref<{ id: number; name: string }[]>([])

const handleRoleChange = () => {
  form.company_id = ''
  company.name = ''
  company.industry = ''
  company.address = ''
}

const loadCompanies = async () => {
  try {
    const res = await axios.get(`${localhost}api/companies`)
    companies.value = res.data
  } catch (error) {
    console.error('Failed to load companies:', error)
  }
}

const handleRegister = async () => {
  isLoading.value = true
  try {
    if (form.role === 'admin') {
      const companyRes = await axios.post(`${localhost}api/companies`, {
        name: company.name,
        industry: company.industry,
        address: company.address,
      })

      form.company_id = companyRes.data.company_id
    }

    const userRes = await axios.post(`${localhost}api/register`, {
      ...form,
    })

    if (userRes.data.success) {
      alert('Registered successfully!')
      router.push('/login')
    } else {
      alert('Registration failed.')
    }
  } catch (error) {
    console.error('Registration error:', error)
    alert('Something went wrong.')
  } finally {
    isLoading.value = false
  }
}

loadCompanies()

watch(role, handleRoleChange)
</script>

<template>
  <div class="login-container">
    <div class="login-header">
      <h1>Create your account</h1>
      <p>Register to access the system</p>
    </div>

    <div class="login-card">
      <form @submit.prevent="handleRegister">
        <div class="input-group">
          <label>Username</label>
          <input type="text" v-model="form.username" placeholder="Enter username" required />
        </div>

        <div class="input-group">
          <label>Email</label>
          <input type="email" v-model="form.email" placeholder="Enter email" required />
        </div>

        <div class="input-group">
          <label>Password</label>
          <input type="password" v-model="form.password" placeholder="Enter password" required />
        </div>

        <div class="input-group">
          <label>Role</label>
          <select v-model="form.role" @change="handleRoleChange">
            <option value="staff">Staff</option>
            <option value="admin">Admin</option>
          </select>
        </div>

        <!-- STAFF ONLY: Choose existing company -->
        <div class="input-group" v-if="form.role === 'staff'">
          <label>Company</label>
          <select v-model="form.company_id" required>
            <option value="" disabled>Select company</option>
            <option v-for="company in companies" :key="company.id" :value="company.id">
              {{ company.name }}
            </option>
          </select>
        </div>

        <!-- ADMIN ONLY: Register new company -->
        <div v-if="form.role === 'admin'">
          <div class="input-group">
            <label>Company Name</label>
            <input type="text" v-model="company.name" placeholder="Enter company name" required />
          </div>

          <div class="input-group">
            <label>Industry</label>
            <input type="text" v-model="company.industry" placeholder="Enter industry" required />
          </div>

          <div class="input-group">
            <label>Address</label>
            <input type="text" v-model="company.address" placeholder="Enter address" required />
          </div>
        </div>

        <button type="submit" class="login-button">Register</button>
      </form>

      <div class="login-footer">Already have an account? <a href="#">Login</a></div>
    </div>
  </div>
</template>
