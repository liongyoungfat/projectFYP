<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
const email = ref('')
const password = ref('')
const isLoading = ref(false)
const showPassword = ref(false)
const router = useRouter()

const togglePassword = () => {
  showPassword.value = !showPassword.value
}

const handleLogin = async () => {
  isLoading.value = true
  try {
    const res = await axios.post('http://localhost:5000/api/login', {
      email: email.value,
      password: password.value,
    })

    // success path
    if (res.data.success) {
      userStore.setUser({
        user_id: res.data.user.id,
        role: res.data.user.role,
        company_id: res.data.user.company_id,
        username: res.data.user.username,
        token: res.data.token,
      })
      localStorage.setItem('userRole', res.data.user.role)
      localStorage.setItem('userCompanyId', res.data.user.company_id)
      localStorage.setItem('userId', res.data.user.id)
      localStorage.setItem('userName', res.data.user.username)
      router.push('/dashboard')
    } else {
      // shouldn't happen, but just in case
      alert(res.data.message || 'Login failed')
    }
  } catch (error) {
    const status = error.response?.status
    const msg = error.response?.data?.message

    if (status === 403) {
      // account exists but inactive
      alert(msg || 'Your account is inactive. Please contact support.')
    } else if (status === 401) {
      // bad credentials
      alert('Invalid credentials')
    } else {
      console.error('Login error:', error)
      alert('Something went wrong. Please try again later.')
    }
  } finally {
    isLoading.value = false
  }
}

const goToRegister = () => {
  router.push('/register')
}
</script>

<template>
  <div class="login-container">
    <!-- Header -->
    <div class="login-header">
      <div
        style="
          background-color: #2563eb;
          padding: 12px;
          border-radius: 10px;
          display: inline-block;
          margin-bottom: 16px;
        "
      >
        <svg
          width="24"
          height="24"
          fill="none"
          stroke="white"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
          viewBox="0 0 24 24"
        >
          <path d="M3 3v18h18" />
        </svg>
      </div>
      <h1>Welcome back</h1>
      <p>Sign in to your account to access your financial dashboard</p>
    </div>

    <!-- Login Card -->
    <div class="login-card">
      <form @submit.prevent="handleLogin">
        <div class="input-group">
          <label>Email address</label>
          <input type="email" v-model="email" placeholder="Enter your email" required />
        </div>

        <div class="input-group">
          <label>Password</label>
          <div style="position: relative">
            <input
              :type="showPassword ? 'text' : 'password'"
              v-model="password"
              placeholder="Enter your password"
              required
              style="padding-right: 40px"
            />
            <button
              type="button"
              @click="togglePassword"
              style="
                position: absolute;
                right: 10px;
                top: 50%;
                transform: translateY(-50%);
                background: none;
                border: none;
                cursor: pointer;
                color: #6b7280;
              "
            >
              <i :class="showPassword ? 'ri-eye-off-line' : 'ri-eye-line'"></i>
            </button>
          </div>
        </div>

        <div class="options-row">
          <label><input type="checkbox" /> Remember me</label>
          <a
            href="https://mail.google.com/mail/?view=cm&fs=1&to=liongyeong@gmail.com&su=Password%20Reset%20Request&body=Hi,%20my%20gmail%20is%20[YOUR_EMAIL]%20and%20I%20forget%20my%20password.%20Please%20help%20me%20change%20it."
            target="_blank"
          >
            Forget your password?
          </a>
        </div>

        <button type="submit" class="login-button">Sign in</button>
      </form>

      <div class="login-footer">
        Don't have an account?
        <a href="#" @click.prevent="goToRegister">Sign up</a>
      </div>
    </div>
  </div>
</template>

<style scoped>
body {
  background-color: #f9fafb;
}
</style>
