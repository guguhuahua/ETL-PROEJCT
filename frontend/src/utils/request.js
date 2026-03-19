import axios from 'axios'
import { ElMessage } from 'element-plus'

// Create axios instance
// 生产环境使用相对路径，开发环境使用localhost
const baseURL = process.env.NODE_ENV === 'production'
  ? '/api'
  : (process.env.VUE_APP_API_URL || 'http://localhost:5000/api')

const request = axios.create({
  baseURL: baseURL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Request interceptor
request.interceptors.request.use(
  config => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// Response interceptor
request.interceptors.response.use(
  response => {
    return response.data
  },
  error => {
    const message = error.response?.data?.error || error.message || '请求失败'

    // 401错误处理：登录接口显示错误，其他接口跳转登录页
    if (error.response?.status === 401) {
      const isLoginRequest = error.config?.url?.includes('/auth/login')
      if (isLoginRequest) {
        // 登录失败，显示错误信息
        ElMessage.error(message)
      } else {
        // token过期，清除登录状态并跳转
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        window.location.href = '/login'
      }
    } else {
      ElMessage.error(message)
    }

    return Promise.reject(error)
  }
)

export default request