import api from '../../api/client'

export default {
  namespaced: true,
  
  state: {
    orders: [],
    loading: false,
    error: null
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
    }
  },
  
  actions: {
    async fetchOrders({ commit }, params = {}) {
      commit('SET_LOADING', true)
      commit('SET_ERROR', null)
      
      try {
        const orders = await api.getOrders(params)
        commit('SET_ORDERS', orders)
      } catch (error) {
        commit('SET_ERROR', error.message)
        console.error('Error fetching orders:', error)
      } finally {
        commit('SET_LOADING', false)
      }
    },
    
    async fetchActiveOrders({ commit }) {
      commit('SET_LOADING', true)
      commit('SET_ERROR', null)
      
      try {
        const orders = await api.getActiveOrders()
        commit('SET_ORDERS', orders)
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
    ordersByMarket: state => marketId => state.orders.filter(o => o.market_id === marketId)
  }
}

