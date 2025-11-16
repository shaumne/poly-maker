<template>
  <div id="app">
    <nav class="navbar">
      <div class="navbar-brand">
        <h1>🎯 Polymarket Trading Bot</h1>
      </div>
      <div class="navbar-menu">
        <router-link to="/" class="nav-link">Dashboard</router-link>
        <router-link to="/markets" class="nav-link">Markets</router-link>
        <router-link to="/positions" class="nav-link">Positions</router-link>
        <router-link to="/orders" class="nav-link">Orders</router-link>
        <router-link to="/settings" class="nav-link">Settings</router-link>
      </div>
      <div class="navbar-status">
        <span :class="['status-indicator', botStatus ? 'active' : 'inactive']"></span>
        <span>{{ botStatus ? 'Running' : 'Stopped' }}</span>
      </div>
    </nav>
    
    <main class="main-content">
      <router-view/>
    </main>
  </div>
</template>

<script>
import { computed, onMounted } from 'vue'
import { useStore } from 'vuex'

export default {
  name: 'App',
  setup() {
    const store = useStore()
    
    const botStatus = computed(() => store.state.trading.isRunning)
    
    onMounted(() => {
      // Load initial data
      store.dispatch('trading/fetchStatus')
      store.dispatch('markets/fetchMarkets')
    })
    
    return {
      botStatus
    }
  }
}
</script>

