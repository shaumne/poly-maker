<template>
  <div class="positions">
    <div class="positions-header">
      <h2>Positions</h2>
      <button @click="refreshPositions" class="btn btn-primary">🔄 Refresh</button>
    </div>

    <!-- Summary Stats -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-label">Total PnL</div>
        <div class="stat-value" :class="totalPnl >= 0 ? 'positive' : 'negative'">
          ${{ totalPnl.toFixed(2) }}
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-label">Open Positions</div>
        <div class="stat-value">{{ positions.length }}</div>
      </div>

      <div class="stat-card">
        <div class="stat-label">Total Unrealized PnL</div>
        <div class="stat-value" :class="unrealizedPnl >= 0 ? 'positive' : 'negative'">
          ${{ unrealizedPnl.toFixed(2) }}
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-label">Total Realized PnL</div>
        <div class="stat-value" :class="realizedPnl >= 0 ? 'positive' : 'negative'">
          ${{ realizedPnl.toFixed(2) }}
        </div>
      </div>
    </div>

    <!-- Positions Table -->
    <div class="card">
      <div v-if="loading" class="loading">Loading positions...</div>
      <div v-else-if="positions.length > 0">
        <table class="table">
          <thead>
            <tr>
              <th>Market ID</th>
              <th>Token ID</th>
              <th>Side</th>
              <th>Size</th>
              <th>Avg Price</th>
              <th>Unrealized PnL</th>
              <th>Realized PnL</th>
              <th>Total PnL</th>
              <th>Last Updated</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="position in positions" :key="position.id">
              <td>{{ position.market_id }}</td>
              <td>{{ position.token_id.slice(0, 8) }}...</td>
              <td>
                <span :class="['badge', position.side === 'YES' ? 'badge-success' : 'badge-danger']">
                  {{ position.side || 'N/A' }}
                </span>
              </td>
              <td>{{ position.size.toFixed(2) }}</td>
              <td>${{ position.avg_price.toFixed(3) }}</td>
              <td :class="position.unrealized_pnl >= 0 ? 'positive' : 'negative'">
                ${{ position.unrealized_pnl.toFixed(2) }}
              </td>
              <td :class="position.realized_pnl >= 0 ? 'positive' : 'negative'">
                ${{ position.realized_pnl.toFixed(2) }}
              </td>
              <td :class="(position.unrealized_pnl + position.realized_pnl) >= 0 ? 'positive' : 'negative'">
                ${{ (position.unrealized_pnl + position.realized_pnl).toFixed(2) }}
              </td>
              <td>{{ formatDate(position.updated_at) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <div v-else class="empty-state">
        <div class="empty-state-icon">📈</div>
        <p>No open positions</p>
      </div>
    </div>
  </div>
</template>

<script>
import { computed, onMounted } from 'vue'
import { useStore } from 'vuex'

export default {
  name: 'Positions',
  setup() {
    const store = useStore()
    
    const positions = computed(() => store.state.positions.positions)
    const loading = computed(() => store.state.positions.loading)
    
    const totalPnl = computed(() => {
      return positions.value.reduce((sum, pos) => {
        return sum + (pos.realized_pnl + pos.unrealized_pnl)
      }, 0)
    })
    
    const unrealizedPnl = computed(() => {
      return positions.value.reduce((sum, pos) => sum + pos.unrealized_pnl, 0)
    })
    
    const realizedPnl = computed(() => {
      return positions.value.reduce((sum, pos) => sum + pos.realized_pnl, 0)
    })
    
    const refreshPositions = () => {
      store.dispatch('positions/fetchPositions')
    }
    
    const formatDate = (dateStr) => {
      if (!dateStr) return 'N/A'
      const date = new Date(dateStr)
      return date.toLocaleString()
    }
    
    onMounted(() => {
      refreshPositions()
      
      // Auto-refresh every 15 seconds
      setInterval(refreshPositions, 15000)
    })
    
    return {
      positions,
      loading,
      totalPnl,
      unrealizedPnl,
      realizedPnl,
      refreshPositions,
      formatDate
    }
  }
}
</script>

<style scoped>
.positions-header {
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

