import axios, { AxiosError, type AxiosInstance } from 'axios'
import { ElMessage } from 'element-plus'

const http: AxiosInstance = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

http.interceptors.request.use((config) => {
  const token = localStorage.getItem('autotest_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

http.interceptors.response.use(
  (resp) => resp,
  (err: AxiosError<{ detail?: string }>) => {
    const status = err.response?.status
    const msg = err.response?.data?.detail || err.message
    if (status === 401) {
      localStorage.removeItem('autotest_token')
      ElMessage.error('请重新登录')
      window.location.href = '/login'
    } else if (status && status >= 400) {
      ElMessage.error(msg)
    } else {
      ElMessage.error(msg)
    }
    return Promise.reject(err)
  }
)

export default http
