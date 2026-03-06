import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000
})

const strategiesApi = {
  getPresets: () => api.get('/strategies/presets'),
  getList: () => api.get('/strategies'),
  create: (data) => api.post('/strategies', data),
  toggle: (id) => api.put(`/strategies/${id}/toggle`)
}

const backtestApi = {
  run: (data) => api.post('/backtest', data),
  getHistory: () => api.get('/backtest/history'),
  get: (id) => api.get(`/backtest/${id}`)
}

const signalsApi = {
  getList: (skip = 0, limit = 50) => api.get(`/signals?skip=${skip}&limit=${limit}`),
  getToday: () => api.get('/signals/today'),
  scan: () => api.post('/signals/scan')
}

const notifyApi = {
  test: (data) => api.post('/notify/test', data),
  getSettings: () => api.get('/notify/settings'),
  updateSettings: (data) => api.post('/notify/settings', data)
}

const watchlistApi = {
  getList: (assetType) => api.get('/watchlist', { params: { asset_type: assetType } }),
  add: (data) => api.post('/watchlist', data),
  remove: (ts_code) => api.delete(`/watchlist/${ts_code}`),
  getQuotes: () => api.get('/watchlist/quotes')
}

const stocksApi = {
  search: (keyword) => api.get(`/stocks/search?keyword=${encodeURIComponent(keyword)}`),
  list: (limit = 100) => api.get(`/stocks/list?limit=${limit}`),
  getKline: (ts_code, freq = 'auto') => api.get(`/stocks/${ts_code}/kline?freq=${freq}`)
}

const fundsApi = {
  search: (keyword) => api.get('/funds/search', { params: { keyword } }),
  list: (fundType, limit) => api.get('/funds/list', { params: { fund_type: fundType, limit } }),
  getKline: (tsCode) => api.get(`/funds/${tsCode}/kline`),
}

export { strategiesApi, backtestApi, signalsApi, notifyApi, watchlistApi, stocksApi, fundsApi }
export default api
