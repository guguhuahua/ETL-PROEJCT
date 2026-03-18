import { ref, computed } from 'vue'
import api from '@/api'

const token = ref(localStorage.getItem('token') || '')
const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))

const isAuthenticated = computed(() => !!token.value)

async function login(credentials) {
  try {
    const response = await api.auth.login(credentials)
    token.value = response.access_token
    user.value = response.user

    localStorage.setItem('token', response.access_token)
    localStorage.setItem('user', JSON.stringify(response.user))

    return { success: true }
  } catch (error) {
    return { success: false, error: error.response?.data?.error || '登录失败' }
  }
}

async function register(userData) {
  try {
    await api.auth.register(userData)
    return { success: true }
  } catch (error) {
    return { success: false, error: error.response?.data?.error || '注册失败' }
  }
}

function logout() {
  token.value = ''
  user.value = null
  localStorage.removeItem('token')
  localStorage.removeItem('user')
}

async function fetchProfile() {
  try {
    const response = await api.auth.getProfile()
    user.value = response
    localStorage.setItem('user', JSON.stringify(response))
    return { success: true }
  } catch (error) {
    return { success: false, error: error.response?.data?.error }
  }
}

export function useAuthStore() {
  return {
    token,
    user,
    isAuthenticated,
    login,
    register,
    logout,
    fetchProfile
  }
}

// Export for direct access
export { token, user, isAuthenticated, login, register, logout, fetchProfile }