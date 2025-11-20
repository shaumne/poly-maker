import api from '../../api/client'

// Cache süresi: 5 saniye (trade botu için sürekli güncel veri gerekli)
const CACHE_DURATION = 5000

export default {
  namespaced: true,
  
  state: {
    positions: [],
    loading: false,
    error: null,
    lastFetched: null
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
    },
    
    SET_LAST_FETCHED(state, timestamp) {
      state.lastFetched = timestamp
    }
  },
  
  actions: {
    async fetchPositions({ commit, state, getters }, params = {}) {
      const { force = false } = params
      
      // Cache kontrolü: eğer cache geçerliyse ve force refresh değilse ve veri varsa, API çağrısı yapma
      // Eğer positions boşsa ve ilk yükleme ise cache'i bypass et
      if (!force && getters.isCacheValid && state.positions.length > 0) {
        console.log('[Positions] Cache geçerli, API çağrısı yapılmıyor')
        return
      }
      
      commit('SET_LOADING', true)
      commit('SET_ERROR', null)
      
      try {
        const positions = await api.getPositions(params)
        commit('SET_POSITIONS', positions)
        commit('SET_LAST_FETCHED', Date.now())
        console.log(`[Positions] Veri başarıyla çekildi: ${positions.length} position, cache güncellendi`)
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
    },
    
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

