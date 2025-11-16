<template>
  <div class="dashboard">
    <div class="dashboard-header">
      <h2>Dashboard</h2>
      <div class="controls">
        <button 
          v-if="!isRunning" 
          @click="startBot" 
          class="btn btn-success"
          :disabled="loading"
        >
          ▶ Start Trading
        </button>
        <button 
          v-else 
          @click="stopBot" 
          class="btn btn-danger"
          :disabled="loading"
        >
          ⏸ Stop Trading
        </button>
      </div>
    </div>

    <!-- Stats Grid -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-label">Positions Value</div>
        <div class="stat-value" :class="stats?.positions_value !== null && stats?.positions_value !== undefined ? '' : 'text-muted'">
          ${{ stats?.positions_value?.toFixed(2) ?? 'N/A' }}
        </div>
        <div class="stat-change" v-if="tokenBalances && tokenBalances.count > 0">
          {{ tokenBalances.count }} token(s) with balance
        </div>
        <div class="stat-change text-muted" v-else>
          No active positions
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-label">Total PnL</div>
        <div class="stat-value" :class="stats?.total_pnl >= 0 ? 'positive' : 'negative'">
          ${{ stats?.total_pnl?.toFixed(2) || '0.00' }}
        </div>
        <div class="stat-change" :class="stats?.today_pnl >= 0 ? 'positive' : 'negative'">
          Today: ${{ stats?.today_pnl?.toFixed(2) || '0.00' }}
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-label">Active Markets</div>
        <div class="stat-value">{{ stats?.active_markets || 0 }}</div>
        <div class="stat-change">Total: {{ stats?.total_markets || 0 }}</div>
      </div>

      <div class="stat-card">
        <div class="stat-label">Open Positions</div>
        <div class="stat-value">{{ stats?.total_positions || 0 }}</div>
      </div>

      <div class="stat-card">
        <div class="stat-label">Active Orders</div>
        <div class="stat-value">{{ stats?.active_orders || 0 }}</div>
        <div class="stat-change">Total: {{ stats?.total_orders || 0 }}</div>
      </div>
    </div>

    <!-- Recent Activity -->
    <div class="card">
      <div class="card-header">
        <h3 class="card-title">Recent Orders</h3>
        <router-link to="/orders" class="btn btn-secondary">View All</router-link>
      </div>
      <div v-if="orders.length > 0">
        <table class="table">
          <thead>
            <tr>
              <th>Market</th>
              <th>Side</th>
              <th>Price</th>
              <th>Size</th>
              <th>Status</th>
              <th>Time</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="order in orders.slice(0, 5)" :key="order.id">
              <td>{{ order.market_id }}</td>
              <td>
                <span :class="['badge', order.side_type === 'BUY' ? 'badge-success' : 'badge-danger']">
                  {{ order.side_type }}
                </span>
              </td>
              <td>${{ order.price.toFixed(3) }}</td>
              <td>{{ order.size.toFixed(1) }}</td>
              <td>
                <span :class="['badge', getStatusBadge(order.status)]">
                  {{ order.status }}
                </span>
              </td>
              <td>{{ formatDate(order.created_at) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <div v-else class="empty-state">
        <p>No recent orders</p>
      </div>
    </div>

    <!-- Token Balances -->
    <div class="card" v-if="tokenBalances && tokenBalances.tokens && tokenBalances.tokens.length > 0">
      <div class="card-header">
        <h3 class="card-title">Token Balances</h3>
        <span class="badge badge-primary">{{ tokenBalances.count }} token(s)</span>
      </div>
      <div>
        <table class="table">
          <thead>
            <tr>
              <th>Token ID</th>
              <th>Size</th>
              <th>Avg Price</th>
              <th>Current Price</th>
              <th>Value</th>
              <th>PnL %</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="token in tokenBalances.tokens" :key="token.token_id">
              <td>{{ token.token_id.substring(0, 10) }}...</td>
              <td>{{ token.size.toFixed(4) }}</td>
              <td>${{ token.avg_price.toFixed(4) }}</td>
              <td>${{ token.current_price.toFixed(4) }}</td>
              <td>${{ token.value.toFixed(2) }}</td>
              <td :class="token.pnl_percent >= 0 ? 'positive' : 'negative'">
                {{ token.pnl_percent >= 0 ? '+' : '' }}{{ token.pnl_percent.toFixed(2) }}%
              </td>
            </tr>
          </tbody>
        </table>
        <div style="padding: 1rem; border-top: 1px solid var(--border); margin-top: 1rem;">
          <strong>Total Value: ${{ tokenBalances.total_value.toFixed(2) }}</strong>
        </div>
      </div>
    </div>

    <!-- Active Positions -->
    <div class="card">
      <div class="card-header">
        <h3 class="card-title">Active Positions</h3>
        <router-link to="/positions" class="btn btn-secondary">View All</router-link>
      </div>
      <div v-if="positions.length > 0">
        <table class="table">
          <thead>
            <tr>
              <th>Market</th>
              <th>Side</th>
              <th>Size</th>
              <th>Avg Price</th>
              <th>Unrealized PnL</th>
              <th>Realized PnL</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="position in positions.slice(0, 5)" :key="position.id">
              <td>{{ position.market_id }}</td>
              <td><span class="badge badge-primary">{{ position.side || 'N/A' }}</span></td>
              <td>{{ position.size.toFixed(2) }}</td>
              <td>${{ position.avg_price.toFixed(3) }}</td>
              <td :class="position.unrealized_pnl >= 0 ? 'positive' : 'negative'">
                ${{ position.unrealized_pnl.toFixed(2) }}
              </td>
              <td :class="position.realized_pnl >= 0 ? 'positive' : 'negative'">
                ${{ position.realized_pnl.toFixed(2) }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div v-else class="empty-state">
        <p>No active positions</p>
      </div>
    </div>
  </div>
</template>

<script>
import { computed, onMounted, ref } from 'vue'
import { useStore } from 'vuex'
import api from '../api/client'

export default {
  name: 'Dashboard',
  setup() {
    const store = useStore()
    
    const stats = computed(() => store.state.stats.stats)
    const orders = computed(() => store.state.orders.orders)
    const positions = computed(() => store.state.positions.positions)
    const isRunning = computed(() => store.state.trading.isRunning)
    const loading = computed(() => store.state.trading.loading)
    const tokenBalances = ref(null)
    
    const startBot = async () => {
      try {
        await store.dispatch('trading/startTrading')
        alert('Trading bot started successfully!')
      } catch (error) {
        alert('Failed to start trading bot: ' + error.message)
      }
    }
    
    const stopBot = async () => {
      try {
        await store.dispatch('trading/stopTrading')
        alert('Trading bot stopped successfully!')
      } catch (error) {
        alert('Failed to stop trading bot: ' + error.message)
      }
    }
    
    const getStatusBadge = (status) => {
      const badges = {
        'PENDING': 'badge-warning',
        'FILLED': 'badge-success',
        'CANCELLED': 'badge-danger'
      }
      return badges[status] || 'badge-primary'
    }
    
    const formatDate = (dateStr) => {
      if (!dateStr) return 'N/A'
      const date = new Date(dateStr)
      return date.toLocaleString()
    }
    
    const fetchTokenBalances = async () => {
      try {
        const balances = await api.getTokenBalances()
        tokenBalances.value = balances
      } catch (error) {
        console.error('Error fetching token balances:', error)
        tokenBalances.value = null
      }
    }
    
    onMounted(() => {
      store.dispatch('stats/fetchStats')
      store.dispatch('orders/fetchOrders', { limit: 10 })
      store.dispatch('positions/fetchPositions')
      fetchTokenBalances()
      
      // Auto-refresh every 10 seconds
      setInterval(() => {
        store.dispatch('stats/fetchStats')
        store.dispatch('orders/fetchOrders', { limit: 10 })
        store.dispatch('positions/fetchPositions')
        fetchTokenBalances()
      }, 10000)
    })
    
    return {
      stats,
      orders,
      positions,
      isRunning,
      loading,
      tokenBalances,
      startBot,
      stopBot,
      getStatusBadge,
      formatDate
    }
  }
}
</script>

<style scoped>
.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.positive {
  color: var(--success-color);
}

.negative {
  color: var(--danger-color);
}
</style>

