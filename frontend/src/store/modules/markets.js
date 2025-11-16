import api from '../../api/client'

export default {
  namespaced: true,
  
  state: {
    markets: [],
    selectedMarket: null,
    loading: false,
    error: null
  },
  
  mutations: {
    SET_MARKETS(state, markets) {
      state.markets = markets
    },
    
    SET_SELECTED_MARKET(state, market) {
      state.selectedMarket = market
    },
    
    SET_LOADING(state, loading) {
      state.loading = loading
    },
    
    SET_ERROR(state, error) {
      state.error = error
    },
    
    ADD_MARKET(state, market) {
      state.markets.push(market)
    },
    
    UPDATE_MARKET(state, updatedMarket) {
      const index = state.markets.findIndex(m => m.id === updatedMarket.id)
      if (index !== -1) {
        state.markets.splice(index, 1, updatedMarket)
      }
    },
    
    REMOVE_MARKET(state, id) {
      state.markets = state.markets.filter(m => m.id !== id)
    }
  },
  
  actions: {
    async fetchMarkets({ commit }, params = {}) {
      commit('SET_LOADING', true)
      commit('SET_ERROR', null)
      
      try {
        // Set default limit to 10000 to get all markets
        const fetchParams = { limit: 10000, ...params }
        const markets = await api.getMarkets(fetchParams)
        commit('SET_MARKETS', markets)
        console.log(`Loaded ${markets.length} markets`)
      } catch (error) {
        commit('SET_ERROR', error.message)
        console.error('Error fetching markets:', error)
      } finally {
        commit('SET_LOADING', false)
      }
    },
    
    async fetchMarket({ commit }, id) {
      commit('SET_LOADING', true)
      commit('SET_ERROR', null)
      
      try {
        const market = await api.getMarket(id)
        commit('SET_SELECTED_MARKET', market)
        return market
      } catch (error) {
        commit('SET_ERROR', error.message)
        console.error('Error fetching market:', error)
      } finally {
        commit('SET_LOADING', false)
      }
    },
    
    async createMarket({ commit }, marketData) {
      try {
        const market = await api.createMarket(marketData)
        commit('ADD_MARKET', market)
        return market
      } catch (error) {
        commit('SET_ERROR', error.message)
        throw error
      }
    },
    
    async updateMarket({ commit }, { id, data }) {
      try {
        const market = await api.updateMarket(id, data)
        commit('UPDATE_MARKET', market)
        return market
      } catch (error) {
        commit('SET_ERROR', error.message)
        throw error
      }
    },
    
    async deleteMarket({ commit }, id) {
      try {
        await api.deleteMarket(id)
        commit('REMOVE_MARKET', id)
      } catch (error) {
        commit('SET_ERROR', error.message)
        throw error
      }
    },
    
    async fetchCryptoMarkets({ commit }) {
      commit('SET_LOADING', true)
      commit('SET_ERROR', null)
      
      try {
        const markets = await api.fetchCryptoMarkets()
        commit('SET_MARKETS', markets)
        return markets
      } catch (error) {
        // Extract detailed error message
        const errorMessage = error.response?.data?.detail || error.message || 'Unknown error occurred'
        commit('SET_ERROR', errorMessage)
        console.error('Error fetching crypto markets:', error)
        
        // Re-throw with more context
        const enhancedError = new Error(errorMessage)
        enhancedError.response = error.response
        throw enhancedError
      } finally {
        commit('SET_LOADING', false)
      }
    }
  },
  
  getters: {
    activeMarkets: state => state.markets.filter(m => m.is_active),
    cryptoMarkets: state => state.markets.filter(m => m.category === 'crypto'),
    marketById: state => id => state.markets.find(m => m.id === id)
  }
}

