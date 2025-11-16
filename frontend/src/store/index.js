import { createStore } from 'vuex'
import markets from './modules/markets'
import trading from './modules/trading'
import positions from './modules/positions'
import orders from './modules/orders'
import settings from './modules/settings'
import stats from './modules/stats'

export default createStore({
  modules: {
    markets,
    trading,
    positions,
    orders,
    settings,
    stats
  }
})

