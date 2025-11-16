import api from '../../api/client'

export default {
  namespaced: true,
  
  state: {
    status: null,
    isRunning: false,
    loading: false,
    error: null
  },
  
  mutations: {
    SET_STATUS(state, status) {
      state.status = status
      state.isRunning = status?.is_running || false
    },
    
    SET_LOADING(state, loading) {
      state.loading = loading
    },
    
    SET_ERROR(state, error) {
      state.error = error
    }
  },
  
  actions: {
    async fetchStatus({ commit }) {
      commit('SET_LOADING', true)
      commit('SET_ERROR', null)
      
      try {
        const status = await api.getTradingStatus()
        commit('SET_STATUS', status)
        return status
      } catch (error) {
        commit('SET_ERROR', error.message)
        console.error('Error fetching status:', error)
      } finally {
        commit('SET_LOADING', false)
      }
    },
    
    async startTrading({ commit, dispatch }) {
      commit('SET_LOADING', true)
      commit('SET_ERROR', null)
      
      try {
        await api.startTrading()
        await dispatch('fetchStatus')
      } catch (error) {
        commit('SET_ERROR', error.message)
        throw error
      } finally {
        commit('SET_LOADING', false)
      }
    },
    
    async stopTrading({ commit, dispatch }) {
      commit('SET_LOADING', true)
      commit('SET_ERROR', null)
      
      try {
        await api.stopTrading()
        await dispatch('fetchStatus')
      } catch (error) {
        commit('SET_ERROR', error.message)
        throw error
      } finally {
        commit('SET_LOADING', false)
      }
    },
    
    async restartTrading({ commit, dispatch }) {
      commit('SET_LOADING', true)
      commit('SET_ERROR', null)
      
      try {
        await api.restartTrading()
        await dispatch('fetchStatus')
      } catch (error) {
        commit('SET_ERROR', error.message)
        throw error
      } finally {
        commit('SET_LOADING', false)
      }
    }
  }
}

