import api from '../../api/client'

// Cache süresi: 5 saniye (trade botu için sürekli güncel veri gerekli)
const CACHE_DURATION = 5000

export default {
  namespaced: true,
  
  state: {
    orders: [],
    loading: false,
    error: null,
    lastFetched: null
  },
  
  mutations: {
    SET_ORDERS(state, orders) {
      state.orders = orders
    },
    
    SET_LOADING(state, loading) {
      state.loading = loading
    },
    
    SET_ERROR(state, error) {
      state.error = error
    },
    
    SET_LAST_FETCHED(state, timestamp) {
      state.lastFetched = timestamp
    }
  },
  
  actions: {
    async fetchOrders({ commit, state, getters }, params = {}) {
      const { force = false } = params
      
      // Cache kontrolü: eğer cache geçerliyse ve force refresh değilse ve veri varsa, API çağrısı yapma
      // Eğer orders boşsa ve ilk yükleme ise cache'i bypass et
      if (!force && getters.isCacheValid && state.orders.length > 0) {
        console.log('[Orders] Cache geçerli, API çağrısı yapılmıyor')
        return
      }
      
      commit('SET_LOADING', true)
      commit('SET_ERROR', null)
      
      try {
        const orders = await api.getOrders(params)
        commit('SET_ORDERS', orders)
        commit('SET_LAST_FETCHED', Date.now())
        console.log(`[Orders] Veri başarıyla çekildi: ${orders.length} order, cache güncellendi`)
      } catch (error) {
        commit('SET_ERROR', error.message)
        console.error('Error fetching orders:', error)
      } finally {
        commit('SET_LOADING', false)
      }
    },
    
    async fetchActiveOrders({ commit, state, getters }, force = false) {
      // Cache kontrolü: eğer cache geçerliyse ve force refresh değilse ve veri varsa, API çağrısı yapma
      // Eğer orders boşsa ve ilk yükleme ise cache'i bypass et
      if (!force && getters.isCacheValid && state.orders.length > 0) {
        console.log('[Orders] Cache geçerli (active orders), API çağrısı yapılmıyor')
        return
      }
      
      commit('SET_LOADING', true)
      commit('SET_ERROR', null)
      
      try {
        const orders = await api.getActiveOrders()
        commit('SET_ORDERS', orders)
        commit('SET_LAST_FETCHED', Date.now())
        console.log(`[Orders] Active orders başarıyla çekildi: ${orders.length} order, cache güncellendi`)
      } catch (error) {
        commit('SET_ERROR', error.message)
        console.error('Error fetching active orders:', error)
      } finally {
        commit('SET_LOADING', false)
      }
    }
  },
  
  getters: {
    activeOrders: state => state.orders.filter(o => o.status === 'PENDING'),
    ordersByMarket: state => marketId => state.orders.filter(o => o.market_id === marketId),
    
    isCacheValid: state => {
      if (!state.lastFetched) {
        return false
      }
      const now = Date.now()
      const cacheAge = now - state.lastFetched
      return cacheAge < CACHE_DURATION
    }
  }
}

