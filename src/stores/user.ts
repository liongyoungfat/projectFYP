import { ref } from 'vue'
import { defineStore } from 'pinia'

export const useUserStore = defineStore('user', () => {
  const role = ref('')
  const token = ref('')

  const setUser = (userData: { role: string; token: string }) => {
    role.value = userData.role
    token.value = userData.token
  }

  const logout = () => {
    role.value = ''
    token.value = ''
    localStorage.clear()
  }

  return { role, token, setUser, logout }
})
