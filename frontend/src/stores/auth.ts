import { defineStore } from 'pinia'
import { ref } from 'vue'
import { authApi, type LoginPayload } from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('autotest_token') || '')
  const username = ref(localStorage.getItem('autotest_user') || '')

  async function login(payload: LoginPayload) {
    const data = await authApi.login(payload)
    token.value = data.access
    username.value = payload.username
    localStorage.setItem('autotest_token', data.access)
    localStorage.setItem('autotest_refresh', data.refresh)
    localStorage.setItem('autotest_user', payload.username)
  }

  function logout() {
    token.value = ''
    username.value = ''
    localStorage.removeItem('autotest_token')
    localStorage.removeItem('autotest_refresh')
    localStorage.removeItem('autotest_user')
  }

  return { token, username, login, logout }
})
