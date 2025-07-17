import { ref } from 'vue'
import { defineStore } from 'pinia'

export const useUserStore = defineStore('user', () => {
  const role = ref(localStorage.getItem('userRole') || '')
  const token = ref(localStorage.getItem('userToken') || '')
  const company_id = ref(Number(localStorage.getItem('userCompanyId')) || null)
  const user_id = ref(Number(localStorage.getItem('userId')) || null)
  const username = ref(localStorage.getItem('username') || '')

  const setUser = (userData: {
    role: string
    token: string
    company_id: number
    user_id: number
    username: string
  }) => {
    role.value = userData.role
    token.value = userData.token
    company_id.value = userData.company_id
    user_id.value = userData.user_id
    username.value = userData.username

    // Also persist to localStorage
    localStorage.setItem('userRole', userData.role)
    localStorage.setItem('userToken', userData.token)
    localStorage.setItem('userCompanyId', String(userData.company_id))
    localStorage.setItem('userId', String(userData.user_id))
    localStorage.setItem('username', userData.username)
    // Set authToken for router guard
    localStorage.setItem('authToken', userData.token)
  }

  const logout = () => {
    role.value = ''
    token.value = ''
    company_id.value = null
    user_id.value = null
    username.value = ''
    localStorage.clear()
  }

  return { role, token, company_id, user_id, username, setUser, logout }
})
