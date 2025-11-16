import api from '../../api/client'

export default {
  namespaced: true,
  
  state: {
    settings: [],
    loading: false,
    error: null
  },
  
  mutations: {
    SET_SETTINGS(state, settings) {
      state.settings = settings
    },
    
    SET_LOADING(state, loading) {
      state.loading = loading
    },
    
    SET_ERROR(state, error) {
      state.error = error
    },
    
    UPDATE_SETTING(state, updatedSetting) {
      const index = state.settings.findIndex(s => s.key === updatedSetting.key)
      if (index !== -1) {
        state.settings.splice(index, 1, updatedSetting)
      } else {
        state.settings.push(updatedSetting)
      }
    }
  },
  
  actions: {
    async fetchSettings({ commit }) {
      commit('SET_LOADING', true)
      commit('SET_ERROR', null)
      
      try {
        const settings = await api.getSettings()
        commit('SET_SETTINGS', settings)
      } catch (error) {
        commit('SET_ERROR', error.message)
        console.error('Error fetching settings:', error)
      } finally {
        commit('SET_LOADING', false)
      }
    },
    
    async updateSetting({ commit }, { key, data }) {
      try {
        const setting = await api.updateSetting(key, data)
        commit('UPDATE_SETTING', setting)
        return setting
      } catch (error) {
        commit('SET_ERROR', error.message)
        throw error
      }
    },
    
    async createSetting({ commit }, data) {
      try {
        const setting = await api.createSetting(data)
        commit('UPDATE_SETTING', setting)
        return setting
      } catch (error) {
        commit('SET_ERROR', error.message)
        throw error
      }
    }
  },
  
  getters: {
    settingByKey: state => key => state.settings.find(s => s.key === key)
  }
}

