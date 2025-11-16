<template>
  <div class="markets">
    <div class="markets-header">
      <h2>Markets</h2>
      <div class="controls">
        <button @click="fetchCryptoMarkets" class="btn btn-primary" :disabled="loading">
          🔄 Fetch Crypto Markets
        </button>
        <button @click="showAddModal = true" class="btn btn-success">
          ➕ Add Market
        </button>
      </div>
    </div>

    <!-- Filters -->
    <div class="card">
      <div class="filters">
        <div class="form-group">
          <label class="form-label">Category</label>
          <select v-model="filter.category" class="form-select">
            <option value="">All</option>
            <option value="crypto">Crypto</option>
            <option value="other">Other</option>
          </select>
        </div>
        <div class="form-group">
          <label class="form-label">Status</label>
          <select v-model="filter.is_active" class="form-select">
            <option value="">All</option>
            <option value="true">Active</option>
            <option value="false">Inactive</option>
          </select>
        </div>
        <button @click="applyFilters" class="btn btn-primary">Apply</button>
      </div>
    </div>

    <!-- Markets Table -->
    <div class="card">
      <div v-if="loading" class="loading">Loading markets...</div>
      <div v-else-if="markets.length > 0">
        <!-- Bulk Actions -->
        <div class="bulk-actions" style="margin-bottom: 1rem; padding: 1rem; background: var(--card-bg); border-radius: 8px;">
          <div style="display: flex; gap: 1rem; align-items: center; flex-wrap: wrap; justify-content: space-between;">
            <div style="display: flex; gap: 1rem; align-items: center; flex-wrap: wrap;">
              <span style="font-weight: bold;">Bulk Actions:</span>
              <select v-model="bulkSideToTrade" class="form-select" style="width: auto;">
                <option value="">Select Side...</option>
                <option value="YES">Set All to YES</option>
                <option value="NO">Set All to NO</option>
                <option value="BOTH">Set All to BOTH</option>
              </select>
              <button 
                @click="bulkUpdateSide" 
                class="btn btn-primary btn-sm"
                :disabled="!bulkSideToTrade"
              >
                Apply to Filtered Markets
              </button>
            </div>
            <div style="display: flex; gap: 1rem; align-items: center;">
              <label style="display: flex; align-items: center; gap: 0.5rem; cursor: pointer;">
                <input type="checkbox" v-model="showSubMarkets" />
                <span>Group Sub-Markets</span>
              </label>
              <span style="color: var(--text-secondary); font-size: 0.875rem;">
                ({{ totalMarketsCount }} market(s))
              </span>
            </div>
          </div>
        </div>
        
        <table class="table">
          <thead>
            <tr>
              <th style="width: 40px;"></th>
              <th>Question / Token Pair</th>
              <th>Side</th>
              <th>Mode</th>
              <th>Category</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <template v-for="market in markets" :key="market.id">
              <!-- Parent Market Row -->
              <tr :class="{ 'parent-row': market.sub_markets && market.sub_markets.length > 0 }">
                <td>
                  <button 
                    v-if="market.sub_markets && market.sub_markets.length > 0"
                    @click="toggleExpand(market.id)"
                    class="expand-btn"
                    :class="{ expanded: expandedMarkets.has(market.id) }"
                  >
                    {{ expandedMarkets.has(market.id) ? '▼' : '▶' }}
                  </button>
                </td>
                <td>
                  <div style="font-weight: 600;">{{ market.question }}</div>
                  <div v-if="market.sub_markets && market.sub_markets.length > 0" style="font-size: 0.875rem; color: var(--text-secondary); margin-top: 0.25rem;">
                    {{ market.sub_markets.length }} sub-market(s)
                  </div>
                </td>
                <td>
                  <span :class="['badge', 
                    market.side_to_trade === 'YES' ? 'badge-success' : 
                    market.side_to_trade === 'NO' ? 'badge-danger' : 
                    'badge-primary'
                  ]">
                    {{ market.side_to_trade }}
                  </span>
                </td>
                <td>
                  <span class="badge badge-success">{{ market.trading_mode }}</span>
                </td>
                <td>
                  <span :class="['badge', market.category === 'crypto' ? 'badge-warning' : 'badge-primary']">
                    {{ market.category }}
                  </span>
                </td>
                <td>
                  <span :class="['badge', market.is_active ? 'badge-success' : 'badge-danger']">
                    {{ market.is_active ? 'Active' : 'Inactive' }}
                  </span>
                </td>
                <td>
                  <button @click="editMarket(market)" class="btn btn-primary btn-sm">Configure</button>
                  <button @click="deleteMarket(market.id)" class="btn btn-danger btn-sm">Delete</button>
                </td>
              </tr>
              <!-- Sub-Markets Rows (shown when expanded) -->
              <template v-if="showSubMarkets && market.sub_markets && market.sub_markets.length > 0 && expandedMarkets.has(market.id)">
                <tr v-for="subMarket in market.sub_markets" :key="subMarket.id" class="sub-market-row">
                  <td></td>
                  <td>
                    <div style="padding-left: 1.5rem; color: var(--text-secondary);">
                      <span style="color: var(--info);">└─</span> {{ subMarket.answer1 }} / {{ subMarket.answer2 }}
                    </div>
                  </td>
                  <td>
                    <span :class="['badge', 
                      subMarket.side_to_trade === 'YES' ? 'badge-success' : 
                      subMarket.side_to_trade === 'NO' ? 'badge-danger' : 
                      'badge-primary'
                    ]">
                      {{ subMarket.side_to_trade }}
                    </span>
                  </td>
                  <td>
                    <span class="badge badge-success">{{ subMarket.trading_mode }}</span>
                  </td>
                  <td>
                    <span :class="['badge', subMarket.category === 'crypto' ? 'badge-warning' : 'badge-primary']">
                      {{ subMarket.category }}
                    </span>
                  </td>
                  <td>
                    <span :class="['badge', subMarket.is_active ? 'badge-success' : 'badge-danger']">
                      {{ subMarket.is_active ? 'Active' : 'Inactive' }}
                    </span>
                  </td>
                  <td>
                    <button @click="editMarket(subMarket)" class="btn btn-primary btn-sm">Configure</button>
                    <button @click="deleteMarket(subMarket.id)" class="btn btn-danger btn-sm">Delete</button>
                  </td>
                </tr>
              </template>
            </template>
          </tbody>
        </table>
      </div>
      <div v-else class="empty-state">
        <div class="empty-state-icon">📊</div>
        <p>No markets found. Click "Fetch Crypto Markets" to get started.</p>
      </div>
    </div>

    <!-- Edit Market Modal -->
    <div v-if="showEditModal" class="modal-overlay" @click="showEditModal = false">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>Configure Market</h3>
          <button @click="showEditModal = false" class="modal-close">×</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label class="form-label">
              Side to Trade
              <span class="form-help-icon" title="Which side of the market to trade">ℹ️</span>
            </label>
            <select v-model="editForm.side_to_trade" class="form-select">
              <option value="YES">YES</option>
              <option value="NO">NO</option>
              <option value="BOTH">BOTH</option>
            </select>
            <span class="form-help">
              <strong>Which token side to trade:</strong><br>
              • <strong>YES:</strong> Bot will ONLY trade YES tokens (token1). Buy/sell behavior depends on Trading Mode below.<br>
              • <strong>NO:</strong> Bot will ONLY trade NO tokens (token2). Buy/sell behavior depends on Trading Mode below.<br>
              • <strong>BOTH:</strong> Bot will trade both YES and NO tokens (default behavior).<br><br>
              <strong>Buy/Sell Logic:</strong> The actual buy/sell actions depend on your Trading Mode setting. For example, if you select YES + Market Making mode, the bot will both BUY and SELL YES tokens to profit from spreads. If you select YES + Position Building mode, the bot will only BUY YES tokens to build a position.
            </span>
          </div>

          <div class="form-group">
            <label class="form-label">
              Trading Mode
              <span class="form-help-icon" title="Trading strategy mode">ℹ️</span>
            </label>
            <select v-model="editForm.trading_mode" class="form-select">
              <option value="MARKET_MAKING">Market Making</option>
              <option value="POSITION_BUILDING">Position Building</option>
              <option value="HYBRID">Hybrid</option>
              <option value="SELL_ONLY">Sell Only</option>
            </select>
            <span class="form-help">
              <strong>Market Making:</strong> Grind profit with limit buys and sells, continuously trading both sides.<br>
              <strong>Position Building:</strong> Build a position on the designated side, hold until resolution or manual sale.<br>
              <strong>Hybrid:</strong> Build position first, then aggressively trade once target position size is met.<br>
              <strong>Sell Only:</strong> Only sell existing positions for de-risking, no new buys.
            </span>
          </div>

          <div v-if="editForm.trading_mode !== 'MARKET_MAKING' && editForm.trading_mode !== 'SELL_ONLY'" class="form-group">
            <label class="form-label">
              Target Position
              <span class="form-help-icon" title="Desired position size">ℹ️</span>
            </label>
            <input v-model.number="editForm.target_position" type="number" class="form-input" step="0.1" min="0" />
            <span class="form-help">
              The desired position size to build before switching to aggressive trading (Hybrid mode) or the target position to maintain (Position Building mode). Set to 0 to disable position limits.
            </span>
          </div>

          <div class="form-group">
            <label class="form-label">
              <input v-model="editForm.is_active" type="checkbox" />
              Active
              <span class="form-help-icon" title="Enable/disable trading for this market">ℹ️</span>
            </label>
            <span class="form-help">
              When enabled, the bot will actively trade this market. When disabled, the bot will skip this market entirely.
            </span>
          </div>

          <!-- Trading Parameters -->
          <h4>Trading Parameters</h4>
          
          <div class="form-group">
            <label class="form-label">
              Trade Size
              <span class="form-help-icon" title="Base trade size">ℹ️</span>
            </label>
            <input v-model.number="editParams.trade_size" type="number" class="form-input" step="0.1" min="0" />
            <span class="form-help">
              The base size for each trade order. This is the default amount the bot will use when placing buy/sell orders. Adjust based on your risk tolerance and market liquidity.
            </span>
          </div>

          <div class="form-group">
            <label class="form-label">
              Max Size
              <span class="form-help-icon" title="Maximum position size">ℹ️</span>
            </label>
            <input v-model.number="editParams.max_size" type="number" class="form-input" step="0.1" min="0" />
            <span class="form-help">
              Maximum position size allowed for this market. The bot will stop buying once this limit is reached. Helps manage risk and prevent over-exposure to a single market.
            </span>
          </div>

          <div class="form-group">
            <label class="form-label">
              Stop Loss Threshold (%)
              <span class="form-help-icon" title="Automatic sell trigger">ℹ️</span>
            </label>
            <input v-model.number="editParams.stop_loss_threshold" type="number" class="form-input" step="0.1" min="0" max="100" />
            <span class="form-help">
              If your position's unrealized loss reaches this percentage, the bot will automatically sell to limit losses. Set to 0 to disable stop-loss. Example: 10 means sell if position is down 10%.
            </span>
          </div>

          <div class="form-group">
            <label class="form-label">
              Take Profit Threshold (%)
              <span class="form-help-icon" title="Automatic profit-taking">ℹ️</span>
            </label>
            <input v-model.number="editParams.take_profit_threshold" type="number" class="form-input" step="0.1" min="0" max="100" />
            <span class="form-help">
              If your position's unrealized profit reaches this percentage, the bot will automatically sell to lock in profits. Set to 0 to disable take-profit. Example: 20 means sell if position is up 20%.
            </span>
          </div>

          <div class="form-group">
            <label class="form-label">
              <input v-model="editParams.order_front_running" type="checkbox" />
              Order Front Running
              <span class="form-help-icon" title="Aggressive order placement">ℹ️</span>
            </label>
            <span class="form-help">
              When enabled, the bot will place orders slightly ahead of the current best bid/ask to get priority in the order book. This increases fill probability but may reduce profit per trade. Useful for competing with other bots.
            </span>
          </div>

          <div class="form-group">
            <label class="form-label">
              Tick Improvement
              <span class="form-help-icon" title="Price improvement amount">ℹ️</span>
            </label>
            <input v-model.number="editParams.tick_improvement" type="number" class="form-input" step="0.001" min="0" max="1" />
            <span class="form-help">
              The minimum price improvement (in cents) when placing limit orders. Higher values mean better prices but lower fill probability. Example: 0.01 means place orders 1 cent better than current best bid/ask. Set to 0 for market orders.
            </span>
          </div>
        </div>
        <div class="modal-footer">
          <button @click="showEditModal = false" class="btn btn-secondary">Cancel</button>
          <button @click="saveMarket" class="btn btn-primary">Save</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { useStore } from 'vuex'
