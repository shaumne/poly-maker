import axios from 'axios'

const API_BASE_URL = process.env.VUE_APP_API_URL || 'http://localhost:8000/api'

const client = axios.create({
  baseURL: API_BASE_URL,
  timeout: 45000,  // Increased to 45s for slow API calls (balance fetching from blockchain)
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
    // Preserve the original error structure for better error handling
    const apiError = {
      ...error,
      response: error.response,
      message: error.message || 'API request failed',
      status: error.response?.status || error.status,
      data: error.response?.data || error.data
    }
    console.error('API Error:', apiError.response?.data || apiError.message, apiError)
    return Promise.reject(apiError)
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
  
  fetchMarketBySlug(slug) {
    return client.get(`/markets/slug/${slug}`)
  },
  
  fetchAllMarketsBySlug(slug) {
    return client.get(`/markets/slug/${slug}/all`)
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
  
  fetchAllMarkets() {
    return client.get('/markets/fetch')
  },
  
  fetchCryptoMarkets() {
    return client.get('/markets/crypto/fetch')
  },
  
  getFetchStatus() {
    return client.get('/markets/fetch/status')
  },
  
  getCryptoFetchStatus() {
    return client.get('/markets/crypto/fetch/status')
  },
  
  bulkUpdateMarkets(marketIds, updateData) {
    return client.post('/markets/bulk/update', { 
      market_ids: marketIds,
      ...updateData
    })
  },
  
  bulkDeleteMarkets(marketIds) {
    return client.post('/markets/bulk/delete', { 
      market_ids: marketIds
    })
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
  
  getTestInfo() {
    return client.get('/trading/test-info')
  },
  
  getTradingDiagnostics() {
    return client.get('/trading/diagnostics')
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

