import api from '../../api/client'

export default {
  namespaced: true,
  
  state: {
    positions: [],
    loading: false,
    error: null
  },
  
  mutations: {
    SET_POSITIONS(state, positions) {
      state.positions = positions
    },
    
    SET_LOADING(state, loading) {
      state.loading = loading
    },
    
    SET_ERROR(state, error) {
      state.error = error
    }
  },
  
  actions: {
    async fetchPositions({ commit }, params = {}) {
      commit('SET_LOADING', true)
      commit('SET_ERROR', null)
      
      try {
        const positions = await api.getPositions(params)
        commit('SET_POSITIONS', positions)
      } catch (error) {
        commit('SET_ERROR', error.message)
        console.error('Error fetching positions:', error)
      } finally {
        commit('SET_LOADING', false)
      }
    }
  },
  
  getters: {
    totalPnl: state => {
      return state.positions.reduce((sum, pos) => {
        return sum + (pos.realized_pnl + pos.unrealized_pnl)
      }, 0)
    },
    
    positionsByMarket: state => marketId => {
      return state.positions.filter(p => p.market_id === marketId)
    }
  }
}

