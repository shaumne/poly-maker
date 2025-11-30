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
        const errorMsg = typeof error?.message === 'string' 
          ? error.message 
          : (error?.response?.data?.detail || JSON.stringify(error) || 'Unknown error')
        commit('SET_ERROR', errorMsg)
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
        const errorMsg = typeof error?.message === 'string' 
          ? error.message 
          : (error?.response?.data?.detail || JSON.stringify(error) || 'Unknown error')
        commit('SET_ERROR', errorMsg)
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
        const errorMsg = typeof error?.message === 'string' 
          ? error.message 
          : (error?.response?.data?.detail || JSON.stringify(error) || 'Unknown error')
        commit('SET_ERROR', errorMsg)
        throw error
      }
    },
    
    async updateMarket({ commit }, { id, data }) {
      try {
        const market = await api.updateMarket(id, data)
        commit('UPDATE_MARKET', market)
        return market
      } catch (error) {
        const errorMsg = typeof error?.message === 'string' 
          ? error.message 
          : (error?.response?.data?.detail || JSON.stringify(error) || 'Unknown error')
        commit('SET_ERROR', errorMsg)
        throw error
      }
    },
    
    async deleteMarket({ commit }, id) {
      try {
        await api.deleteMarket(id)
        commit('REMOVE_MARKET', id)
      } catch (error) {
        const errorMsg = typeof error?.message === 'string' 
          ? error.message 
          : (error?.response?.data?.detail || JSON.stringify(error) || 'Unknown error')
        commit('SET_ERROR', errorMsg)
        throw error
      }
    },
    
    async fetchCryptoMarkets({ commit }) {
      commit('SET_LOADING', true)
      commit('SET_ERROR', null)
      
      try {
        const response = await api.fetchCryptoMarkets()
        // fetchCryptoMarkets returns a status object, not markets array
        // It starts a background task, so we return the response
        return response
      } catch (error) {
        // Extract detailed error message - handle object errors properly
        let errorMessage = 'Unknown error occurred'
        
        if (typeof error === 'string') {
          errorMessage = error
        } else if (error?.response?.data?.detail) {
          errorMessage = typeof error.response.data.detail === 'string' 
            ? error.response.data.detail 
            : JSON.stringify(error.response.data.detail)
        } else if (error?.response?.data?.message) {
          errorMessage = typeof error.response.data.message === 'string'
            ? error.response.data.message
            : JSON.stringify(error.response.data.message)
        } else if (error?.data?.detail) {
          errorMessage = typeof error.data.detail === 'string'
            ? error.data.detail
            : JSON.stringify(error.data.detail)
        } else if (error?.message) {
          errorMessage = typeof error.message === 'string'
            ? error.message
            : JSON.stringify(error.message)
        } else if (error?.response?.data) {
          try {
            errorMessage = JSON.stringify(error.response.data)
          } catch {
            errorMessage = String(error.response.data)
          }
        }
        
        commit('SET_ERROR', errorMessage)
        console.error('Error fetching crypto markets:', error)
        
        // Re-throw with more context
        const enhancedError = new Error(errorMessage)
        enhancedError.response = error.response
        enhancedError.status = error.status || error.response?.status
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

