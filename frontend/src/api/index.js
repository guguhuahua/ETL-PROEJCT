import request from '@/utils/request'

const auth = {
  register: (data) => request.post('/auth/register', data),
  login: (data) => request.post('/auth/login', data),
  logout: () => request.post('/auth/logout'),
  getProfile: () => request.get('/auth/profile'),
  updateProfile: (data) => request.put('/auth/profile', data),
  refreshToken: () => request.post('/auth/refresh')
}

const dataSources = {
  getAll: () => request.get('/data-sources'),
  getById: (id) => request.get(`/data-sources/${id}`),
  create: (data) => request.post('/data-sources', data),
  update: (id, data) => request.put(`/data-sources/${id}`, data),
  delete: (id) => request.delete(`/data-sources/${id}`),
  testConnection: (data) => request.post('/data-sources/test-connection', data),
  getTables: (id) => request.get(`/data-sources/${id}/tables`),
  getColumns: (id, tableName) => request.get(`/data-sources/${id}/tables/${tableName}/columns`),
  testSql: (id, sql) => request.post(`/data-sources/${id}/test-sql`, { sql })
}

const eltTasks = {
  getAll: () => request.get('/elt-tasks'),
  getById: (id) => request.get(`/elt-tasks/${id}`),
  create: (data) => request.post('/elt-tasks', data),
  update: (id, data) => request.put(`/elt-tasks/${id}`, data),
  delete: (id) => request.delete(`/elt-tasks/${id}`),
  execute: (id) => request.post(`/elt-tasks/${id}/execute`),
  preview: (id, sql) => request.post(`/elt-tasks/${id}/preview`, { sql }),
  getExecutions: (id) => request.get(`/elt-tasks/${id}/executions`)
}

const schedules = {
  getAll: () => request.get('/schedules'),
  getById: (id) => request.get(`/schedules/${id}`),
  create: (data) => request.post('/schedules', data),
  update: (id, data) => request.put(`/schedules/${id}`, data),
  delete: (id) => request.delete(`/schedules/${id}`),
  toggle: (id) => request.post(`/schedules/${id}/toggle`)
}

const taskExecutions = {
  getAll: (params) => request.get('/task-executions', { params }),
  getById: (id) => request.get(`/task-executions/${id}`),
  getStats: () => request.get('/task-executions/stats')
}

const workflows = {
  getAll: (params) => request.get('/workflows', { params }),
  getById: (id) => request.get(`/workflows/${id}`),
  create: (data) => request.post('/workflows', data),
  update: (id, data) => request.put(`/workflows/${id}`, data),
  delete: (id) => request.delete(`/workflows/${id}`),
  execute: (id) => request.post(`/workflows/${id}/execute`),
  getExecutions: (id) => request.get(`/workflows/${id}/executions`),
  toggleActive: (id, isActive) => request.put(`/workflows/${id}`, { is_active: isActive })
}

export default {
  auth,
  dataSources,
  eltTasks,
  schedules,
  taskExecutions,
  workflows
}