import api from '../api/client'

export default {
  name: 'Markets',
  setup() {
    const store = useStore()
    
    const markets = computed(() => store.state.markets.markets)
    const loading = computed(() => store.state.markets.loading)
    
    const showAddModal = ref(false)
    const showEditModal = ref(false)
    const selectedMarket = ref(null)
    
    const filter = ref({
      category: '',
      is_active: ''
    })
    
    const bulkSideToTrade = ref('')
    const showSubMarkets = ref(true)  // Toggle for showing sub-markets
    const expandedMarkets = ref(new Set())  // Track which parent markets are expanded
    
    const editForm = ref({
      side_to_trade: 'BOTH',
      trading_mode: 'MARKET_MAKING',
      target_position: 0,
      is_active: true
    })
    
    const editParams = ref({
      trade_size: 10,
      max_size: 100,
      stop_loss_threshold: -5,
      take_profit_threshold: 2,
      order_front_running: true,
      tick_improvement: 1
    })
    
    const applyFilters = async () => {
      try {
        const params = {}
        if (filter.value.category) params.category = filter.value.category
        if (filter.value.is_active !== '') params.is_active = filter.value.is_active === 'true'
        if (showSubMarkets.value) params.group_by_parent = true
        
        await store.dispatch('markets/fetchMarkets', params)
      } catch (error) {
        console.error('Error applying filters:', error)
      }
    }
    
    const toggleExpand = (marketId) => {
      if (expandedMarkets.value.has(marketId)) {
        expandedMarkets.value.delete(marketId)
      } else {
        expandedMarkets.value.add(marketId)
      }
    }
    
    const totalMarketsCount = computed(() => {
      let count = markets.value.length
      markets.value.forEach(market => {
        if (market.sub_markets) {
          count += market.sub_markets.length
        }
      })
      return count
    })
    
    const fetchCryptoMarkets = async () => {
      try {
        // Show loading state
        const loadingMessage = 'Fetching crypto markets from Polymarket...\nThis may take a few minutes.\n\nThe process will run in the background.\n\nContinue?'
        if (confirm(loadingMessage)) {
          const response = await store.dispatch('markets/fetchCryptoMarkets')
          
          if (response && response.status === 'fetching') {
            alert('✅ Market fetch started in background!\n\nYou can check the progress by refreshing the page.\n\nStatus endpoint: /api/markets/crypto/fetch/status')
            
            // Start polling for status
            pollFetchStatus()
          } else {
            alert('✅ Crypto markets fetched successfully!')
          }
        }
      } catch (error) {
        let errorMessage = 'Failed to fetch crypto markets.\n\n'
        
        // Provide helpful error messages
        if (error.response?.status === 409) {
          errorMessage += 'Already in Progress:\n'
          errorMessage += error.response?.data?.detail || error.message
          errorMessage += '\n\nPlease wait for the current fetch to complete.'
        } else if (error.response?.status === 400) {
          errorMessage += 'Configuration Error:\n'
          errorMessage += error.response?.data?.detail || error.message
          errorMessage += '\n\nPlease check your .env file and ensure PK and BROWSER_ADDRESS are set correctly.'
        } else if (error.response?.status === 404) {
          errorMessage += 'No Markets Found:\n'
          errorMessage += error.response?.data?.detail || error.message
          errorMessage += '\n\nThis might be a temporary API issue. Please try again later.'
        } else if (error.response?.status === 503) {
          errorMessage += 'Connection Error:\n'
          errorMessage += error.response?.data?.detail || error.message
          errorMessage += '\n\nPlease check your internet connection and Polymarket API status.'
        } else if (error.response?.status === 500) {
          errorMessage += 'Server Error:\n'
          errorMessage += error.response?.data?.detail || error.message
          errorMessage += '\n\nPlease check backend logs for more details.'
        } else {
          errorMessage += error.response?.data?.detail || error.message || 'Unknown error occurred'
        }
        
        alert(errorMessage)
        console.error('Error fetching crypto markets:', error)
      }
    }
    
    const pollFetchStatus = () => {
      // Poll fetch status every 5 seconds
      const interval = setInterval(async () => {
        try {
          const status = await api.getFetchStatus()
          console.log('Fetch status:', status)
          
          if (status.status === 'completed' || status.status === 'error') {
            clearInterval(interval)
            if (status.status === 'completed') {
              alert(`✅ Market fetch completed!\n\nSaved ${status.total_saved} markets to database.`)
              // Refresh markets list with current filters
              applyFilters()
            } else {
              alert(`❌ Market fetch failed:\n\n${status.error || 'Unknown error'}`)
            }
          }
        } catch (error) {
          console.error('Error polling fetch status:', error)
        }
      }, 5000)
      
      // Stop polling after 10 minutes
      setTimeout(() => clearInterval(interval), 600000)
    }
    
    const editMarket = async (market) => {
      selectedMarket.value = market
      editForm.value = {
        side_to_trade: market.side_to_trade,
        trading_mode: market.trading_mode,
        target_position: market.target_position,
        is_active: market.is_active
      }
      
      // Fetch trading params
      try {
        const params = await api.getMarketConfig(market.id)
        editParams.value = { ...params }
      } catch (error) {
        console.error('Error fetching params:', error)
      }
      
      showEditModal.value = true
    }
    
    const saveMarket = async () => {
      try {
        await api.updateMarket(selectedMarket.value.id, editForm.value)
        await api.updateMarketConfig(selectedMarket.value.id, editParams.value)
        showEditModal.value = false
        applyFilters()
        alert('Market updated successfully!')
      } catch (error) {
        alert('Failed to update market: ' + error.message)
      }
    }
    
    const deleteMarket = async (id) => {
      if (!confirm('Are you sure you want to delete this market?')) return
      
      try {
        await store.dispatch('markets/deleteMarket', id)
        alert('Market deleted successfully!')
      } catch (error) {
        alert('Failed to delete market: ' + error.message)
      }
    }
    
    const bulkUpdateSide = async () => {
      if (!bulkSideToTrade.value) {
        alert('Please select a side to apply')
        return
      }
      
      if (!confirm(`Set side_to_trade to "${bulkSideToTrade.value}" for all ${markets.value.length} visible markets?`)) {
        return
      }
      
      try {
        let updated = 0
        let errors = 0
        
        for (const market of markets.value) {
          try {
            await api.updateMarket(market.id, { side_to_trade: bulkSideToTrade.value })
            updated++
          } catch (error) {
            errors++
            console.error(`Error updating market ${market.id}:`, error)
          }
        }
        
        alert(`✅ Updated ${updated} markets successfully${errors > 0 ? `\n❌ ${errors} errors` : ''}`)
        
        // Refresh markets list
        applyFilters()
        bulkSideToTrade.value = ''
      } catch (error) {
        alert('Failed to update markets: ' + error.message)
      }
    }
    
    onMounted(() => {
      // Load all markets on mount with grouping enabled
      store.dispatch('markets/fetchMarkets', { group_by_parent: true })
    })
    
    // Watch for showSubMarkets changes and reload
    watch(showSubMarkets, () => {
      applyFilters()
    })
    
    return {
      markets,
      loading,
      showAddModal,
      showEditModal,
      filter,
      editForm,
      editParams,
      bulkSideToTrade,
      bulkUpdateSide,
      showSubMarkets,
      expandedMarkets,
      toggleExpand,
      totalMarketsCount,
      applyFilters,
      fetchCryptoMarkets,
      editMarket,
      saveMarket,
      deleteMarket
    }
  }
}
</script>

<style scoped>
.markets-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.controls {
  display: flex;
  gap: 1rem;
}

.filters {
  display: flex;
  gap: 1rem;
  align-items: flex-end;
}

.btn-sm {
  padding: 0.25rem 0.5rem;
  font-size: 0.875rem;
  margin-right: 0.5rem;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 8px;
  max-width: 600px;
  width: 90%;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid var(--border-color);
}

.modal-close {
  background: none;
  border: none;
  font-size: 2rem;
  cursor: pointer;
  color: var(--text-secondary);
}

.modal-body {
  padding: 1.5rem;
}

.modal-footer {
  padding: 1.5rem;
  border-top: 1px solid var(--border-color);
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
}
</style>

