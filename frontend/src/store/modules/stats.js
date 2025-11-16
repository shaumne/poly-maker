import api from '../../api/client'

export default {
  namespaced: true,
  
  state: {
    stats: null,
    pnlBreakdown: [],
    dailyPerformance: [],
    loading: false,
    error: null
  },
  
  mutations: {
    SET_STATS(state, stats) {
      state.stats = stats
    },
    
    SET_PNL_BREAKDOWN(state, breakdown) {
      state.pnlBreakdown = breakdown
    },
    
    SET_DAILY_PERFORMANCE(state, performance) {
      state.dailyPerformance = performance
    },
    
    SET_LOADING(state, loading) {
      state.loading = loading
    },
    
    SET_ERROR(state, error) {
      state.error = error
    }
  },
  
  actions: {
    async fetchStats({ commit }) {
      commit('SET_LOADING', true)
      commit('SET_ERROR', null)
      
      try {
        const stats = await api.getStats()
        commit('SET_STATS', stats)
      } catch (error) {
        commit('SET_ERROR', error.message)
        console.error('Error fetching stats:', error)
      } finally {
        commit('SET_LOADING', false)
      }
    },
    
    async fetchPnlBreakdown({ commit }) {
      try {
        const data = await api.getPnlBreakdown()
        commit('SET_PNL_BREAKDOWN', data.breakdown)
      } catch (error) {
        commit('SET_ERROR', error.message)
        console.error('Error fetching PnL breakdown:', error)
      }
    },
    
    async fetchDailyPerformance({ commit }, days = 7) {
      try {
        const data = await api.getDailyPerformance(days)
        commit('SET_DAILY_PERFORMANCE', data.performance)
      } catch (error) {
        commit('SET_ERROR', error.message)
        console.error('Error fetching daily performance:', error)
      }
    }
  }
}

