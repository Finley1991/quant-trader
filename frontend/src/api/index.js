import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000
})

export const strategiesApi = {
  getPresets: () => api.get('/strategies/presets'),
  getList: () => api.get('/strategies'),
  create: (data) => api.post('/strategies', data),
  toggle: (id) => api.put(`/strategies/${id}/toggle`)
}

export const backtestApi = {
  run: (data) => api.post('/backtest', data),
  getHistory: () => api.get('/backtest/history'),
  get: (id) => api.get(`/backtest/${id}`)
}

export const signalsApi = {
  getList: (skip = 0, limit = 50) => api.get(`/signals?skip=${skip}&limit=${limit}`),
  getToday: () => api.get('/signals/today'),
  scan: () => api.post('/signals/scan')
}

export const notifyApi = {
  test: (data) => api.post('/notify/test', data),
  getSettings: () => api.get('/notify/settings'),
  updateSettings: (data) => api.post('/notify/settings', data)
}

export default api
