import axios from 'axios'

const API_BASE_URL = process.env.VUE_APP_API_URL || 'http://localhost:8000/api'

const client = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Request interceptor
client.interceptors.request.use(
  config => {
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// Response interceptor
client.interceptors.response.use(
  response => response.data,
  error => {
    console.error('API Error:', error.response?.data || error.message)
    return Promise.reject(error)
  }
)

export default {
  // Markets
  getMarkets(params = {}) {
    return client.get('/markets', { params })
  },
  
  getMarket(id) {
    return client.get(`/markets/${id}`)
  },
  
  createMarket(data) {
    return client.post('/markets', data)
  },
  
  updateMarket(id, data) {
    return client.put(`/markets/${id}`, data)
  },
  
  deleteMarket(id) {
    return client.delete(`/markets/${id}`)
  },
  
  getMarketConfig(id) {
    return client.get(`/markets/${id}/config`)
  },
  
  updateMarketConfig(id, data) {
    return client.put(`/markets/${id}/config`, data)
  },
  
  fetchCryptoMarkets() {
    return client.get('/markets/crypto/fetch')
  },
  
  getFetchStatus() {
    return client.get('/markets/crypto/fetch/status')
  },
  
  // Trading
  getTradingStatus() {
    return client.get('/trading/status')
  },
  
  startTrading() {
    return client.post('/trading/start')
  },
  
  stopTrading() {
    return client.post('/trading/stop')
  },
  
  restartTrading() {
    return client.post('/trading/restart')
  },
  
  // Positions
  getPositions(params = {}) {
    return client.get('/positions', { params })
  },
  
  getPosition(id) {
    return client.get(`/positions/${id}`)
  },
  
  getMarketPositions(marketId) {
    return client.get(`/positions/market/${marketId}`)
  },
  
  getTokenPosition(tokenId) {
    return client.get(`/positions/token/${tokenId}`)
  },
  
  // Orders
  getOrders(params = {}) {
    return client.get('/orders', { params })
  },
  
  getActiveOrders() {
    return client.get('/orders/active')
  },
  
  getOrder(id) {
    return client.get(`/orders/${id}`)
  },
  
  getMarketOrders(marketId) {
    return client.get(`/orders/market/${marketId}`)
  },
  
  // Settings
  getSettings() {
    return client.get('/settings')
  },
  
  getSetting(key) {
    return client.get(`/settings/${key}`)
  },
  
  createSetting(data) {
    return client.post('/settings', data)
  },
  
  updateSetting(key, data) {
    return client.put(`/settings/${key}`, data)
  },
  
  deleteSetting(key) {
    return client.delete(`/settings/${key}`)
  },
  
  // Stats
  getStats() {
    return client.get('/stats')
  },
  
  getPnlBreakdown() {
    return client.get('/stats/pnl/breakdown')
  },
  
  getDailyPerformance(days = 7) {
    return client.get('/stats/performance/daily', { params: { days } })
  },
  
  // Wallet
  getWalletBalance() {
    return client.get('/wallet/balance')
  },
  
  getWalletTotal() {
    return client.get('/wallet/total')
  },
  
  getPositionsValue() {
    return client.get('/wallet/positions-value')
  },
  
  getWalletInfo() {
    return client.get('/wallet/info')
  },
  
  getTokenBalances() {
    return client.get('/wallet/token-balances')
  }
}

