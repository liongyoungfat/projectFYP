import { ref } from 'vue'
import { defineStore } from 'pinia'

export const useUserStore = defineStore('user', () => {
  // In a real app this would come from login
  const role = ref('admin')
  return { role }
})
