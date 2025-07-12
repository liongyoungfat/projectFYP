<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

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
      password: password.value
    })

    if (res.data.success) {
      localStorage.setItem('token', res.data.token)
      router.push('/dashboard')
    } else {
      alert('Invalid credentials')
    }
  } catch (error) {
    console.error('Login error:', error)
    alert('Login failed')
  } finally {
    isLoading.value = false
  }
}
</script>


<template>
  <div class="min-h-screen bg-gray-50">
    <header class="flex items-center justify-between px-6 py-4 shadow-sm bg-white">
      <div class="flex items-center gap-2 text-xl font-semibold text-blue-600">
        <img src="@/assets/logo.svg" class="w-6 h-6" alt="logo" />
        FinancePro
      </div>
      <div class="flex items-center gap-4">
        <RouterLink to="/login" class="text-gray-600 hover:text-blue-600">Login</RouterLink>
        <RouterLink to="/register" class="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700">Get Started</RouterLink>
      </div>
    </header>

    <div class="flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div class="max-w-md w-full space-y-8">
        <div class="text-center">
          <div class="w-16 h-16 bg-blue-600 rounded-xl flex items-center justify-center mx-auto mb-4">
            <i class="ri-line-chart-line text-white text-2xl"></i>
          </div>
          <h2 class="text-3xl font-bold text-gray-900 mb-2">Welcome back</h2>
          <p class="text-gray-600">Sign in to your account to access your financial dashboard</p>
        </div>

        <div class="bg-white p-8 rounded-xl shadow-sm border border-gray-200">
          <form @submit.prevent="handleLogin" class="space-y-6">
            <div>
              <label for="email" class="block text-sm font-medium text-gray-700 mb-2">Email address</label>
              <input
                type="email"
                id="email"
                v-model="email"
                required
                class="w-full px-4 py-2 border rounded-md focus:outline-none focus:ring focus:border-blue-300"
                placeholder="Enter your email"
              />
            </div>

            <div>
              <label for="password" class="block text-sm font-medium text-gray-700 mb-2">Password</label>
              <div class="relative">
                <input
                  :type="showPassword ? 'text' : 'password'"
                  id="password"
                  v-model="password"
                  required
                  class="w-full px-4 py-2 border rounded-md pr-10 focus:outline-none focus:ring focus:border-blue-300"
                  placeholder="Enter your password"
                />
                <button type="button" @click="togglePassword" class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500">
                  <i :class="showPassword ? 'ri-eye-off-line' : 'ri-eye-line'"></i>
                </button>
              </div>
            </div>

            <div class="flex items-center justify-between">
              <label class="flex items-center">
                <input type="checkbox" class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded" />
                <span class="ml-2 text-sm text-gray-700">Remember me</span>
              </label>
              <RouterLink to="/forgot-password" class="text-sm text-blue-600 hover:text-blue-500">Forgot your password?</RouterLink>
            </div>

            <button
              type="submit"
              :disabled="isLoading"
              class="w-full flex justify-center items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              <i v-if="isLoading" class="ri-loader-4-line animate-spin mr-2"></i>
              {{ isLoading ? 'Signing in...' : 'Sign in' }}
            </button>
          </form>

          <div class="mt-6 text-center">
            <p class="text-gray-600">
              Don't have an account?
              <RouterLink to="/register" class="text-blue-600 hover:text-blue-500 font-medium">Sign up</RouterLink>
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>


<style scoped>
/* Optional: additional scoped styles */
</style>
