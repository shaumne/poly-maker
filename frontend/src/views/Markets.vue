<template>
  <div class="markets">
    <div class="markets-header">
      <h2>Markets</h2>
      <div class="controls">
        <button @click="showAddModal = true" class="btn btn-success">
          ➕ Add Market
        </button>
      </div>
    </div>

    <!-- Filters -->
    <div class="card">
      <div class="filters">
        <div class="form-group" style="flex: 2;">
          <label class="form-label">🔍 Search</label>
          <input 
            v-model="filter.search" 
            type="text" 
            class="form-input" 
            placeholder="Search markets by question..."
            @keyup.enter="applyFilters"
          />
        </div>
        <div class="form-group">
          <label class="form-label">Category</label>
          <select v-model="filter.category" class="form-select">
            <option value="">All</option>
            <option value="crypto">Crypto</option>
            <option value="politics">Politics</option>
            <option value="sports">Sports</option>
            <option value="economics">Economics</option>
            <option value="entertainment">Entertainment</option>
            <option value="technology">Technology</option>
            <option value="science">Science</option>
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
        <button @click="clearFilters" class="btn btn-secondary">Clear</button>
      </div>
    </div>

    <!-- Markets Table -->
    <div class="card">
      <!-- Bulk Actions Toolbar -->
      <div v-if="selectedMarkets.length > 0" class="bulk-actions-toolbar">
        <div class="bulk-actions-info">
          <strong>{{ selectedMarkets.length }}</strong> market(s) selected
        </div>
        <div class="bulk-actions-buttons">
          <button @click="bulkActivate" class="btn btn-success btn-sm">
            ✅ Activate
          </button>
          <button @click="bulkDeactivate" class="btn btn-warning btn-sm">
            ⏸ Deactivate
          </button>
          <button @click="bulkDelete" class="btn btn-danger btn-sm">
            🗑️ Delete
          </button>
          <button @click="clearSelection" class="btn btn-secondary btn-sm">
            Clear Selection
          </button>
        </div>
      </div>
      
      <div v-if="loading" class="loading">Loading markets...</div>
      <div v-else-if="markets.length > 0">
        <!-- Expand/Collapse All Controls -->
        <div class="group-controls">
          <button @click="expandAllGroups" class="btn btn-sm btn-secondary">
            ▼ Expand All
          </button>
          <button @click="collapseAllGroups" class="btn btn-sm btn-secondary">
            ▶ Collapse All
          </button>
        </div>
        
        <!-- Grouped Markets View -->
        <div class="markets-grouped">
          <div 
            v-for="(group, eventName) in groupedMarkets" 
            :key="eventName"
            class="market-group"
          >
            <!-- Group Header (Event) -->
            <div 
              class="market-group-header"
              :class="{ 
                'expanded': expandedGroups.includes(eventName),
                'standalone': eventName === 'Standalone Markets'
              }"
              @click="toggleGroup(eventName)"
            >
              <div class="group-header-left">
                <span class="group-expand-icon">
                  {{ expandedGroups.includes(eventName) ? '▼' : '▶' }}
                </span>
                <input 
                  type="checkbox" 
                  :checked="isGroupSelected(eventName)"
                  @click.stop="toggleGroupSelection(eventName)"
                  title="Select all markets in this event"
                />
                <div class="group-title">
                  <span class="group-event-icon">{{ eventName === 'Standalone Markets' ? '📋' : '🎯' }}</span>
                  <span class="group-event-name">{{ eventName }}</span>
                </div>
              </div>
              <div class="group-header-right">
                <span class="group-market-count">{{ group.length }} market(s)</span>
                <span 
                  class="group-active-count" 
                  :class="{ 'all-active': getActiveCount(group) === group.length }"
                >
                  {{ getActiveCount(group) }}/{{ group.length }} active
                </span>
                <span :class="['badge', getCategoryBadgeClass(group[0]?.category)]">
                  {{ group[0]?.category || 'other' }}
                </span>
              </div>
            </div>
            
            <!-- Expanded Sub-Markets -->
            <div v-if="expandedGroups.includes(eventName)" class="market-group-content">
              <table class="table sub-markets-table">
                <thead>
                  <tr>
                    <th style="width: 40px;"></th>
                    <th>Market Question</th>
                    <th>Side</th>
                    <th>Mode</th>
                    <th>Status</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="market in group" :key="market.id" class="sub-market-row">
                    <td>
                      <input 
                        type="checkbox" 
                        :value="market.id"
                        v-model="selectedMarkets"
                      />
                    </td>
                    <td>
                      <div class="sub-market-question">
                        {{ getQuestionWithoutPrefix(market.question) }}
                      </div>
                      <div class="sub-market-answers">
                        <span class="answer-tag yes">{{ market.answer1 || 'YES' }}</span>
                        <span class="answer-tag no">{{ market.answer2 || 'NO' }}</span>
                      </div>
                    </td>
                    <td>
                      <span class="badge badge-primary">{{ market.side_to_trade }}</span>
                    </td>
                    <td>
                      <span class="badge badge-info">{{ market.trading_mode }}</span>
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
                </tbody>
              </table>
            </div>
          </div>
        </div>
        
        <!-- Summary Stats -->
        <div class="markets-summary">
          <span>{{ Object.keys(groupedMarkets).length }} event(s)</span>
          <span class="separator">•</span>
          <span>{{ markets.length }} total market(s)</span>
          <span class="separator">•</span>
          <span>{{ markets.filter(m => m.is_active).length }} active</span>
        </div>
      </div>
      <div v-else class="empty-state">
        <div class="empty-state-icon">📊</div>
        <p>No markets found. Click "Fetch Crypto Markets" to get started.</p>
      </div>
    </div>

    <!-- Add Market Modal -->
    <div v-if="showAddModal" class="modal-overlay" @click="showAddModal = false">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>Add New Market</h3>
          <button @click="showAddModal = false" class="modal-close">×</button>
        </div>
        <div class="modal-body">
          <form @submit.prevent="addMarket">
            <div class="form-group">
              <label class="form-label">
                🔗 Polymarket URL (Auto Fill)
              </label>
              <div style="display: flex; gap: 8px;">
                <input 
                  v-model="addForm.url" 
                  type="text" 
                  class="form-input" 
                  placeholder="https://polymarket.com/event/what-price-will-bitcoin-hit-november-24-30"
                  @blur="fetchMarketFromUrl"
                />
                <button 
                  type="button" 
                  @click="fetchMarketFromUrl" 
                  class="btn btn-primary"
                  :disabled="loadingMarketFromUrl"
                  style="white-space: nowrap;"
                >
                  {{ loadingMarketFromUrl ? '⏳' : '🔍' }}
                </button>
              </div>
              <small class="form-help">Paste Polymarket URL to automatically fill market information</small>
              
              <!-- Sub-markets indicator -->
              <div v-if="hasSubMarkets && subMarketsInfo" class="sub-markets-info">
                <div class="sub-markets-alert">
                  <strong>📦 {{ subMarketsInfo.total }} markets found!</strong>
                  <p v-if="subMarketsInfo.eventTitle">Event: {{ subMarketsInfo.eventTitle }}</p>
                  <p>This event contains multiple tradeable markets.</p>
                  <button 
                    type="button" 
                    @click="showAllSubMarkets" 
                    class="btn btn-warning"
                    :disabled="loadingSubMarkets"
                    style="margin-top: 8px;"
                  >
                    {{ loadingSubMarkets ? '⏳ Loading...' : '📋 Show All Markets' }}
                  </button>
                </div>
              </div>
            </div>

            <div class="form-group">
              <label class="form-label">
                Condition ID <span class="required">*</span>
              </label>
              <input 
                v-model="addForm.condition_id" 
                type="text" 
                class="form-input" 
                placeholder="0x..."
                required
              />
              <small class="form-help">The Polymarket condition ID for this market</small>
            </div>

            <div class="form-group">
              <label class="form-label">
                Question <span class="required">*</span>
              </label>
              <input 
                v-model="addForm.question" 
                type="text" 
                class="form-input" 
                placeholder="What price will Bitcoin hit November 24-30?"
                required
              />
              <small class="form-help">The market question/title</small>
            </div>

            <div class="form-group">
              <label class="form-label">
                Token 1 ID <span class="required">*</span>
              </label>
              <input 
                v-model="addForm.token1" 
                type="text" 
                class="form-input" 
                placeholder="Token ID for YES/First outcome"
                required
              />
              <small class="form-help">Token ID for the first outcome (usually YES)</small>
            </div>

            <div class="form-group">
              <label class="form-label">
                Token 2 ID <span class="required">*</span>
              </label>
              <input 
                v-model="addForm.token2" 
                type="text" 
                class="form-input" 
                placeholder="Token ID for NO/Second outcome"
                required
              />
              <small class="form-help">Token ID for the second outcome (usually NO)</small>
            </div>

            <div class="form-group">
              <label class="form-label">Answer 1 (Optional)</label>
              <input 
                v-model="addForm.answer1" 
                type="text" 
                class="form-input" 
                placeholder="YES"
              />
              <small class="form-help">Label for the first outcome</small>
            </div>

            <div class="form-group">
              <label class="form-label">Answer 2 (Optional)</label>
              <input 
                v-model="addForm.answer2" 
                type="text" 
                class="form-input" 
                placeholder="NO"
              />
              <small class="form-help">Label for the second outcome</small>
            </div>

            <div class="form-group">
              <label class="form-label">Market Slug (Optional)</label>
              <input 
                v-model="addForm.market_slug" 
                type="text" 
                class="form-input" 
                placeholder="what-price-will-bitcoin-hit-november-24-30"
              />
              <small class="form-help">The market slug from Polymarket URL</small>
            </div>

            <div class="form-group">
              <label class="form-label">Category</label>
              <select v-model="addForm.category" class="form-select">
                <option value="crypto">Crypto</option>
                <option value="other">Other</option>
              </select>
            </div>

            <div class="form-group checkbox-group">
              <label class="checkbox-label">
                <input v-model="addForm.is_active" type="checkbox" />
                <span>Active (start trading immediately)</span>
              </label>
            </div>

            <div v-if="addError" class="alert alert-danger">
              {{ addError }}
            </div>
          </form>
        </div>
        <div class="modal-footer">
          <button @click="showAddModal = false" class="btn btn-secondary">Cancel</button>
          <button @click="addMarket" class="btn btn-primary" :disabled="adding">
            {{ adding ? 'Adding...' : 'Add Market' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Edit Market Modal -->
    <div v-if="showEditModal" class="modal-overlay" @click="showEditModal = false">
      <div class="modal-content configure-modal" @click.stop>
        <div class="modal-header">
          <h3>Configure Market: {{ selectedMarket?.question }}</h3>
          <button @click="showEditModal = false" class="modal-close">×</button>
        </div>
        <div class="modal-body">
          <!-- Market Settings Section -->
          <div class="config-section">
            <div class="section-header">
              <h4>📊 Market Settings</h4>
            </div>
            
            <div class="form-group">
              <label class="form-label">
                Side to Trade
                <span class="info-icon" @click="toggleInfo('side_to_trade')" title="Click for more info">ℹ️</span>
              </label>
              <select v-model="editForm.side_to_trade" class="form-select">
                <option value="YES">YES</option>
                <option value="NO">NO</option>
                <option value="BOTH">BOTH</option>
              </select>
              <div v-if="expandedInfo === 'side_to_trade'" class="info-box">
                <p><strong>Description:</strong> This parameter determines which side(s) of the prediction market the bot will actively trade. In prediction markets, each market has two outcomes represented by YES and NO tokens. The bot can trade on one side, the other, or both sides depending on market conditions and opportunities.</p>
                <p><strong>Options Explained:</strong></p>
                <ul>
                  <li><strong>YES:</strong> The bot will only buy YES tokens, betting that the event will occur. This is a directional bet where you believe the outcome will be true. The bot will place buy orders for YES tokens and may sell them when profitable. Use this when you have a strong conviction that the event will happen.</li>
                  <li><strong>NO:</strong> The bot will only buy NO tokens, betting that the event will not occur. This is the opposite directional bet. The bot will place buy orders for NO tokens. Use this when you believe the event will not happen.</li>
                  <li><strong>BOTH:</strong> The bot can trade on either side depending on market conditions, price movements, and opportunities. This provides maximum flexibility and allows the bot to profit from volatility and price inefficiencies on either side. The bot will analyze market conditions and choose the side with better risk/reward ratio.</li>
                </ul>
                <p><strong>Recommended:</strong> BOTH is recommended for most users as it provides maximum flexibility and allows the bot to adapt to changing market conditions. Use YES or NO only when you have a strong directional view and want the bot to focus exclusively on that side.</p>
                <p><strong>Default:</strong> BOTH</p>
                <p><strong>Strategy Considerations:</strong> When using BOTH, the bot will evaluate both sides and choose the one with better opportunities. This is particularly effective in volatile markets where prices swing between YES and NO. For stable markets with clear trends, a specific side (YES or NO) might be more appropriate if you want to build a directional position.</p>
                <p><strong>Risk Impact:</strong> Trading BOTH sides can help diversify risk, while trading a single side concentrates risk but may offer higher returns if your directional view is correct. Consider your risk tolerance and market analysis when choosing.</p>
              </div>
            </div>

            <div class="form-group">
              <label class="form-label">
                Trading Mode
                <span class="info-icon" @click="toggleInfo('trading_mode')" title="Click for more info">ℹ️</span>
              </label>
              <select v-model="editForm.trading_mode" class="form-select">
                <option value="MARKET_MAKING">Market Making</option>
                <option value="POSITION_BUILDING">Position Building</option>
                <option value="HYBRID">Hybrid</option>
                <option value="SELL_ONLY">Sell Only (Exit)</option>
              </select>
              <div v-if="expandedInfo === 'trading_mode'" class="info-box">
                <p><strong>Description:</strong> This is one of the most important parameters as it defines the core trading strategy the bot will employ for this specific market. The trading mode determines how the bot interacts with the market, what types of orders it places, and how it manages positions.</p>
                <p><strong>Modes Explained in Detail:</strong></p>
                <ul>
                  <li><strong>Market Making:</strong> The bot acts as a liquidity provider by simultaneously placing both buy and sell orders around the current market price. It profits from the bid-ask spread - buying at slightly lower prices and selling at slightly higher prices. This strategy works best in stable, liquid markets where prices don't move too dramatically. The bot continuously adjusts its orders to stay near the market price, capturing small but frequent profits. This is a lower-risk, lower-return strategy that works well in markets with high trading volume and tight spreads. The bot will maintain a relatively neutral position, profiting from the spread rather than directional moves.</li>
                  <li><strong>Position Building:</strong> The bot accumulates a position in one direction (YES or NO) over time, gradually building up to a target position size. This is used when you have a directional view on the market outcome. The bot will place buy orders strategically to build the position while trying to get good entry prices. Once the target position is reached, the bot may hold it until profit targets are met or stop losses are triggered. This strategy is higher risk but can offer higher returns if your directional view is correct. It's best for markets where you have strong conviction about the outcome.</li>
                  <li><strong>Hybrid:</strong> This mode combines both strategies - the bot makes markets (provides liquidity) while simultaneously building a directional position. It places market-making orders to capture spread profits, but with a bias toward one side to gradually build a position. This allows you to profit from both the spread and directional moves. It's more complex but can be very effective in markets where you have a moderate directional view but still want to capture spread profits. The bot balances between making markets and building position, adjusting based on market conditions.</li>
                  <li><strong>Sell Only (Exit):</strong> In this mode, the bot will ONLY place sell orders to exit existing positions. No new buy orders will be placed. This is used for de-risking when you want to exit a market completely or reduce your position size. The bot will place sell orders at favorable prices to gradually exit the position. This mode is useful when market conditions change, you need to free up capital, or you've reached your profit target and want to close out positions systematically. It's a risk-reduction strategy that allows controlled exit rather than panic selling.</li>
                </ul>
                <p><strong>Recommended:</strong> Start with Market Making for most scenarios as it's the most stable and lower-risk approach. Use Position Building when you have strong directional conviction and are willing to take on more risk for potentially higher returns. Hybrid mode is for advanced users who want to combine both approaches.</p>
                <p><strong>Default:</strong> MARKET_MAKING</p>
                <p><strong>Market Conditions:</strong> Market Making works best in liquid markets with tight spreads and moderate volatility. Position Building is better for markets with clear trends or where you have strong fundamental analysis. Hybrid works well in markets with good liquidity but also some directional movement.</p>
                <p><strong>Capital Requirements:</strong> Market Making requires less capital as positions are typically smaller and more balanced. Position Building requires more capital as you're building a larger directional position. Hybrid requires moderate capital.</p>
                <p><strong>Time Horizon:</strong> Market Making is a short-term strategy with frequent trades. Position Building is medium to long-term, holding positions until targets are met. Hybrid combines both time horizons.</p>
              </div>
            </div>

            <div v-if="editForm.trading_mode === 'POSITION_BUILDING' || editForm.trading_mode === 'HYBRID'" class="form-group">
              <label class="form-label">
                Target Position
                <span class="info-icon" @click="toggleInfo('target_position')" title="Click for more info">ℹ️</span>
              </label>
              <input v-model.number="editForm.target_position" type="number" step="0.1" class="form-input" />
              <div v-if="expandedInfo === 'target_position'" class="info-box">
                <p><strong>Description:</strong> This parameter defines the target position size (in USD) that the bot will attempt to build when using Position Building or Hybrid trading modes. The bot will gradually accumulate positions through multiple trades until it reaches this target size. This allows you to build a position over time rather than entering all at once, which can help get better average entry prices and reduce the impact of market volatility.</p>
                <p><strong>How It Works:</strong> When the bot is in Position Building or Hybrid mode, it will continuously place buy orders (for the selected side) until the total position size reaches this target. The bot will space out these orders over time, trying to get favorable entry prices. Once the target is reached, the bot will stop building the position and will manage it according to your stop loss and take profit settings.</p>
                <p><strong>Recommended:</strong> 10-50% of your allocated capital per market. For beginners, start with 10-20% to limit risk exposure. As you gain experience and confidence, you can increase to 30-50% for markets where you have strong conviction. Never allocate more than 50% of your capital to a single market to maintain proper diversification.</p>
                <p><strong>Default:</strong> 0.0 (not used in Market Making mode)</p>
                <p><strong>Important Notes:</strong></p>
                <ul>
                  <li>This parameter is only active when Trading Mode is set to POSITION_BUILDING or HYBRID. In MARKET_MAKING mode, it is ignored.</li>
                  <li>The target position should be larger than your Trade Size but smaller than your Max Size parameter.</li>
                  <li>Consider the market's liquidity - very large target positions in illiquid markets may take a long time to build and could move prices against you.</li>
                  <li>The bot will respect your Max Size limit even if Target Position is set higher.</li>
                </ul>
                <p><strong>Risk Management:</strong> Setting a target position that's too large relative to your capital can lead to over-concentration of risk. Always ensure you have enough capital to handle potential losses. Consider the worst-case scenario (stop loss triggered) and ensure you can afford that loss.</p>
                <p><strong>Example:</strong> If you have $1000 allocated to trading and set Target Position to $200, the bot will build a $200 position in this market. If you're trading 5 markets simultaneously, ensure your total target positions don't exceed your available capital.</p>
                <p><strong>Adjustment Strategy:</strong> Start with a smaller target position when testing a new market or strategy. Monitor performance and gradually increase the target as you gain confidence. If a market becomes less favorable, reduce the target position or switch back to Market Making mode.</p>
              </div>
            </div>

            <div class="form-group checkbox-group">
              <label class="checkbox-label">
                <input v-model="editForm.is_active" type="checkbox" />
                <span>Active</span>
                <span class="info-icon" @click="toggleInfo('is_active')" title="Click for more info">ℹ️</span>
              </label>
              <div v-if="expandedInfo === 'is_active'" class="info-box">
                <p><strong>Description:</strong> This toggle enables or disables trading activity for this specific market. When set to inactive (unchecked), the bot will completely ignore this market - it won't place orders, check prices, or manage positions. This is useful for temporarily pausing trading without deleting the market configuration.</p>
                <p><strong>Use Cases:</strong></p>
                <ul>
                  <li><strong>Temporary Pause:</strong> Pause trading on a market that's experiencing unusual volatility or technical issues. You can reactivate it later without losing your configuration.</li>
                  <li><strong>Market Resolution:</strong> Disable markets that are close to resolution or have already resolved. This prevents the bot from trying to trade on markets that are no longer active.</li>
                  <li><strong>Testing:</strong> Configure a market with your desired parameters, set it to inactive, and review the settings. Once satisfied, activate it to start trading.</li>
                  <li><strong>Risk Management:</strong> Quickly disable a market if you notice something wrong or want to stop trading immediately without changing other parameters.</li>
                  <li><strong>Capital Management:</strong> Temporarily disable markets to free up capital for other opportunities or to reduce overall exposure.</li>
                  <li><strong>Market Analysis:</strong> Disable trading while you analyze market conditions, review performance, or adjust your strategy.</li>
                </ul>
                <p><strong>Default:</strong> true (active)</p>
                <p><strong>Important Notes:</strong></p>
                <ul>
                  <li>When a market is inactive, existing positions are NOT automatically closed. You'll need to manually manage or close any open positions.</li>
                  <li>Inactive markets still appear in your market list, but the bot won't place new orders or manage positions.</li>
                  <li>You can toggle this setting on and off as needed without losing your configuration.</li>
                  <li>This is different from deleting a market - inactive markets retain all their settings and can be reactivated instantly.</li>
                </ul>
                <p><strong>Best Practices:</strong> Regularly review your active markets and disable those that are no longer relevant or profitable. This helps the bot focus its resources on the most promising opportunities. Consider disabling markets during major news events or when you're unsure about market direction.</p>
              </div>
            </div>
          </div>

          <!-- Position Sizing Section -->
          <div class="config-section">
            <div class="section-header">
              <h4>💰 Position Sizing</h4>
            </div>
            
            <div class="form-group">
              <label class="form-label">
                Trade Size (USD)
                <span class="info-icon" @click="toggleInfo('trade_size')" title="Click for more info">ℹ️</span>
              </label>
              <input v-model.number="editParams.trade_size" type="number" step="0.1" min="0.1" class="form-input" />
              <div v-if="expandedInfo === 'trade_size'" class="info-box">
                <p><strong>Description:</strong> Trade Size is the base amount (in USD) that the bot will use for each individual order it places. This is the standard order size that determines how much capital is committed per trade. The bot will use this size consistently unless market conditions or other parameters require adjustments.</p>
                <p><strong>How It Works:</strong> When the bot identifies a trading opportunity, it will place an order for this amount. For example, if Trade Size is set to $10, each order will be for $10 worth of tokens. The bot may place multiple orders of this size to build positions or provide liquidity, but each individual order will be this size (or smaller if approaching position limits).</p>
                <p><strong>Recommended:</strong> 5-20 USD for most markets. Start with smaller values (5-10 USD) when testing new strategies or markets. Once you've validated the strategy and are comfortable with the risk, you can increase to 15-20 USD for established strategies. For very liquid markets with tight spreads, you might use larger sizes (20-30 USD), while for volatile or less liquid markets, smaller sizes (5-10 USD) are safer.</p>
                <p><strong>Default:</strong> 10.0 USD</p>
                <p><strong>Important Constraints:</strong></p>
                <ul>
                  <li>Trade Size MUST be less than Max Size. The bot will not place orders larger than Max Size.</li>
                  <li>Trade Size should be greater than or equal to Min Size for the orders to be meaningful.</li>
                  <li>The total of all positions cannot exceed Max Size, so if Trade Size is too large relative to Max Size, you'll only be able to place a few orders.</li>
                </ul>
                <p><strong>Risk Considerations:</strong> Larger trade sizes mean more capital at risk per trade, which increases both potential profits and potential losses. If a trade goes against you, a larger trade size means a larger loss. However, larger sizes also mean fewer trades are needed to build positions, which can reduce transaction costs (gas fees) and simplify position management.</p>
                <p><strong>Market Impact:</strong> In less liquid markets, very large trade sizes can move prices against you (slippage). The bot tries to minimize this, but larger orders in illiquid markets may get worse fills. Consider market liquidity when setting trade size - liquid markets can handle larger sizes, while illiquid markets require smaller sizes.</p>
                <p><strong>Relationship with Other Parameters:</strong> Trade Size works together with Max Size (which limits total position), Min Size (which sets minimum meaningful order size), and Multiplier (which scales all sizes). The bot will place orders of Trade Size until the total position approaches Max Size, at which point it will stop or reduce order sizes.</p>
                <p><strong>Example Scenarios:</strong></p>
                <ul>
                  <li><strong>Conservative:</strong> Trade Size = $5, Max Size = $50. This allows up to 10 trades of $5 each, providing good diversification and risk control.</li>
                  <li><strong>Moderate:</strong> Trade Size = $10, Max Size = $100. This allows up to 10 trades, balancing risk and efficiency.</li>
                  <li><strong>Aggressive:</strong> Trade Size = $20, Max Size = $100. This allows only 5 trades, concentrating risk but potentially faster position building.</li>
                </ul>
                <p><strong>Adjustment Strategy:</strong> Start small and gradually increase as you gain confidence. Monitor your win rate, average profit per trade, and maximum drawdown. If you're consistently profitable with smaller sizes, consider gradually increasing. If you're experiencing losses, reduce trade size to limit risk.</p>
              </div>
            </div>

            <div class="form-group">
              <label class="form-label">
                Max Size (USD)
                <span class="info-icon" @click="toggleInfo('max_size')" title="Click for more info">ℹ️</span>
              </label>
              <input v-model.number="editParams.max_size" type="number" step="0.1" min="0.1" class="form-input" />
              <div v-if="expandedInfo === 'max_size'" class="info-box">
                <p><strong>Description:</strong> Max Size is the absolute maximum position size (in USD) that the bot is allowed to build in this market. This is a hard limit that the bot will never exceed, regardless of how profitable opportunities appear. Once the total position reaches this limit, the bot will stop placing new buy orders and will only manage the existing position (taking profits, stopping losses, or selling).</p>
                <p><strong>How It Works:</strong> The bot tracks your total position size (sum of all buy orders minus sell orders) for this market. As it places orders, it continuously checks if adding another Trade Size order would exceed Max Size. If it would, the bot will either reduce the order size or skip placing the order entirely. This ensures you never have more capital at risk in a single market than you're comfortable with.</p>
                <p><strong>Recommended:</strong> 50-200 USD depending on your capital allocation and risk tolerance. For beginners or conservative traders, start with 50-100 USD. For experienced traders with larger capital, 100-200 USD may be appropriate. The key is to ensure Max Size represents a percentage of your total capital that you're comfortable losing (considering your stop loss settings).</p>
                <p><strong>Default:</strong> 100.0 USD</p>
                <p><strong>Critical Risk Management:</strong> This is one of the most important risk control parameters. Max Size directly limits your maximum loss potential in a single market. Consider the worst-case scenario: if your stop loss is -5% and Max Size is $100, your maximum loss would be $5. If Max Size is $200, maximum loss would be $10. Always set Max Size based on:</p>
                <ul>
                  <li>Your total trading capital</li>
                  <li>Your risk tolerance (what percentage of capital you're willing to risk per market)</li>
                  <li>Your stop loss threshold (Max Size × Stop Loss % = Maximum Loss)</li>
                  <li>Number of markets you're trading simultaneously (total Max Sizes shouldn't exceed your capital)</li>
                </ul>
                <p><strong>Relationship with Trade Size:</strong> Max Size should be 5-10x your Trade Size to allow for multiple trades and position building. For example, if Trade Size is $10, Max Size of $50 allows 5 trades, while Max Size of $100 allows 10 trades. This ratio affects how quickly you can build positions and how diversified your entry prices are.</p>
                <p><strong>Capital Allocation:</strong> If you're trading multiple markets, ensure the sum of all Max Sizes doesn't exceed your available capital. For example, if you have $1000 and trade 10 markets, average Max Size should be around $100. However, you might allocate more to markets you're more confident about and less to experimental markets.</p>
                <p><strong>Position Building Impact:</strong> In Position Building or Hybrid mode, Max Size works with Target Position. The bot will build toward Target Position, but will never exceed Max Size. If Target Position is set higher than Max Size, Max Size becomes the effective limit.</p>
                <p><strong>Example Calculations:</strong></p>
                <ul>
                  <li><strong>Conservative:</strong> $1000 capital, 10 markets, Max Size = $50 each. Total max exposure = $500 (50% of capital), leaving buffer for losses.</li>
                  <li><strong>Moderate:</strong> $1000 capital, 5 markets, Max Size = $150 each. Total max exposure = $750 (75% of capital), more concentrated.</li>
                  <li><strong>Aggressive:</strong> $1000 capital, 3 markets, Max Size = $300 each. Total max exposure = $900 (90% of capital), very concentrated, higher risk.</li>
                </ul>
                <p><strong>Best Practices:</strong> Never set Max Size so high that a single market failure could significantly impact your total capital. Diversification is key - it's better to have smaller positions in more markets than large positions in few markets. Regularly review and adjust Max Size based on market performance and your evolving risk tolerance.</p>
              </div>
            </div>

            <div class="form-group">
              <label class="form-label">
                Min Size (USD)
                <span class="info-icon" @click="toggleInfo('min_size')" title="Click for more info">ℹ️</span>
              </label>
              <input v-model.number="editParams.min_size" type="number" step="0.1" min="0.1" class="form-input" />
              <div v-if="expandedInfo === 'min_size'" class="info-box">
                <p><strong>Description:</strong> Min Size defines the minimum position size (in USD) that the bot considers meaningful or worthwhile. This parameter helps filter out very small positions that may not be economically viable due to transaction costs (gas fees) and may clutter your position management. Orders or positions smaller than this threshold may be ignored, consolidated, or the bot may wait until it can build a larger position.</p>
                <p><strong>How It Works:</strong> When the bot evaluates whether to place an order or manage a position, it checks if the resulting position size would be at least Min Size. If an order would result in a position smaller than Min Size, the bot may skip it or wait for a better opportunity. This prevents the accumulation of many tiny positions that individually don't matter much but collectively can be a nuisance to manage.</p>
                <p><strong>Recommended:</strong> 1-5 USD. Should be less than Trade Size, typically 20-50% of Trade Size. For example, if Trade Size is $10, Min Size of $2-5 is appropriate. If Trade Size is $20, Min Size of $4-10 works well. The exact value depends on your gas costs and how granular you want position management to be.</p>
                <p><strong>Default:</strong> 5.0 USD</p>
                <p><strong>Gas Fee Considerations:</strong> On blockchain-based prediction markets, every transaction (buy, sell, cancel) costs gas fees. If you're making many very small trades, the gas fees can eat into or exceed your profits. Min Size helps ensure that each position is large enough that potential profits justify the gas costs. For example, if gas fees cost $0.50 per transaction and you're making $1 trades, you'd need 50% profit just to break even, which is unrealistic.</p>
                <p><strong>Position Management:</strong> Very small positions can be difficult to manage effectively. They may not move the needle on your overall PnL, but they still require monitoring and management. By setting a meaningful Min Size, you ensure that positions are large enough to matter and worth the effort to manage.</p>
                <p><strong>Relationship with Trade Size:</strong> Min Size should always be less than Trade Size. A good rule of thumb is Min Size = 20-50% of Trade Size. This ensures that a single trade of Trade Size will always exceed Min Size, but partial fills or smaller adjustments might be filtered out if they're too small.</p>
                <p><strong>Use Cases:</strong></p>
                <ul>
                  <li><strong>Gas Fee Optimization:</strong> Prevents trades that are too small to be profitable after gas fees.</li>
                  <li><strong>Position Cleanup:</strong> Helps avoid accumulating many tiny positions that are hard to track and manage.</li>
                  <li><strong>Focus on Quality:</strong> Ensures the bot focuses on meaningful positions rather than micro-trades.</li>
                  <li><strong>Reduced Complexity:</strong> Fewer, larger positions are easier to monitor and manage than many tiny ones.</li>
                </ul>
                <p><strong>Adjustment Guidelines:</strong> If you notice the bot is making too many very small trades that aren't profitable after fees, increase Min Size. If you want more granular position management and are willing to accept higher gas costs, decrease Min Size. Consider your average gas costs and typical profit margins when setting this value.</p>
                <p><strong>Example:</strong> If gas fees are $0.50 per transaction and you want to ensure at least 5% profit margin, Min Size should be at least $10 (so $0.50 is 5% of $10). However, in practice, you might set it lower (like $5) to allow for smaller positions while still filtering out truly tiny ones.</p>
              </div>
            </div>
          </div>

          <!-- Risk Management Section -->
          <div class="config-section">
            <div class="section-header">
              <h4>🛡️ Risk Management</h4>
            </div>
            
            <div class="form-group">
              <label class="form-label">
                Stop Loss Threshold (%)
                <span class="info-icon" @click="toggleInfo('stop_loss_threshold')" title="Click for more info">ℹ️</span>
              </label>
              <input v-model.number="editParams.stop_loss_threshold" type="number" step="0.1" class="form-input" />
              <div v-if="expandedInfo === 'stop_loss_threshold'" class="info-box">
                <p><strong>Description:</strong> Stop Loss Threshold is a critical risk management parameter that defines the maximum acceptable loss percentage before the bot automatically exits a position. When your unrealized profit and loss (PnL) drops to or below this threshold, the bot will immediately close the position to limit further losses. This is an essential tool for protecting your capital and preventing catastrophic losses.</p>
                <p><strong>How It Works:</strong> The bot continuously monitors your position's unrealized PnL, which is calculated as the difference between your current position value and your average entry price. If the market moves against you and the unrealized loss reaches this threshold (e.g., -5%), the bot will automatically execute a market order to close the position, accepting the loss but preventing it from getting worse. This happens regardless of your other settings or market conditions.</p>
                <p><strong>Recommended:</strong> -3% to -10% depending on your risk tolerance and market volatility. More conservative traders should use tighter stops (-3% to -5%) to limit losses quickly. Moderate traders typically use -5% to -7%. Aggressive traders who can tolerate larger swings may use -8% to -10%. The key is balancing loss limitation with avoiding premature exits due to normal market volatility.</p>
                <p><strong>Default:</strong> -5.0%</p>
                <p><strong>Critical Risk Control:</strong> This is one of the most important risk management tools. Without a stop loss, a single bad trade could wipe out significant capital. The stop loss ensures that no single position can cause catastrophic damage to your account. Always set a stop loss - never trade without one, especially when starting out.</p>
                <p><strong>Volatility Considerations:</strong> In highly volatile markets, tighter stop losses (like -3%) may get triggered frequently by normal price swings, causing premature exits. In such markets, you might need slightly wider stops (-7% to -10%) to avoid being stopped out by noise. Conversely, in stable markets, tighter stops work well. Monitor your market's typical volatility and adjust accordingly.</p>
                <p><strong>Relationship with Max Size:</strong> Your maximum potential loss is calculated as: Max Size × |Stop Loss Threshold|. For example, if Max Size is $100 and Stop Loss is -5%, your maximum loss per market is $5. This helps you understand your risk exposure. Always ensure this maximum loss is acceptable relative to your total capital.</p>
                <p><strong>Psychological Impact:</strong> Stop losses help remove emotion from trading decisions. Without them, you might hold losing positions hoping they'll recover, often leading to even larger losses. Automated stop losses enforce discipline and prevent emotional decision-making.</p>
                <p><strong>Example Scenarios:</strong></p>
                <ul>
                  <li><strong>Conservative:</strong> Stop Loss = -3%, Max Size = $100. Maximum loss = $3 per market. Good for beginners or risk-averse traders.</li>
                  <li><strong>Moderate:</strong> Stop Loss = -5%, Max Size = $100. Maximum loss = $5 per market. Balanced approach for most traders.</li>
                  <li><strong>Aggressive:</strong> Stop Loss = -10%, Max Size = $100. Maximum loss = $10 per market. Only for experienced traders comfortable with larger swings.</li>
                </ul>
                <p><strong>Adjustment Strategy:</strong> Start with a conservative stop loss (-3% to -5%) when learning. As you gain experience and understand your market's volatility patterns, you can adjust. If you're getting stopped out too frequently by normal volatility, consider widening slightly. If you're experiencing larger losses than you're comfortable with, tighten the stop loss.</p>
                <p><strong>Important Notes:</strong> Stop losses are executed as market orders, which means they may execute at slightly worse prices than the threshold due to slippage, especially in volatile or illiquid markets. Also, stop losses protect against unrealized losses - if you've already taken some profits, the stop loss applies to the remaining position value.</p>
              </div>
            </div>

            <div class="form-group">
              <label class="form-label">
                Take Profit Threshold (%)
                <span class="info-icon" @click="toggleInfo('take_profit_threshold')" title="Click for more info">ℹ️</span>
              </label>
              <input v-model.number="editParams.take_profit_threshold" type="number" step="0.1" min="0" class="form-input" />
              <div v-if="expandedInfo === 'take_profit_threshold'" class="info-box">
                <p><strong>Description:</strong> Take Profit Threshold is the profit percentage at which the bot will automatically close a position to lock in gains. When your unrealized profit and loss (PnL) reaches or exceeds this threshold (e.g., +2%), the bot will execute a market order to close the position, securing your profit. This helps ensure you actually realize profits rather than watching them disappear if the market reverses.</p>
                <p><strong>How It Works:</strong> The bot continuously monitors your position's unrealized PnL. As the market moves in your favor and your position becomes profitable, the unrealized PnL increases. Once it reaches the Take Profit Threshold, the bot automatically closes the position, converting unrealized gains into realized profits. This happens automatically, ensuring you don't miss the opportunity to lock in profits due to hesitation or inattention.</p>
                <p><strong>Recommended:</strong> 1% to 5% depending on your trading style and market conditions. Conservative traders who prefer frequent, smaller wins typically use 1-2%. Moderate traders use 2-3%. Aggressive traders seeking larger moves may use 3-5% or even higher. The key is balancing the desire to capture larger moves with the risk of giving back profits if the market reverses.</p>
                <p><strong>Default:</strong> 2.0%</p>
                <p><strong>Profit Locking Strategy:</strong> Taking profits is crucial because unrealized gains can quickly turn into losses if the market reverses. Many traders make the mistake of holding winning positions too long, watching profits evaporate. A take profit threshold enforces discipline and ensures you actually realize gains. Remember: a profit isn't real until you close the position.</p>
                <p><strong>Trade-off Analysis:</strong> There's a fundamental trade-off with take profit levels:</p>
                <ul>
                  <li><strong>Lower values (1-2%):</strong> Lock in profits more frequently, ensuring you capture gains. However, you may exit too early and miss larger moves. This is good for consistent, steady returns.</li>
                  <li><strong>Higher values (3-5%):</strong> Allow positions to run and capture larger moves. However, you risk giving back profits if the market reverses before reaching the target. This is better for markets with strong trends.</li>
                </ul>
                <p><strong>Market Condition Considerations:</strong> In volatile markets with frequent reversals, lower take profit levels (1-2%) work well to lock in gains before they disappear. In trending markets with sustained moves, higher levels (3-5%) allow you to capture more of the trend. Consider your market's typical behavior when setting this parameter.</p>
                <p><strong>Relationship with Stop Loss:</strong> The ratio of Take Profit to Stop Loss is important. A common rule of thumb is to have at least a 1:1 ratio (e.g., +2% take profit with -2% stop loss) or better (e.g., +3% take profit with -2% stop loss). This ensures that your average winning trades are at least as large as your average losing trades, which is necessary for long-term profitability.</p>
                <p><strong>Example Scenarios:</strong></p>
                <ul>
                  <li><strong>Conservative:</strong> Take Profit = 1%, Stop Loss = -3%. Captures small wins frequently, but needs high win rate to be profitable.</li>
                  <li><strong>Balanced:</strong> Take Profit = 2%, Stop Loss = -5%. Good risk/reward ratio, works well for most markets.</li>
                  <li><strong>Aggressive:</strong> Take Profit = 5%, Stop Loss = -5%. Captures larger moves but may give back profits more often.</li>
                </ul>
                <p><strong>Position Sizing Impact:</strong> With larger positions (higher Max Size), even small take profit percentages can represent significant dollar amounts. For example, a 2% take profit on a $100 position is $2, while on a $200 position it's $4. Consider your position sizes when setting take profit levels.</p>
                <p><strong>Adjustment Strategy:</strong> Start with a moderate take profit (2-3%) and monitor your results. If you find that positions frequently reach higher profits before reversing, consider increasing the threshold. If you're consistently giving back profits before reaching the target, consider lowering it. Track your average realized profit per trade to optimize this parameter.</p>
                <p><strong>Partial Profit Taking:</strong> Some advanced strategies involve taking partial profits at different levels (e.g., close 50% at +2%, let the rest run to +5%). While this bot uses a single take profit threshold, you can achieve similar results by adjusting the threshold based on market conditions or using multiple positions with different thresholds.</p>
              </div>
            </div>

            <div class="form-group">
              <label class="form-label">
                Volatility Threshold
                <span class="info-icon" @click="toggleInfo('volatility_threshold')" title="Click for more info">ℹ️</span>
              </label>
              <input v-model.number="editParams.volatility_threshold" type="number" step="1" min="0" class="form-input" />
              <div v-if="expandedInfo === 'volatility_threshold'" class="info-box">
                <p><strong>Description:</strong> Volatility Threshold defines the maximum acceptable market volatility level before the bot reduces trading activity or pauses trading to avoid excessive risk. Volatility measures how much and how quickly prices are moving - high volatility means large, rapid price swings, while low volatility means stable, predictable prices. When market volatility exceeds this threshold, the bot recognizes that conditions have become too risky and may pause trading or reduce position sizes to protect your capital.</p>
                <p><strong>How It Works:</strong> The bot continuously monitors market volatility, typically calculated as the standard deviation or range of price movements over a recent time period (e.g., the last hour or day). When volatility spikes above your threshold, it indicates that the market is experiencing unusual turbulence - perhaps due to breaking news, major events, or market manipulation. In such conditions, normal trading strategies may not work well, and the risk of large, unexpected losses increases. The bot responds by either pausing new trades or reducing position sizes until volatility subsides.</p>
                <p><strong>Recommended:</strong> 30-70 depending on your risk tolerance and trading style. Lower values (30-50) are more conservative and will pause trading sooner when volatility increases. This protects capital but may cause you to miss opportunities in volatile but potentially profitable markets. Higher values (60-70) allow trading in more volatile conditions, accepting higher risk for potentially higher rewards. Moderate traders typically use 40-60.</p>
                <p><strong>Default:</strong> 50.0</p>
                <p><strong>Volatility Measurement:</strong> Volatility is typically measured as the percentage price movement over a time period. For example, if prices swing between $0.45 and $0.55 over an hour, that's roughly 10% volatility. The bot may use various methods to calculate volatility, including standard deviation, price range, or rate of change. Higher numbers indicate more volatile markets.</p>
                <p><strong>Risk Management:</strong> High volatility markets are dangerous because prices can move rapidly against you, potentially triggering stop losses before you can react, or causing slippage that makes fills worse than expected. The volatility threshold acts as an early warning system, helping you avoid trading during dangerous conditions. This is especially important for market making strategies, which rely on relatively stable prices.</p>
                <p><strong>Market Conditions:</strong> Different markets have different baseline volatility levels. Crypto markets, for example, tend to be more volatile than traditional prediction markets. News-driven markets can experience sudden volatility spikes. Consider your market's typical volatility when setting this threshold - you want it high enough to allow normal trading but low enough to protect against dangerous conditions.</p>
                <p><strong>Adjustment Strategy:</strong> Start with the default (50) and monitor how often the bot pauses due to volatility. If it's pausing too frequently during normal market conditions, increase the threshold. If you're experiencing large losses during volatile periods, decrease it. Track your performance during high volatility periods to find the optimal setting.</p>
                <p><strong>Example:</strong> If volatility threshold is set to 50 and the market experiences a sudden 8% price swing due to breaking news, the bot will detect this high volatility and may pause trading until conditions stabilize. This prevents you from placing orders during chaotic conditions where execution quality is poor and risk is elevated.</p>
              </div>
            </div>

            <div class="form-group">
              <label class="form-label">
                Max Spread (%)
                <span class="info-icon" @click="toggleInfo('max_spread')" title="Click for more info">ℹ️</span>
              </label>
              <input v-model.number="editParams.max_spread" type="number" step="0.1" min="0" class="form-input" />
              <div v-if="expandedInfo === 'max_spread'" class="info-box">
                <p><strong>Description:</strong> Max Spread is the maximum acceptable bid-ask spread percentage that the bot will tolerate before refusing to place orders. The spread is the difference between the highest price someone is willing to pay (bid) and the lowest price someone is willing to sell at (ask), expressed as a percentage of the mid price. Wider spreads indicate lower liquidity, higher trading costs, and potentially worse execution quality. This parameter ensures the bot only trades in markets with reasonable liquidity.</p>
                <p><strong>How It Works:</strong> Before placing any order, the bot calculates the current bid-ask spread. If the spread exceeds Max Spread, the bot will skip placing orders in that market, waiting for better conditions or moving to other markets. For example, if Max Spread is 5% and the current spread is 7%, the bot won't trade. If the spread is 3%, trading proceeds normally. This protects you from trading in illiquid markets where you'll get poor fills and pay high implicit costs.</p>
                <p><strong>Recommended:</strong> 2% to 8% depending on your strategy and market selection. Tighter spreads (2-4%) ensure better execution quality and lower trading costs, but limit you to only the most liquid markets. This is good for market making strategies that rely on tight spreads. Wider spreads (6-8%) allow trading in less liquid markets, expanding opportunities but accepting higher costs. Moderate traders typically use 4-6%.</p>
                <p><strong>Default:</strong> 5.0%</p>
                <p><strong>Spread Impact on Profits:</strong> The spread represents an immediate cost when trading. If you buy at the ask and immediately sell at the bid, you lose the spread. For market makers, wider spreads can mean more profit potential, but only if you can actually get fills at good prices. For position builders, wider spreads mean worse entry prices. Always consider that wider spreads reduce your effective profit margin.</p>
                <p><strong>Liquidity Relationship:</strong> Spread and liquidity are inversely related - liquid markets have tight spreads (1-3%), while illiquid markets have wide spreads (5%+). Very wide spreads (10%+) often indicate extremely low liquidity where large orders can move prices significantly. Max Spread helps you avoid these dangerous markets.</p>
                <p><strong>Market Making Considerations:</strong> For market making strategies, you want to profit from the spread, so you need markets with reasonable spreads that you can capture. However, if spreads are too wide, it may indicate low activity where your orders won't fill. A Max Spread of 3-5% works well for market making.</p>
                <p><strong>Position Building Considerations:</strong> For position building, you want to enter at good prices, so tighter spreads are better. However, you may need to accept wider spreads in less liquid markets if you have strong directional conviction. A Max Spread of 5-8% may be acceptable for position building if you're confident in your view.</p>
                <p><strong>Dynamic Nature:</strong> Spreads change constantly based on market activity, news, and time of day. A market might have a 2% spread most of the time but spike to 10% during low activity periods. Max Spread ensures you don't trade during these unfavorable periods.</p>
                <p><strong>Example:</strong> If Max Spread is 5% and a market has a bid of $0.48 and ask of $0.52, the spread is 8% (calculated as (0.52-0.48)/0.50 = 8%). Since 8% > 5%, the bot won't place orders. If the spread tightens to 3%, trading resumes.</p>
              </div>
            </div>

            <div class="form-group">
              <label class="form-label">
                Spread Threshold
                <span class="info-icon" @click="toggleInfo('spread_threshold')" title="Click for more info">ℹ️</span>
              </label>
              <input v-model.number="editParams.spread_threshold" type="number" step="0.01" min="0" max="1" class="form-input" />
              <div v-if="expandedInfo === 'spread_threshold'" class="info-box">
                <p><strong>Description:</strong> Spread Threshold is the minimum bid-ask spread (expressed as a decimal, where 0.05 = 5%) required for the bot to consider placing orders. This is the opposite of Max Spread - while Max Spread sets an upper limit (don't trade if spread is too wide), Spread Threshold sets a lower limit (don't trade if spread is too tight). Markets with spreads below this threshold may be too competitive or too efficient to profit from, especially for market making strategies.</p>
                <p><strong>How It Works:</strong> The bot checks the current spread before placing orders. If the spread is below Spread Threshold, the bot may skip trading, assuming that the spread is too tight to capture meaningful profits after accounting for gas fees and execution costs. For example, if Spread Threshold is 0.05 (5%) and the current spread is 0.02 (2%), the bot won't trade. If the spread is 0.06 (6%), trading proceeds. This ensures you only trade when there's sufficient profit potential.</p>
                <p><strong>Recommended:</strong> 0.02 to 0.10 (2% to 10%) depending on your strategy. Lower values (0.02-0.05) allow trading in tight, competitive markets where spreads are small but volume is high. This works if you can capture many small profits. Higher values (0.05-0.10) focus on markets with wider spreads and better profit potential per trade, but may have lower volume. Moderate traders typically use 0.03-0.06.</p>
                <p><strong>Default:</strong> 0.05 (5%)</p>
                <p><strong>Market Making Strategy:</strong> For market making, you need spreads wide enough to profit from after costs. If spreads are too tight (e.g., 1%), you may not be able to capture enough profit to cover gas fees and make it worthwhile. Spread Threshold ensures you only make markets when there's sufficient spread to profit from. A threshold of 0.03-0.05 (3-5%) is typical for market making.</p>
                <p><strong>Profitability Calculation:</strong> To determine if a spread is profitable, consider: Spread % - Gas Fees % - Slippage % - Risk Buffer = Net Profit %. For example, if spread is 3%, gas fees are 0.5%, slippage is 0.5%, and you want 1% net profit, you need at least a 2% spread. Set Spread Threshold accordingly.</p>
                <p><strong>Relationship with Max Spread:</strong> These two parameters work together to define an acceptable spread range. Spread Threshold sets the minimum (e.g., 2%) and Max Spread sets the maximum (e.g., 8%). The bot will only trade when the spread is between these two values. This creates a "sweet spot" where markets are liquid enough (not too wide) but profitable enough (not too tight).</p>
                <p><strong>Competitive Markets:</strong> Very tight spreads often indicate highly competitive markets with many market makers. While these markets may be liquid, they can be difficult to profit from because competition has compressed spreads. Spread Threshold helps you avoid these overly competitive markets unless you have a significant advantage.</p>
                <p><strong>Gas Fee Considerations:</strong> On blockchain-based markets, every trade costs gas fees. If spreads are too tight, the gas fees can eat up all or most of the potential profit. Spread Threshold should be set high enough that profits exceed gas costs. For example, if gas fees cost 0.5% per round trip, you need at least a 1-2% spread just to break even, so Spread Threshold should be at least 0.02-0.03.</p>
                <p><strong>Example:</strong> If Spread Threshold is 0.05 (5%) and Max Spread is 0.08 (8%), the bot will only trade when spreads are between 5% and 8%. A market with a 3% spread is too tight (below threshold), a market with a 6% spread is acceptable, and a market with a 10% spread is too wide (above max).</p>
              </div>
            </div>
          </div>

          <!-- Order Management Section -->
          <div class="config-section">
            <div class="section-header">
              <h4>⚙️ Order Management</h4>
            </div>
            
            <div class="form-group">
              <label class="form-label">
                Tick Size
                <span class="info-icon" @click="toggleInfo('tick_size')" title="Click for more info">ℹ️</span>
              </label>
              <input v-model.number="editParams.tick_size" type="number" step="0.001" min="0.001" class="form-input" />
              <div v-if="expandedInfo === 'tick_size'" class="info-box">
                <p><strong>Description:</strong> Tick Size is the minimum price increment allowed for orders in this market. All order prices must be exact multiples of this tick size - you cannot place orders at prices between ticks. This is typically set by the exchange or market protocol and represents the smallest unit by which prices can change. For example, if tick size is 0.01, valid prices are $0.50, $0.51, $0.52, etc., but not $0.505 or $0.5125.</p>
                <p><strong>How It Works:</strong> When the bot calculates order prices, it rounds them to the nearest valid tick. If tick size is 0.01 and the calculated price is $0.4567, it will be rounded to $0.46 (or $0.45, depending on rounding rules). This ensures all orders conform to the market's price granularity requirements. Orders placed at invalid prices (not multiples of tick size) will be rejected by the exchange.</p>
                <p><strong>Recommended:</strong> 0.01 for most Polymarket markets, which allows prices in 1-cent increments (e.g., $0.50, $0.51, $0.52). Some markets may use finer granularity like 0.001 (allowing $0.500, $0.501, $0.502) for more precise pricing, or coarser granularity like 0.05 (allowing $0.50, $0.55, $0.60) for simpler markets. Always check the specific market's actual tick size requirements - you can usually find this in the market details or by observing the order book prices.</p>
                <p><strong>Default:</strong> 0.01</p>
                <p><strong>Critical Importance:</strong> Using an incorrect tick size will cause all your orders to be rejected by the exchange. This is one of the most common configuration errors. The bot will attempt to round prices correctly, but if the tick size setting is wrong, the rounding will be incorrect and orders will fail. Always verify the tick size matches the market's actual requirements.</p>
                <p><strong>Finding the Correct Tick Size:</strong> To determine a market's tick size, look at the order book and observe the price increments. If prices are $0.50, $0.51, $0.52, tick size is 0.01. If prices are $0.500, $0.501, $0.502, tick size is 0.001. If prices are $0.50, $0.55, $0.60, tick size is 0.05. You can also check the market's API documentation or contract specifications.</p>
                <p><strong>Impact on Order Placement:</strong> Smaller tick sizes (like 0.001) allow more precise price placement, which can be advantageous for competitive market making where small price differences matter. Larger tick sizes (like 0.05) simplify pricing but reduce flexibility. The bot will work with any tick size, but precision matters more in competitive markets.</p>
                <p><strong>Relationship with Tick Improvement:</strong> Tick Improvement is measured in number of ticks. If tick size is 0.01 and tick improvement is 2, the bot improves prices by 0.02 (2 × 0.01). If tick size is 0.001 and tick improvement is 2, the improvement is 0.002. The tick size determines the granularity of price improvements.</p>
                <p><strong>Example:</strong> If tick size is 0.01 and the market price is $0.50, valid order prices are $0.48, $0.49, $0.50, $0.51, $0.52, etc. The bot cannot place an order at $0.495 - it must round to $0.49 or $0.50. If you set tick size incorrectly to 0.001 when the market actually uses 0.01, orders at prices like $0.501 will be rejected.</p>
              </div>
            </div>

            <div class="form-group">
              <label class="form-label">
                Tick Improvement
                <span class="info-icon" @click="toggleInfo('tick_improvement')" title="Click for more info">ℹ️</span>
              </label>
              <input v-model.number="editParams.tick_improvement" type="number" step="1" min="0" max="5" class="form-input" />
              <div v-if="expandedInfo === 'tick_improvement'" class="info-box">
                <p><strong>Description:</strong> Tick Improvement is the number of price ticks (price increments) by which the bot improves order prices to increase the probability of execution. For buy orders, "improving" means placing the order at a lower price (more attractive to sellers). For sell orders, "improving" means placing at a higher price (more attractive to buyers). This parameter balances the trade-off between execution probability and profit per trade.</p>
                <p><strong>How It Works:</strong> When placing a buy order, instead of placing it at the current best bid, the bot places it a certain number of ticks lower (better price for you). For example, if the best bid is $0.50 and tick improvement is 2, the bot might place the buy order at $0.48 (2 ticks lower, assuming tick size is 0.01). This makes your order more attractive and likely to fill, but you get a better entry price. Similarly, for sell orders, the bot places them higher than the current best ask, making them more likely to fill but at a better exit price for you.</p>
                <p><strong>Recommended:</strong> 1-3 ticks depending on your priority. Higher values (2-3) significantly improve execution probability - your orders are more likely to fill because they're more competitive. However, this reduces your profit per trade because you're getting better prices (lower buys, higher sells). Lower values (0-1) maximize potential profit per trade but may result in fewer fills, especially in competitive markets. Moderate traders typically use 1-2 ticks.</p>
                <p><strong>Default:</strong> 1 tick</p>
                <p><strong>Range:</strong> 0 to 5 ticks. Higher values are more aggressive in getting orders filled but sacrifice profit margin. Setting to 0 means no price improvement - orders are placed at market prices, maximizing profit potential but reducing fill probability.</p>
                <p><strong>Execution vs Profit Trade-off:</strong> This is a fundamental trade-off in trading:</p>
                <ul>
                  <li><strong>Low tick improvement (0-1):</strong> Orders are placed at or near market prices, maximizing profit if they fill. However, in competitive markets, these orders may sit unfilled while other traders' more aggressive orders execute. Good for liquid markets with less competition.</li>
                  <li><strong>High tick improvement (2-3):</strong> Orders are placed at significantly better prices, making them very attractive and likely to fill quickly. However, you're leaving money on the table - you could have gotten better prices. Good for competitive markets or when you prioritize execution speed over maximum profit.</li>
                </ul>
                <p><strong>Market Conditions:</strong> In highly competitive markets with many bots, higher tick improvement (2-3) may be necessary to get fills at all. In less competitive or more liquid markets, lower values (0-1) work well. Monitor your fill rate - if orders aren't filling, increase tick improvement. If they're filling easily, you might reduce it to capture more profit.</p>
                <p><strong>Relationship with Tick Size:</strong> The actual price improvement in dollars depends on tick size. If tick size is 0.01 and tick improvement is 2, you improve by $0.02. If tick size is 0.001 and tick improvement is 2, you improve by $0.002. Consider both parameters together when setting your strategy.</p>
                <p><strong>Market Making Strategy:</strong> For market making, you want to provide liquidity while still getting fills. Moderate tick improvement (1-2) works well - you're competitive enough to get fills but not so aggressive that you give away all your profit. Too high (3+) and you may not profit from the spread. Too low (0) and you may not get fills in competitive markets.</p>
                <p><strong>Position Building Strategy:</strong> For position building, you want good entry prices. Lower tick improvement (0-1) helps you get better entries, but you may need to wait longer for fills. If you need to build positions quickly, higher values (2-3) ensure faster execution.</p>
                <p><strong>Example:</strong> If tick size is 0.01, tick improvement is 2, and you want to buy at market price $0.50, the bot places the buy order at $0.48 (2 ticks lower). This order is more attractive to sellers and more likely to fill, but you're paying $0.48 instead of potentially getting $0.49 or $0.50. The trade-off is execution certainty vs. price optimization.</p>
              </div>
            </div>

            <div class="form-group">
              <label class="form-label">
                Quick Cancel Threshold
                <span class="info-icon" @click="toggleInfo('quick_cancel_threshold')" title="Click for more info">ℹ️</span>
              </label>
              <input v-model.number="editParams.quick_cancel_threshold" type="number" step="0.01" min="0" max="1" class="form-input" />
              <div v-if="expandedInfo === 'quick_cancel_threshold'" class="info-box">
                <p><strong>Description:</strong> Quick Cancel Threshold is the price movement percentage (expressed as a decimal, where 0.01 = 1%) that triggers immediate cancellation of existing orders and placement of new orders at updated prices. When the market price moves by more than this threshold from when your orders were placed, the bot recognizes that your orders have become stale (outdated) and cancels them to place fresh orders at current market prices. This ensures your orders remain relevant and competitive.</p>
                <p><strong>How It Works:</strong> The bot continuously monitors market price movements. When it detects that prices have moved by more than Quick Cancel Threshold (e.g., 1%), it immediately cancels all existing orders for that market and places new orders at prices adjusted to the current market conditions. For example, if you placed a buy order at $0.50 and the market moves to $0.48 (a 4% move), and your threshold is 0.01 (1%), the bot will cancel the old order and place a new one at the updated price. This keeps your orders competitive and prevents them from becoming irrelevant.</p>
                <p><strong>Recommended:</strong> 0.01 to 0.05 (1% to 5%) depending on market volatility and your gas cost tolerance. Lower values (0.01-0.02) keep orders very current and relevant, ensuring they're always competitive. However, this may cause frequent cancellations in volatile markets, increasing gas costs. Higher values (0.03-0.05) reduce cancellation frequency and gas costs, but orders may become slightly stale before being updated. Moderate traders typically use 0.02-0.03.</p>
                <p><strong>Default:</strong> 0.01 (1%)</p>
                <p><strong>Stale Order Problem:</strong> In fast-moving markets, orders can become stale quickly. An order placed at $0.50 becomes less relevant if the market moves to $0.48 - it's now 4% away from current prices and unlikely to fill. Stale orders waste capital (locked in unfillable orders) and miss trading opportunities. Quick Cancel Threshold solves this by automatically refreshing orders when they become outdated.</p>
                <p><strong>Gas Cost Considerations:</strong> Every cancellation and new order placement costs gas fees on blockchain-based markets. If you set Quick Cancel Threshold too low (e.g., 0.005 = 0.5%), you may cancel and replace orders very frequently, leading to high gas costs that eat into profits. In volatile markets, this could mean dozens of cancellations per hour. Balance the need for current orders with gas cost efficiency.</p>
                <p><strong>Volatility Impact:</strong> In highly volatile markets, prices move frequently and significantly. A low threshold (0.01) will trigger many cancellations, keeping orders current but increasing costs. A higher threshold (0.03-0.05) reduces cancellations but may allow orders to become slightly stale. Consider your market's typical volatility when setting this parameter.</p>
                <p><strong>Market Making Strategy:</strong> For market making, you need orders to be competitive and current. However, excessive cancelling can be costly. A threshold of 0.02-0.03 (2-3%) works well - orders stay relevant without excessive gas costs. In very liquid, stable markets, you might use 0.01. In volatile markets, 0.03-0.05 may be more cost-effective.</p>
                <p><strong>Execution Quality:</strong> Keeping orders current improves execution quality - you're more likely to get fills at good prices. However, there's a diminishing return. Cancelling every 0.5% move may not be worth the gas costs if 1-2% moves are acceptable. Find the balance where orders are current enough to be effective but not so current that gas costs become prohibitive.</p>
                <p><strong>Example:</strong> If Quick Cancel Threshold is 0.02 (2%) and you place a buy order at $0.50:</p>
                <ul>
                  <li>Market moves to $0.49 (2% move) - threshold reached, order cancelled and replaced</li>
                  <li>Market moves to $0.495 (1% move) - below threshold, order remains</li>
                  <li>Market moves to $0.48 (4% move) - well above threshold, order definitely cancelled and replaced</li>
                </ul>
                <p><strong>Adjustment Strategy:</strong> Start with the default (0.01) and monitor your cancellation frequency and gas costs. If you're cancelling too frequently and gas costs are high, increase the threshold. If orders are becoming stale and missing opportunities, decrease it. Track the balance between order relevance and gas costs to find your optimal setting.</p>
              </div>
            </div>

            <div class="form-group checkbox-group">
              <label class="checkbox-label">
                <input v-model="editParams.order_front_running" type="checkbox" />
                <span>Order Front Running</span>
                <span class="info-icon" @click="toggleInfo('order_front_running')" title="Click for more info">ℹ️</span>
              </label>
              <div v-if="expandedInfo === 'order_front_running'" class="info-box">
                <p><strong>Description:</strong> Order Front Running is an advanced competitive feature that attempts to place orders ahead of competing bots by predicting and reacting to market movements before they happen. When enabled, the bot monitors market conditions, order book changes, and trading patterns to anticipate price movements, then places orders slightly ahead of expected moves. This gives you a competitive advantage by getting better prices and execution priority compared to bots that simply react to current market conditions.</p>
                <p><strong>How It Works:</strong> The bot uses various signals to predict price movements: order book imbalances (more buy orders than sell orders suggests upward pressure), recent price trends, trading volume patterns, and other market microstructure signals. When it detects conditions suggesting an imminent price move, it places orders at prices that will be favorable once the move occurs. For example, if it detects upward pressure, it might place a buy order slightly above current prices, anticipating that prices will rise to that level. This allows you to "front run" the move and get better execution than reactive bots.</p>
                <p><strong>Recommended:</strong> Enable for competitive markets where execution speed and price priority matter, especially in liquid markets with many competing bots. In such environments, being slightly ahead can make a significant difference in profitability. Disable if you prefer simpler, more predictable behavior, or if you're trading in less competitive markets where this feature isn't necessary. For beginners, you might start with it disabled to understand basic bot behavior first.</p>
                <p><strong>Default:</strong> true (enabled)</p>
                <p><strong>Competitive Advantage:</strong> In highly competitive markets with many bots, small advantages matter. Being able to place orders slightly ahead of moves can mean the difference between getting fills and missing opportunities, or between profitable and unprofitable trades. This feature is most valuable when competing against other algorithmic traders.</p>
                <p><strong>Gas Cost Impact:</strong> Front running requires more frequent order placement and cancellation as the bot reacts to market signals. This can increase gas costs compared to simpler strategies. The bot may place and cancel orders more often as it adjusts to predicted movements. Consider whether the competitive advantage justifies the additional costs.</p>
                <p><strong>Execution Speed Requirements:</strong> Front running is most effective when you have fast execution - the ability to place orders quickly after detecting signals. If your execution is slow (due to network latency, slow blockchain, etc.), the advantage diminishes as other bots may react before your orders are placed. This feature works best with low-latency infrastructure.</p>
                <p><strong>Market Conditions:</strong> This feature is most effective in:</p>
                <ul>
                  <li>Liquid markets with high trading volume and many participants</li>
                  <li>Markets with clear patterns and predictable microstructure</li>
                  <li>Competitive environments with many bots where small advantages matter</li>
                </ul>
                <p>It's less effective in:</p>
                <ul>
                  <li>Illiquid markets with low activity</li>
                  <li>Highly unpredictable or random markets</li>
                  <li>Markets with few competitors where simple strategies work fine</li>
                </ul>
                <p><strong>Risk Considerations:</strong> Front running involves prediction, which means it's not always correct. If predictions are wrong, you might place orders at unfavorable prices or cancel orders that would have filled. This can reduce profitability compared to simpler reactive strategies. Monitor performance to ensure the feature is actually helping.</p>
                <p><strong>Complexity:</strong> This feature adds complexity to the bot's behavior, making it harder to predict exactly when and why orders are placed. If you prefer transparency and predictability, disable this feature. If you're comfortable with more sophisticated behavior and want maximum competitiveness, enable it.</p>
                <p><strong>Performance Monitoring:</strong> Track your performance with this feature enabled vs. disabled. Compare metrics like fill rate, average profit per trade, and gas costs. If front running is improving results, keep it enabled. If it's increasing costs without improving execution, consider disabling it.</p>
                <p><strong>Example:</strong> The bot detects that the order book has many more buy orders than sell orders, suggesting upward price pressure. Instead of waiting for prices to actually rise, it immediately places a buy order slightly above current prices. When prices do rise (as predicted), your order is already in place and executes at a favorable price, ahead of bots that only react after the price move occurs.</p>
              </div>
            </div>
          </div>

          <!-- Timing Section -->
          <div class="config-section">
            <div class="section-header">
              <h4>⏱️ Timing</h4>
            </div>
            
            <div class="form-group">
              <label class="form-label">
                Sleep Period (hours)
                <span class="info-icon" @click="toggleInfo('sleep_period')" title="Click for more info">ℹ️</span>
              </label>
              <input v-model.number="editParams.sleep_period" type="number" step="0.1" min="0.1" class="form-input" />
              <div v-if="expandedInfo === 'sleep_period'" class="info-box">
                <p><strong>Description:</strong> Sleep Period is the time interval (in hours) that the bot waits between checking market conditions, evaluating trading opportunities, and placing new orders. This parameter controls the frequency and responsiveness of the bot's trading activity. After the bot completes a cycle of checking markets and placing orders, it enters a "sleep" period before the next cycle begins. This balances responsiveness to market changes with computational efficiency and resource usage.</p>
                <p><strong>How It Works:</strong> The bot operates in cycles: (1) Check market conditions, prices, and positions, (2) Evaluate trading opportunities based on your parameters, (3) Place, update, or cancel orders as needed, (4) Sleep for the specified period, (5) Repeat. During the sleep period, the bot is inactive and doesn't monitor markets or place orders. This periodic approach is more efficient than continuous monitoring while still maintaining reasonable responsiveness.</p>
                <p><strong>Recommended:</strong> 0.5 to 2 hours depending on market activity and your priorities. Shorter periods (0.5-1 hour) allow more frequent trading activity, making the bot more responsive to market changes and opportunities. This is good for active, fast-moving markets where conditions change quickly. Longer periods (1-2 hours) reduce computational load and resource usage, and may be sufficient for slower-moving markets. Moderate traders typically use 0.5-1 hour.</p>
                <p><strong>Default:</strong> 1.0 hour</p>
                <p><strong>Responsiveness vs Efficiency Trade-off:</strong> There's a fundamental trade-off:</p>
                <ul>
                  <li><strong>Shorter sleep periods (0.5-1 hour):</strong> More responsive to market changes, can catch opportunities faster, and keeps orders more current. However, this increases computational load, resource usage, and potentially gas costs (if it leads to more frequent order updates). Good for active traders and volatile markets.</li>
                  <li><strong>Longer sleep periods (1-2 hours):</strong> More efficient, uses fewer resources, and may reduce unnecessary activity. However, the bot is less responsive and may miss short-lived opportunities or react slowly to market changes. Good for passive trading and stable markets.</li>
                </ul>
                <p><strong>Market Activity Considerations:</strong> More active, volatile markets benefit from shorter sleep periods because conditions change rapidly and opportunities appear and disappear quickly. Slower, more stable markets can work well with longer sleep periods since conditions don't change as frequently. Consider your market's typical activity level when setting this parameter.</p>
                <p><strong>Computational Resources:</strong> Shorter sleep periods mean the bot runs more frequently, using more CPU, memory, and potentially API rate limits. If you're running the bot on limited resources or have API rate limits, longer sleep periods help. If you have ample resources, shorter periods provide better responsiveness.</p>
                <p><strong>Gas Cost Impact:</strong> More frequent checks may lead to more frequent order updates and cancellations, increasing gas costs. However, this isn't always the case - if market conditions are stable, frequent checks won't necessarily lead to more orders. Monitor your gas costs relative to sleep period to find the optimal balance.</p>
                <p><strong>Opportunity Cost:</strong> Longer sleep periods mean the bot may miss opportunities that appear and disappear between cycles. For example, if a profitable opportunity appears 10 minutes after a check and disappears 30 minutes later, a 2-hour sleep period will miss it, while a 0.5-hour period might catch it. Consider how quickly opportunities appear and disappear in your markets.</p>
                <p><strong>Position Management:</strong> Shorter sleep periods allow more frequent position monitoring and management. If you have active positions that need monitoring (approaching stop loss or take profit), shorter periods ensure faster response. For positions that are well within safe ranges, longer periods may be sufficient.</p>
                <p><strong>Example Scenarios:</strong></p>
                <ul>
                  <li><strong>Active Trading:</strong> Sleep Period = 0.5 hours. Bot checks markets every 30 minutes, very responsive to changes, good for volatile markets.</li>
                  <li><strong>Moderate Trading:</strong> Sleep Period = 1.0 hour. Bot checks hourly, balanced approach for most markets.</li>
                  <li><strong>Passive Trading:</strong> Sleep Period = 2.0 hours. Bot checks every 2 hours, more efficient, suitable for stable markets or when you want minimal activity.</li>
                </ul>
                <p><strong>Adjustment Strategy:</strong> Start with the default (1 hour) and monitor performance. If you're missing opportunities or need faster response, decrease the sleep period. If the bot is checking too frequently without finding opportunities, or if resource usage is a concern, increase it. Track the relationship between sleep period and trading results to optimize.</p>
              </div>
            </div>

            <div class="form-group">
              <label class="form-label">
                Position Patience (hours)
                <span class="info-icon" @click="toggleInfo('position_patience')" title="Click for more info">ℹ️</span>
              </label>
              <input v-model.number="editParams.position_patience" type="number" step="1" min="1" class="form-input" />
              <div v-if="expandedInfo === 'position_patience'" class="info-box">
                <p><strong>Description:</strong> Position Patience is the maximum time (in hours) the bot will hold a position before forcing an exit, regardless of whether the position is profitable or losing. This is a time-based exit mechanism that prevents the bot from holding positions indefinitely in stagnant markets where prices aren't moving. After this time period elapses, the bot will automatically close the position, freeing up capital for new opportunities and preventing capital from being tied up in unproductive positions.</p>
                <p><strong>How It Works:</strong> When the bot opens a position, it starts a timer. If the position hasn't been closed by stop loss, take profit, or manual intervention within the Position Patience period, the bot will automatically close it at the current market price. For example, if Position Patience is 24 hours and you open a position at 10:00 AM, the bot will force-close it at 10:00 AM the next day if it's still open, regardless of profit/loss status. This ensures capital turnover and prevents positions from becoming "stuck."</p>
                <p><strong>Recommended:</strong> 12 to 48 hours depending on your trading style and market characteristics. Shorter periods (12-24 hours) ensure faster capital turnover, allowing you to deploy capital to new opportunities more frequently. This is good for active trading strategies and markets that typically resolve quickly. Longer periods (36-48 hours) allow positions more time to develop and reach profit targets, which is better for markets that take longer to move or for strategies that require patience. Moderate traders typically use 24-36 hours.</p>
                <p><strong>Default:</strong> 24.0 hours</p>
                <p><strong>Capital Efficiency:</strong> Capital tied up in positions that aren't moving is capital that can't be used for new opportunities. Position Patience ensures that capital doesn't get stuck in stagnant positions. This is especially important if you have limited capital and want to maximize its utilization across multiple markets and opportunities.</p>
                <p><strong>Market Resolution Timeframes:</strong> Different markets have different typical resolution timeframes. Some markets resolve quickly (within hours or a day), while others take days or weeks. Set Position Patience based on your market's typical timeframe - it should be long enough to allow normal price movements but short enough to prevent capital from being tied up too long. For example, if most of your markets resolve within 24-48 hours, a Position Patience of 24-36 hours makes sense.</p>
                <p><strong>Trade-off Analysis:</strong></p>
                <ul>
                  <li><strong>Shorter periods (12-24 hours):</strong> Faster capital turnover, more trading opportunities, prevents capital from being tied up. However, you may exit positions too early before they have time to reach profit targets, potentially missing profitable moves that take longer to develop.</li>
                  <li><strong>Longer periods (36-48 hours):</strong> Positions have more time to develop and reach targets, reducing premature exits. However, capital may be tied up longer, reducing opportunities for new trades, and you may hold losing positions longer than necessary.</li>
                </ul>
                <p><strong>Relationship with Stop Loss and Take Profit:</strong> Position Patience works alongside your stop loss and take profit settings. Ideally, most positions should be closed by stop loss (if losing) or take profit (if winning) before Position Patience expires. Position Patience is a safety mechanism for positions that are neither winning nor losing significantly - they're just sitting there not moving. If many positions are hitting the patience limit, consider adjusting your stop loss or take profit levels.</p>
                <p><strong>Stagnant Position Problem:</strong> Some positions may not trigger stop loss or take profit because prices are moving very slowly or not at all. These positions tie up capital without providing returns. Position Patience solves this by forcing exits after a reasonable time, freeing capital for better opportunities.</p>
                <p><strong>Market-Specific Considerations:</strong> Consider your market's characteristics:</p>
                <ul>
                  <li><strong>Fast-moving markets:</strong> Shorter Position Patience (12-24 hours) is appropriate since positions should move quickly.</li>
                  <li><strong>Slow-moving markets:</strong> Longer Position Patience (36-48 hours) allows time for gradual price movements.</li>
                  <li><strong>News-driven markets:</strong> Position Patience should align with when news/events occur. If events happen daily, 24 hours makes sense. If weekly, 48+ hours may be needed.</li>
                </ul>
                <p><strong>Example:</strong> You open a position with Position Patience of 24 hours. The position doesn't hit stop loss or take profit - it's just sitting at breakeven or small profit/loss. After 24 hours, the bot automatically closes it, freeing that capital. You can then use that capital for a new position with better potential, rather than leaving it tied up in a stagnant position.</p>
                <p><strong>Adjustment Strategy:</strong> Monitor how often positions hit the patience limit. If many positions are being closed by patience rather than stop loss/take profit, consider: (1) increasing Position Patience if positions need more time, (2) adjusting stop loss/take profit to be more sensitive, or (3) reviewing whether you're trading the right markets. Find the balance where most positions close via stop loss/take profit, with patience as a backup.</p>
              </div>
            </div>
          </div>

          <!-- Advanced Section -->
          <div class="config-section">
            <div class="section-header">
              <h4>🔧 Advanced</h4>
            </div>
            
            <div class="form-group">
              <label class="form-label">
                Multiplier
                <span class="info-icon" @click="toggleInfo('multiplier')" title="Click for more info">ℹ️</span>
              </label>
              <input v-model.number="editParams.multiplier" type="number" step="0.1" min="0.1" max="10" class="form-input" />
              <div v-if="expandedInfo === 'multiplier'" class="info-box">
                <p><strong>Description:</strong> Multiplier is a global scaling factor that multiplies all position sizes across all parameters. It's a quick way to scale your entire trading strategy up or down without manually adjusting each individual parameter. A multiplier of 1.0 uses your configured sizes as-is (normal operation). A multiplier of 2.0 doubles all sizes (Trade Size, Max Size, etc.), while 0.5 halves them. This is useful for quickly adjusting strategy scale based on performance, capital availability, or market conditions.</p>
                <p><strong>How It Works:</strong> The multiplier is applied to all size-related parameters: Trade Size, Max Size, Min Size, and Target Position. For example, if your Trade Size is $10 and Max Size is $100, and you set Multiplier to 2.0, the effective Trade Size becomes $20 and Max Size becomes $200. The bot uses these scaled values for all trading decisions. This allows you to scale your entire strategy proportionally with a single parameter change.</p>
                <p><strong>Recommended:</strong> 1.0 for normal operation. Use 0.5-0.8 for testing new strategies, conservative scaling, or when you want to reduce risk exposure. Use 1.2-2.0 for aggressive scaling when you're confident in your strategy and have appropriate risk management in place. Never exceed 2.0 without careful consideration of your risk management parameters.</p>
                <p><strong>Default:</strong> 1.0 (no scaling)</p>
                <p><strong>Critical Warning:</strong> Increasing the multiplier increases BOTH potential profits AND potential losses proportionally. If you double the multiplier (2.0), you double your position sizes, which means you can make twice as much profit per trade, but you can also lose twice as much. Your maximum loss per market becomes: (Max Size × Multiplier) × |Stop Loss %|. For example, if Max Size is $100, Stop Loss is -5%, and Multiplier is 2.0, your maximum loss becomes $10 instead of $5. Always ensure your risk management parameters (especially Max Size and Stop Loss) can handle the increased exposure.</p>
                <p><strong>Use Cases:</strong></p>
                <ul>
                  <li><strong>Testing (0.5-0.8):</strong> Reduce sizes when testing new strategies or parameters to limit risk while validating the approach.</li>
                  <li><strong>Conservative Scaling (0.8-1.0):</strong> Slightly reduce sizes if you want to be more cautious or are experiencing drawdowns.</li>
                  <li><strong>Normal Operation (1.0):</strong> Use your configured sizes as designed.</li>
                  <li><strong>Aggressive Scaling (1.2-2.0):</strong> Increase sizes when you're confident in your strategy and want to scale up profits. Only do this with proper risk management.</li>
                </ul>
                <p><strong>Capital Requirements:</strong> Increasing the multiplier requires more capital. If you use a 2.0 multiplier, you need twice as much capital to support the same number of markets. Ensure you have sufficient capital before increasing the multiplier. Running out of capital can cause the bot to skip trades or fail to place orders.</p>
                <p><strong>Risk Management Impact:</strong> The multiplier affects all risk parameters proportionally. If you increase the multiplier, your maximum loss per market increases, your total capital exposure increases, and your risk per trade increases. Review your overall risk management before increasing the multiplier. Consider:</p>
                <ul>
                  <li>Total capital available vs. total exposure (sum of all Max Sizes × Multiplier)</li>
                  <li>Maximum loss per market (Max Size × Multiplier × |Stop Loss %|)</li>
                  <li>Whether your stop loss levels are still appropriate for the larger sizes</li>
                  <li>Whether you can afford the increased maximum losses</li>
                </ul>
                <p><strong>Gradual Scaling:</strong> Don't jump from 1.0 to 2.0 immediately. Gradually increase the multiplier (e.g., 1.0 → 1.2 → 1.5 → 2.0) and monitor performance at each level. This allows you to validate that the strategy works at larger sizes and catch any issues before scaling too aggressively.</p>
                <p><strong>Performance Validation:</strong> Before increasing the multiplier, ensure your strategy is consistently profitable at the current size. Scaling up a losing strategy just loses money faster. Only scale up when you have a proven track record of profitability and understand the strategy's behavior.</p>
                <p><strong>Market Conditions:</strong> You might adjust the multiplier based on market conditions. During favorable market conditions with high confidence, you might increase to 1.5-2.0. During uncertain or volatile conditions, you might decrease to 0.7-0.8. This allows dynamic risk adjustment without changing all your parameters.</p>
                <p><strong>Example:</strong> You have a profitable strategy with Trade Size = $10, Max Size = $100, Stop Loss = -5%. Maximum loss per market is $5. You want to scale up, so you set Multiplier to 1.5. Now effective Trade Size = $15, Max Size = $150, and maximum loss = $7.50. You've increased potential profits by 50% but also increased maximum loss by 50%. Ensure you can afford the $7.50 loss and have enough capital to support the larger sizes.</p>
                <p><strong>Best Practices:</strong> Always test multiplier changes with smaller values first. Monitor performance closely after changing the multiplier. Ensure your capital and risk management can handle the scaled sizes. Consider the multiplier as part of your overall risk management strategy, not just a way to make more money. Remember: bigger sizes mean bigger wins AND bigger losses.</p>
              </div>
            </div>
          </div>

          <div class="modal-actions">
            <button @click="resetToDefaults" class="btn btn-secondary">Reset to Defaults</button>
          </div>
        </div>
        <div class="modal-footer">
          <button @click="showEditModal = false" class="btn btn-secondary">Cancel</button>
          <button @click="saveMarket" class="btn btn-primary" :disabled="saving">
            {{ saving ? 'Saving...' : 'Save Configuration' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Sub-Markets Selection Modal -->
    <div v-if="showSubMarketsModal" class="modal-overlay" @click="showSubMarketsModal = false">
      <div class="modal-content modal-large" @click.stop>
        <div class="modal-header">
          <h3>📦 Select Markets to Add</h3>
          <button @click="showSubMarketsModal = false" class="modal-close">×</button>
        </div>
        <div class="modal-body">
          <!-- Event Title Header -->
          <div v-if="subMarketsList.length > 0 && subMarketsList[0].event_title" class="event-header">
            <div class="event-icon">🎯</div>
            <div class="event-info">
              <div class="event-label">Event</div>
              <div class="event-title-text">{{ subMarketsList[0].event_title }}</div>
              <div class="event-market-count">{{ subMarketsList.length }} tradeable market(s) in this event</div>
            </div>
          </div>
          
          <div class="sub-markets-controls">
            <div class="sub-markets-stats">
              <strong>{{ selectedSubMarkets.length }}</strong> of <strong>{{ subMarketsList.length }}</strong> selected
            </div>
            <div class="sub-markets-buttons">
              <button type="button" @click="selectAllSubMarkets" class="btn btn-sm btn-secondary">
                Select All
              </button>
              <button type="button" @click="deselectAllSubMarkets" class="btn btn-sm btn-secondary">
                Deselect All
              </button>
            </div>
          </div>
          
          <div class="sub-markets-list">
            <div 
              v-for="market in subMarketsList" 
              :key="market.condition_id"
              class="sub-market-item"
              :class="{ 'selected': selectedSubMarkets.includes(market.condition_id), 'missing-data': !market.token1 || !market.token2 }"
              @click="toggleSubMarketSelection(market.condition_id)"
            >
              <div class="sub-market-checkbox">
                <input 
                  type="checkbox" 
                  :checked="selectedSubMarkets.includes(market.condition_id)"
                  @click.stop="toggleSubMarketSelection(market.condition_id)"
                />
              </div>
              <div class="sub-market-info">
                <div class="sub-market-question">{{ market.question }}</div>
                <div class="sub-market-details">
                  <span class="badge badge-primary">{{ market.answer1 || 'YES' }}</span>
                  <span class="badge badge-secondary">{{ market.answer2 || 'NO' }}</span>
                  <span v-if="market.category" :class="['badge', getCategoryBadgeClass(market.category)]">
                    {{ market.category }}
                  </span>
                  <span v-if="!market.token1 || !market.token2" class="badge badge-danger">
                    Missing Tokens
                  </span>
                </div>
              </div>
            </div>
          </div>
          
          <div v-if="subMarketsList.length === 0" class="empty-state">
            <p>No markets found</p>
          </div>
        </div>
        <div class="modal-footer">
          <button @click="showSubMarketsModal = false" class="btn btn-secondary">Cancel</button>
          <button 
            @click="addSelectedSubMarkets" 
            class="btn btn-success" 
            :disabled="addingMultiple || selectedSubMarkets.length === 0"
          >
            {{ addingMultiple ? '⏳ Adding...' : `Add ${selectedSubMarkets.length} Market(s)` }}
          </button>
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
    const selectedMarkets = ref([])
    
    const isAllSelected = computed(() => {
      return markets.value.length > 0 && selectedMarkets.value.length === markets.value.length
    })
    
    const filter = ref({
      search: '',
      category: '',
      is_active: ''
    })
    
    const addForm = ref({
      url: '',
      condition_id: '',
      question: '',
      token1: '',
      token2: '',
      answer1: '',
      answer2: '',
      market_slug: '',
      category: 'crypto',
      is_active: true
    })
    
    const addError = ref('')
    const adding = ref(false)
    const loadingMarketFromUrl = ref(false)
    
    // Sub-markets state
    const hasSubMarkets = ref(false)
    const subMarketsInfo = ref(null)
    const showSubMarketsModal = ref(false)
    const subMarketsList = ref([])
    const selectedSubMarkets = ref([])
    const loadingSubMarkets = ref(false)
    const addingMultiple = ref(false)
    
    // Expanded groups state for accordion
    const expandedGroups = ref([])
    
    // Computed: Group markets by event name
    const groupedMarkets = computed(() => {
      const groups = {}
      
      for (const market of markets.value) {
        // Extract event name from question prefix [EventName] or use 'Standalone Markets'
        const eventName = getEventPrefix(market.question) || 'Standalone Markets'
        
        if (!groups[eventName]) {
          groups[eventName] = []
        }
        groups[eventName].push(market)
      }
      
      // Sort groups: Standalone Markets at the end
      const sortedGroups = {}
      const keys = Object.keys(groups).sort((a, b) => {
        if (a === 'Standalone Markets') return 1
        if (b === 'Standalone Markets') return -1
        return a.localeCompare(b)
      })
      
      for (const key of keys) {
        sortedGroups[key] = groups[key]
      }
      
      return sortedGroups
    })
    
    // Toggle group expand/collapse
    const toggleGroup = (eventName) => {
      const index = expandedGroups.value.indexOf(eventName)
      if (index > -1) {
        expandedGroups.value.splice(index, 1)
      } else {
        expandedGroups.value.push(eventName)
      }
    }
    
    // Check if all markets in a group are selected
    const isGroupSelected = (eventName) => {
      const group = groupedMarkets.value[eventName]
      if (!group || group.length === 0) return false
      return group.every(m => selectedMarkets.value.includes(m.id))
    }
    
    // Toggle selection for all markets in a group
    const toggleGroupSelection = (eventName) => {
      const group = groupedMarkets.value[eventName]
      if (!group) return
      
      const groupIds = group.map(m => m.id)
      const allSelected = isGroupSelected(eventName)
      
      if (allSelected) {
        // Deselect all in group
        selectedMarkets.value = selectedMarkets.value.filter(id => !groupIds.includes(id))
      } else {
        // Select all in group
        for (const id of groupIds) {
          if (!selectedMarkets.value.includes(id)) {
            selectedMarkets.value.push(id)
          }
        }
      }
    }
    
    // Get count of active markets in a group
    const getActiveCount = (group) => {
      return group.filter(m => m.is_active).length
    }
    
    // Expand all groups
    const expandAllGroups = () => {
      expandedGroups.value = Object.keys(groupedMarkets.value)
    }
    
    // Collapse all groups
    const collapseAllGroups = () => {
      expandedGroups.value = []
    }
    
    const editForm = ref({
      side_to_trade: 'BOTH',
      trading_mode: 'MARKET_MAKING',
      target_position: 0,
      is_active: true
    })
    
    const editParams = ref({
      trade_size: 10,
      max_size: 100,
      min_size: 5,
      max_spread: 5.0,
      tick_size: 0.01,
      multiplier: 1.0,
      stop_loss_threshold: -5,
      take_profit_threshold: 2,
      volatility_threshold: 50,
      spread_threshold: 0.05,
      sleep_period: 1.0,
      order_front_running: true,
      tick_improvement: 1,
      quick_cancel_threshold: 0.01,
      position_patience: 24
    })
    
    const expandedInfo = ref(null)
    const saving = ref(false)
    
    const defaultParams = {
      trade_size: 10,
      max_size: 100,
      min_size: 5,
      max_spread: 5.0,
      tick_size: 0.01,
      multiplier: 1.0,
      stop_loss_threshold: -5,
      take_profit_threshold: 2,
      volatility_threshold: 50,
      spread_threshold: 0.05,
      sleep_period: 1.0,
      order_front_running: true,
      tick_improvement: 1,
      quick_cancel_threshold: 0.01,
      position_patience: 24
    }
    
    const toggleInfo = (param) => {
      if (expandedInfo.value === param) {
        expandedInfo.value = null
      } else {
        expandedInfo.value = param
      }
    }
    
    const resetToDefaults = () => {
      if (confirm('Reset all parameters to default values?')) {
        editParams.value = { ...defaultParams }
        expandedInfo.value = null
      }
    }
    
    const getCategoryBadgeClass = (category) => {
      const categoryClasses = {
        'crypto': 'badge-warning',
        'politics': 'badge-danger',
        'sports': 'badge-success',
        'economics': 'badge-info',
        'entertainment': 'badge-purple',
        'technology': 'badge-blue',
        'science': 'badge-cyan',
        'other': 'badge-secondary'
      }
      return categoryClasses[category] || 'badge-secondary'
    }
    
    // Helper to extract event prefix from question (e.g., "[Bitcoin Price]" from "[Bitcoin Price] Will it hit $100k?")
    const getEventPrefix = (question) => {
      if (!question) return null
      const match = question.match(/^\[([^\]]+)\]/)
      return match ? match[1] : null
    }
    
    // Helper to get question without the event prefix
    const getQuestionWithoutPrefix = (question) => {
      if (!question) return ''
      return question.replace(/^\[[^\]]+\]\s*/, '')
    }
    
    const applyFilters = () => {
      const params = {}
      if (filter.value.search && filter.value.search.trim()) {
        params.search = filter.value.search.trim()
      }
      if (filter.value.category) params.category = filter.value.category
      // Convert string to boolean properly
      if (filter.value.is_active !== null && filter.value.is_active !== undefined && filter.value.is_active !== '') {
        params.is_active = filter.value.is_active === 'true' || filter.value.is_active === true
      }
      store.dispatch('markets/fetchMarkets', params)
    }
    
    const clearFilters = () => {
      filter.value = {
        search: '',
        category: '',
        is_active: ''
      }
      store.dispatch('markets/fetchMarkets', {})
    }
    
    const fetchMarketFromUrl = async () => {
      if (!addForm.value.url || !addForm.value.url.trim()) {
        return
      }
      
      loadingMarketFromUrl.value = true
      addError.value = ''
      hasSubMarkets.value = false
      subMarketsInfo.value = null
      
      try {
        // Extract slug from URL
        const url = addForm.value.url.trim()
        let slug = ''
        
        // Extract slug from various URL formats
        const urlPatterns = [
          /polymarket\.com\/event\/([^?\/]+)/,
          /polymarket\.com\/market\/([^?\/]+)/,
          /\/event\/([^?\/]+)/,
          /\/market\/([^?\/]+)/
        ]
        
        for (const pattern of urlPatterns) {
          const match = url.match(pattern)
          if (match && match[1]) {
            slug = match[1]
            break
          }
        }
        
        if (!slug) {
          addError.value = 'Invalid URL format. Example: https://polymarket.com/event/market-slug'
          loadingMarketFromUrl.value = false
          return
        }
        
        // Store slug for later use
        addForm.value._slug = slug
        
        // Fetch market data from backend
        const marketData = await api.fetchMarketBySlug(slug)
        
        if (marketData) {
          // Fill form with fetched data
          addForm.value.condition_id = marketData.condition_id || ''
          addForm.value.question = marketData.question || ''
          addForm.value.token1 = marketData.token1 || ''
          addForm.value.token2 = marketData.token2 || ''
          addForm.value.answer1 = marketData.answer1 || 'YES'
          addForm.value.answer2 = marketData.answer2 || 'NO'
          addForm.value.market_slug = marketData.market_slug || slug
          addForm.value.category = marketData.category || 'crypto'
          
          // Check for sub-markets
          if (marketData.has_sub_markets && marketData.total_sub_markets > 1) {
            hasSubMarkets.value = true
            subMarketsInfo.value = {
              total: marketData.total_sub_markets,
              eventTitle: marketData.event_title,
              hint: marketData.sub_markets_hint
            }
            addError.value = `This event contains ${marketData.total_sub_markets} markets. Click "Show All Markets" to see and add them all.`
          } else {
            // Check if required fields are filled
            if (!addForm.value.condition_id || !addForm.value.token1 || !addForm.value.token2) {
              addError.value = 'Warning: Some required fields are missing. Please check Condition ID, Token1, and Token2.'
            } else {
              addError.value = ''
            }
          }
        } else {
          addError.value = 'Market not found. Please check the slug.'
        }
      } catch (error) {
        const errorMsg = error.response?.data?.detail || error.message || 'Failed to fetch market information'
        addError.value = `Error: ${errorMsg}`
        console.error('Error fetching market from URL:', error)
      } finally {
        loadingMarketFromUrl.value = false
      }
    }
    
    const showAllSubMarkets = async () => {
      if (!addForm.value._slug) {
        addError.value = 'Please enter a URL first'
        return
      }
      
      loadingSubMarkets.value = true
      
      try {
        const result = await api.fetchAllMarketsBySlug(addForm.value._slug)
        
        if (result && result.markets && result.markets.length > 0) {
          subMarketsList.value = result.markets
          selectedSubMarkets.value = result.markets.map(m => m.condition_id) // Select all by default
          showSubMarketsModal.value = true
        } else {
          addError.value = 'No markets found for this event'
        }
      } catch (error) {
        const errorMsg = error.response?.data?.detail || error.message || 'Failed to fetch sub-markets'
        addError.value = `Error: ${errorMsg}`
        console.error('Error fetching sub-markets:', error)
      } finally {
        loadingSubMarkets.value = false
      }
    }
    
    const toggleSubMarketSelection = (conditionId) => {
      const index = selectedSubMarkets.value.indexOf(conditionId)
      if (index > -1) {
        selectedSubMarkets.value.splice(index, 1)
      } else {
        selectedSubMarkets.value.push(conditionId)
      }
    }
    
    const selectAllSubMarkets = () => {
      selectedSubMarkets.value = subMarketsList.value.map(m => m.condition_id)
    }
    
    const deselectAllSubMarkets = () => {
      selectedSubMarkets.value = []
    }
    
    const addSelectedSubMarkets = async () => {
      if (selectedSubMarkets.value.length === 0) {
        alert('Please select at least one market to add')
        return
      }
      
      addingMultiple.value = true
      let successCount = 0
      let errorCount = 0
      const errors = []
      
      try {
        for (const conditionId of selectedSubMarkets.value) {
          const market = subMarketsList.value.find(m => m.condition_id === conditionId)
          if (!market) continue
          
          // Skip markets without required fields
          if (!market.condition_id || !market.token1 || !market.token2) {
            errors.push(`Skipped "${market.question?.substring(0, 50)}...": Missing required fields`)
            errorCount++
            continue
          }
          
          try {
            // Build question with event title prefix for better organization
            let questionText = market.question || ''
            const eventTitle = market.event_title || subMarketsList.value[0]?.event_title || ''
            
            // Add event title as prefix if it's different from the question
            // This helps identify which event the sub-market belongs to
            if (eventTitle && !questionText.toLowerCase().includes(eventTitle.toLowerCase().substring(0, 20))) {
              questionText = `[${eventTitle}] ${questionText}`
            }
            
            const marketData = {
              condition_id: market.condition_id,
              question: questionText,
              token1: market.token1,
              token2: market.token2,
              answer1: market.answer1 || 'YES',
              answer2: market.answer2 || 'NO',
              market_slug: market.market_slug || '',
              category: market.category || 'crypto',
              neg_risk: market.neg_risk || 'FALSE',
              is_active: true
            }
            
            await store.dispatch('markets/createMarket', marketData)
            successCount++
          } catch (err) {
            const errMsg = err.response?.data?.detail || err.message || 'Unknown error'
            // Check if it's a duplicate error
            if (errMsg.includes('already exists') || errMsg.includes('UNIQUE constraint')) {
              errors.push(`Skipped "${market.question?.substring(0, 30)}...": Already exists`)
            } else {
              errors.push(`Failed "${market.question?.substring(0, 30)}...": ${errMsg}`)
            }
            errorCount++
          }
        }
        
        // Show results
        let message = `Added ${successCount} market(s) successfully.`
        if (errorCount > 0) {
          message += `\n\n${errorCount} market(s) failed:`
          message += '\n' + errors.slice(0, 5).join('\n')
          if (errors.length > 5) {
            message += `\n... and ${errors.length - 5} more errors`
          }
        }
        
        alert(message)
        
        // Close modal and refresh
        showSubMarketsModal.value = false
        showAddModal.value = false
        store.dispatch('markets/fetchMarkets', {})
        
      } catch (error) {
        console.error('Error adding sub-markets:', error)
        alert('Error adding markets: ' + (error.message || 'Unknown error'))
      } finally {
        addingMultiple.value = false
      }
    }
    
    const fetchAllMarkets = async () => {
      try {
        // Show loading state
        const loadingMessage = 'Fetching ALL markets from Polymarket...\nThis may take several minutes.\n\nMarkets will be automatically categorized.\n\nThe process will run in the background.\n\nContinue?'
        if (confirm(loadingMessage)) {
          const response = await api.fetchAllMarkets()
          
          if (response && response.status === 'fetching') {
            alert('✅ Market fetch started in background!\n\nYou can check the progress by refreshing the page.\n\nStatus endpoint: /api/markets/fetch/status')
            
            // Start polling for status
            pollFetchStatus()
          } else {
            alert('✅ Markets fetched successfully!')
          }
        }
      } catch (error) {
        console.error('Full error object in fetchAllMarkets:', error)
        console.error('Error response data:', error?.response?.data)
        let errorMessage = 'Failed to fetch markets.\n\n'
        
        // Helper function to extract error message - handles all error formats including FastAPI validation errors
        const getErrorMessage = (err) => {
          if (typeof err === 'string') return err
          if (!err) return 'Unknown error occurred'
          
          // Check response.data first (most common)
          if (err?.response?.data) {
            const data = err.response.data
            if (typeof data === 'string') return data
            
            // Handle detail array (FastAPI validation errors - 422)
            if (data?.detail) {
              if (Array.isArray(data.detail)) {
                return data.detail.map(d => {
                  if (typeof d === 'object' && d?.msg) {
                    const loc = Array.isArray(d.loc) ? d.loc.join('.') : (d.loc || 'field')
                    return `${loc}: ${d.msg}`
                  }
                  return String(d)
                }).join('\n')
              }
              if (typeof data.detail === 'string') return data.detail
            }
            
            if (data?.message && typeof data.message === 'string') return data.message
            try {
              const str = JSON.stringify(data, null, 2)
              return str.length > 500 ? str.substring(0, 500) + '...' : str
            } catch {
              return String(data)
            }
          }
          
          if (err?.data) {
            const data = err.data
            if (typeof data === 'string') return data
            if (data?.detail) {
              if (Array.isArray(data.detail)) {
                return data.detail.map(d => String(d)).join('\n')
              }
              if (typeof data.detail === 'string') return data.detail
            }
            if (data?.message && typeof data.message === 'string') return data.message
          }
          
          if (err?.message) {
            if (typeof err.message === 'string') return err.message
            try {
              return JSON.stringify(err.message, null, 2)
            } catch {
              return String(err.message)
            }
          }
          
          try {
            const str = JSON.stringify(err, Object.getOwnPropertyNames(err), 2)
            return str.length > 500 ? str.substring(0, 500) + '...' : str
          } catch {
            return String(err)
          }
        }
        
        const errorDetail = getErrorMessage(error)
        
        // Provide helpful error messages
        if (error.response?.status === 409 || error?.status === 409) {
          errorMessage += 'Already in Progress:\n'
          errorMessage += errorDetail
          errorMessage += '\n\nPlease wait for the current fetch to complete.'
        } else if (error.response?.status === 400 || error?.status === 400) {
          errorMessage += 'Configuration Error:\n'
          errorMessage += errorDetail
          errorMessage += '\n\nPlease check your .env file and ensure PK and BROWSER_ADDRESS are set correctly.'
        } else if (error.response?.status === 404 || error?.status === 404) {
          errorMessage += 'No Markets Found:\n'
          errorMessage += errorDetail
          errorMessage += '\n\nThis might be a temporary API issue. Please try again later.'
        } else if (error.response?.status === 503 || error?.status === 503) {
          errorMessage += 'Connection Error:\n'
          errorMessage += errorDetail
          errorMessage += '\n\nPlease check your internet connection and Polymarket API status.'
        } else if (error.response?.status === 500 || error?.status === 500) {
          errorMessage += 'Server Error:\n'
          errorMessage += errorDetail
          errorMessage += '\n\nPlease check backend logs for more details.'
        } else {
          errorMessage += errorDetail
        }
        
        alert(errorMessage)
        console.error('Error fetching markets:', error)
      }
    }
    
    const fetchCryptoMarkets = async () => {
      try {
        // Show loading state
        const loadingMessage = 'Fetching crypto markets from Polymarket...\nThis may take a few minutes.\n\nThe process will run in the background.\n\nContinue?'
        if (confirm(loadingMessage)) {
          const response = await store.dispatch('markets/fetchCryptoMarkets')
          
          if (response && (response.status === 'fetching' || response.status === 'processing')) {
            alert('✅ Market fetch started in background!\n\nYou can check the progress by refreshing the page.\n\nStatus endpoint: /api/markets/crypto/fetch/status')
            
            // Start polling for status
            pollCryptoFetchStatus()
          } else {
            alert('✅ Crypto markets fetched successfully!')
          }
        }
      } catch (error) {
        console.error('Full error object in fetchCryptoMarkets:', error)
        console.error('Error response data:', error?.response?.data)
        let errorMessage = 'Failed to fetch crypto markets.\n\n'
        
        // Helper function to extract error message - handles all error formats including FastAPI validation errors
        const getErrorMessage = (err) => {
          if (typeof err === 'string') return err
          if (!err) return 'Unknown error occurred'
          
          // Check response.data first (most common)
          if (err?.response?.data) {
            const data = err.response.data
            if (typeof data === 'string') return data
            
            // Handle detail array (FastAPI validation errors - 422)
            if (data?.detail) {
              if (Array.isArray(data.detail)) {
                return data.detail.map(d => {
                  if (typeof d === 'object' && d?.msg) {
                    const loc = Array.isArray(d.loc) ? d.loc.join('.') : (d.loc || 'field')
                    return `${loc}: ${d.msg}`
                  }
                  return String(d)
                }).join('\n')
              }
              if (typeof data.detail === 'string') return data.detail
            }
            
            if (data?.message && typeof data.message === 'string') return data.message
            try {
              const str = JSON.stringify(data, null, 2)
              return str.length > 500 ? str.substring(0, 500) + '...' : str
            } catch {
              return String(data)
            }
          }
          
          if (err?.data) {
            const data = err.data
            if (typeof data === 'string') return data
            if (data?.detail) {
              if (Array.isArray(data.detail)) {
                return data.detail.map(d => String(d)).join('\n')
              }
              if (typeof data.detail === 'string') return data.detail
            }
            if (data?.message && typeof data.message === 'string') return data.message
          }
          
          if (err?.message) {
            if (typeof err.message === 'string') return err.message
            try {
              return JSON.stringify(err.message, null, 2)
            } catch {
              return String(err.message)
            }
          }
          
          try {
            const str = JSON.stringify(err, Object.getOwnPropertyNames(err), 2)
            return str.length > 500 ? str.substring(0, 500) + '...' : str
          } catch {
            return String(err)
          }
        }
        
        const errorDetail = getErrorMessage(error)
        
        // Provide helpful error messages
        if (error.response?.status === 409 || error?.status === 409) {
          errorMessage += 'Already in Progress:\n'
          errorMessage += errorDetail
          errorMessage += '\n\nPlease wait for the current fetch to complete.'
        } else if (error.response?.status === 400 || error?.status === 400) {
          errorMessage += 'Configuration Error:\n'
          errorMessage += errorDetail
          errorMessage += '\n\nPlease check your .env file and ensure PK and BROWSER_ADDRESS are set correctly.'
        } else if (error.response?.status === 404 || error?.status === 404) {
          errorMessage += 'No Markets Found:\n'
          errorMessage += errorDetail
          errorMessage += '\n\nThis might be a temporary API issue. Please try again later.'
        } else if (error.response?.status === 503 || error?.status === 503) {
          errorMessage += 'Connection Error:\n'
          errorMessage += errorDetail
          errorMessage += '\n\nPlease check your internet connection and Polymarket API status.'
        } else if (error.response?.status === 500 || error?.status === 500) {
          errorMessage += 'Server Error:\n'
          errorMessage += errorDetail
          errorMessage += '\n\nPlease check backend logs for more details.'
        } else {
          errorMessage += errorDetail
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
    
    const pollCryptoFetchStatus = () => {
      // Poll fetch status every 5 seconds
      const interval = setInterval(async () => {
        try {
          const status = await api.getCryptoFetchStatus()
          console.log('Crypto fetch status:', status)
          
          if (status.status === 'completed' || status.status === 'error') {
            clearInterval(interval)
            if (status.status === 'completed') {
              alert(`✅ Crypto market fetch completed!\n\nSaved ${status.total_saved} markets to database.`)
              // Refresh markets list with current filters
              applyFilters()
            } else {
              alert(`❌ Crypto market fetch failed:\n\n${status.error || 'Unknown error'}`)
            }
          }
        } catch (error) {
          console.error('Error polling crypto fetch status:', error)
        }
      }, 5000)
      
      // Stop polling after 10 minutes
      setTimeout(() => clearInterval(interval), 600000)
    }
    
    const addMarket = async () => {
      // Validation
      if (!addForm.value.condition_id || !addForm.value.question || 
          !addForm.value.token1 || !addForm.value.token2) {
        addError.value = 'Please fill in all required fields (Condition ID, Question, Token1, Token2)'
        return
      }
      
      adding.value = true
      addError.value = ''
      
      try {
        const marketData = {
          condition_id: addForm.value.condition_id.trim(),
          question: addForm.value.question.trim(),
          token1: addForm.value.token1.trim(),
          token2: addForm.value.token2.trim(),
          answer1: addForm.value.answer1.trim() || undefined,
          answer2: addForm.value.answer2.trim() || undefined,
          market_slug: addForm.value.market_slug.trim() || undefined,
          category: addForm.value.category,
          is_active: addForm.value.is_active
        }
        
        await store.dispatch('markets/createMarket', marketData)
        
        // Reset form
        addForm.value = {
          condition_id: '',
          question: '',
          token1: '',
          token2: '',
          answer1: '',
          answer2: '',
          market_slug: '',
          category: 'crypto',
          is_active: true
        }
        
        showAddModal.value = false
        addError.value = ''
        
        // Refresh markets list
        applyFilters()
        
        alert('✅ Market added successfully!')
      } catch (error) {
        const errorMsg = error.response?.data?.detail || error.message || 'Unknown error'
        addError.value = `Failed to add market: ${errorMsg}`
        console.error('Error adding market:', error)
      } finally {
        adding.value = false
      }
    }
    
    const editMarket = async (market) => {
      selectedMarket.value = market
      editForm.value = {
        side_to_trade: market.side_to_trade,
        trading_mode: market.trading_mode,
        target_position: market.target_position,
        is_active: market.is_active
      }
      
      // Reset expanded info
      expandedInfo.value = null
      
      // Fetch trading params
      try {
        const params = await api.getMarketConfig(market.id)
        // Merge with defaults to ensure all params are present
        editParams.value = { ...defaultParams, ...params }
      } catch (error) {
        console.error('Error fetching params:', error)
        // Use defaults if fetch fails
        editParams.value = { ...defaultParams }
      }
      
      showEditModal.value = true
    }
    
    const saveMarket = async () => {
      saving.value = true
      try {
        await api.updateMarket(selectedMarket.value.id, editForm.value)
        await api.updateMarketConfig(selectedMarket.value.id, editParams.value)
        showEditModal.value = false
        expandedInfo.value = null
        applyFilters()
        alert('✅ Market configuration saved successfully!')
      } catch (error) {
        const errorMsg = error.response?.data?.detail || error.message || 'Unknown error'
        alert('❌ Failed to update market:\n\n' + errorMsg)
        console.error('Error saving market:', error)
      } finally {
        saving.value = false
      }
    }
    
    const deleteMarket = async (id) => {
      if (!confirm('Are you sure you want to delete this market?')) return
      
      try {
        await store.dispatch('markets/deleteMarket', id)
        alert('Market deleted successfully!')
        // Remove from selection if selected
        selectedMarkets.value = selectedMarkets.value.filter(mid => mid !== id)
      } catch (error) {
        alert('Failed to delete market: ' + error.message)
      }
    }
    
    const toggleSelectAll = () => {
      if (isAllSelected.value) {
        selectedMarkets.value = []
      } else {
        selectedMarkets.value = markets.value.map(m => m.id)
      }
    }
    
    const clearSelection = () => {
      selectedMarkets.value = []
    }
    
    const bulkActivate = async () => {
      if (selectedMarkets.value.length === 0) return
      
      if (!confirm(`Activate ${selectedMarkets.value.length} market(s)?`)) return
      
      try {
        await api.bulkUpdateMarkets(selectedMarkets.value, { is_active: true })
        alert(`✅ Successfully activated ${selectedMarkets.value.length} market(s)!`)
        clearSelection()
        applyFilters()
      } catch (error) {
        const errorMsg = error.response?.data?.detail || error.message || 'Unknown error'
        alert('❌ Failed to activate markets:\n\n' + errorMsg)
      }
    }
    
    const bulkDeactivate = async () => {
      if (selectedMarkets.value.length === 0) return
      
      if (!confirm(`Deactivate ${selectedMarkets.value.length} market(s)?`)) return
      
      try {
        await api.bulkUpdateMarkets(selectedMarkets.value, { is_active: false })
        alert(`✅ Successfully deactivated ${selectedMarkets.value.length} market(s)!`)
        clearSelection()
        applyFilters()
      } catch (error) {
        const errorMsg = error.response?.data?.detail || error.message || 'Unknown error'
        alert('❌ Failed to deactivate markets:\n\n' + errorMsg)
      }
    }
    
    const bulkDelete = async () => {
      if (selectedMarkets.value.length === 0) return
      
      const count = selectedMarkets.value.length
      if (!confirm(`⚠️ WARNING: This will permanently delete ${count} market(s)!\n\nThis action cannot be undone.\n\nAre you sure?`)) return
      
      try {
        await api.bulkDeleteMarkets(selectedMarkets.value)
        alert(`✅ Successfully deleted ${count} market(s)!`)
        clearSelection()
        applyFilters()
      } catch (error) {
        const errorMsg = error.response?.data?.detail || error.message || 'Unknown error'
        alert('❌ Failed to delete markets:\n\n' + errorMsg)
      }
    }
    
    onMounted(() => {
      // Load all markets on mount (no filters)
      store.dispatch('markets/fetchMarkets', {})
    })
    
    return {
      markets,
      loading,
      showAddModal,
      showEditModal,
      selectedMarket,
      selectedMarkets,
      isAllSelected,
      filter,
      addForm,
      addError,
      adding,
      editForm,
      editParams,
      expandedInfo,
      saving,
      applyFilters,
      clearFilters,
      fetchMarketFromUrl,
      loadingMarketFromUrl,
      fetchAllMarkets,
      fetchCryptoMarkets,
      addMarket,
      editMarket,
      saveMarket,
      deleteMarket,
      toggleInfo,
      toggleSelectAll,
      clearSelection,
      bulkActivate,
      bulkDeactivate,
      bulkDelete,
      resetToDefaults,
      getCategoryBadgeClass,
      getEventPrefix,
      getQuestionWithoutPrefix,
      // Grouped markets
      groupedMarkets,
      expandedGroups,
      toggleGroup,
      isGroupSelected,
      toggleGroupSelection,
      getActiveCount,
      expandAllGroups,
      collapseAllGroups,
      // Sub-markets
      hasSubMarkets,
      subMarketsInfo,
      showSubMarketsModal,
      subMarketsList,
      selectedSubMarkets,
      loadingSubMarkets,
      addingMultiple,
      showAllSubMarkets,
      toggleSubMarketSelection,
      selectAllSubMarkets,
      deselectAllSubMarkets,
      addSelectedSubMarkets
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
  background: rgba(0, 0, 0, 0.75);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(4px);
  animation: fadeIn 0.3s;
}

.configure-modal {
  background: var(--bg-secondary);
  border-radius: 16px;
  max-width: 900px;
  width: 95%;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: var(--shadow-lg);
  border: 1px solid var(--border);
  animation: slideUp 0.3s;
  color: var(--text-primary);
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid var(--border);
  background: var(--bg-tertiary);
  border-radius: 16px 16px 0 0;
}

.modal-header h3 {
  color: var(--text-primary);
  font-size: 1.25rem;
  font-weight: 600;
  margin: 0;
}

.modal-close {
  background: none;
  border: none;
  font-size: 2rem;
  cursor: pointer;
  color: var(--text-secondary);
  transition: var(--transition);
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  line-height: 1;
}

.modal-close:hover {
  color: var(--text-primary);
  background: var(--bg-primary);
}

.modal-body {
  padding: 2rem;
}

.modal-footer {
  padding: 1.5rem;
  border-top: 1px solid var(--border);
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  background: var(--bg-tertiary);
  border-radius: 0 0 16px 16px;
}

/* Config Sections */
.config-section {
  margin-bottom: 2rem;
  padding: 1.5rem;
  background: var(--bg-primary);
  border-radius: 12px;
  border: 1px solid var(--border);
}

.section-header {
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid var(--border);
}

.section-header h4 {
  color: var(--text-primary);
  font-size: 1.1rem;
  font-weight: 600;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

/* Form Groups */
.form-group {
  margin-bottom: 1.5rem;
}

.form-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
  font-weight: 500;
  color: var(--text-primary);
  font-size: 0.9375rem;
}

.info-icon {
  cursor: pointer;
  font-size: 1rem;
  opacity: 0.7;
  transition: var(--transition);
  user-select: none;
}

.info-icon:hover {
  opacity: 1;
  transform: scale(1.1);
}

.info-box {
  margin-top: 0.75rem;
  padding: 1rem;
  background: var(--bg-tertiary);
  border-left: 3px solid var(--primary);
  border-radius: 8px;
  font-size: 0.875rem;
  line-height: 1.6;
  color: var(--text-secondary);
  animation: slideDown 0.3s;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.info-box p {
  margin: 0.5rem 0;
}

.info-box p:first-child {
  margin-top: 0;
}

.info-box p:last-child {
  margin-bottom: 0;
}

.info-box ul {
  margin: 0.5rem 0;
  padding-left: 1.5rem;
}

.info-box li {
  margin: 0.25rem 0;
}

.info-box strong {
  color: var(--text-primary);
}

.checkbox-group {
  margin-bottom: 1.5rem;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  color: var(--text-primary);
}

.checkbox-label input[type="checkbox"] {
  width: auto;
  cursor: pointer;
}

.modal-actions {
  margin-top: 2rem;
  padding-top: 1.5rem;
  border-top: 1px solid var(--border);
  display: flex;
  justify-content: flex-end;
}

/* Form Inputs */
.form-input,
.form-select {
  width: 100%;
  padding: 0.75rem;
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: 8px;
  color: var(--text-primary);
  font-size: 1rem;
  transition: var(--transition);
}

.form-input:focus,
.form-select:focus {
  outline: none;
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.form-input::placeholder {
  color: var(--text-muted);
}

/* Responsive */
@media (max-width: 768px) {
  .configure-modal {
    max-width: 95%;
    width: 95%;
  }
  
  .modal-body {
    padding: 1rem;
  }
  
  .config-section {
    padding: 1rem;
  }
  
  .modal-footer {
    flex-direction: column;
  }
  
  .modal-footer button {
    width: 100%;
  }
}

/* Bulk Actions */
.bulk-actions-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  background: var(--bg-primary);
  border-bottom: 2px solid var(--primary);
  margin-bottom: 0;
}

.bulk-actions-info {
  color: var(--text-primary);
  font-size: 0.9375rem;
}

.bulk-actions-info strong {
  color: var(--primary);
  font-weight: 600;
}

.bulk-actions-buttons {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.bulk-actions-buttons .btn {
  white-space: nowrap;
}

.table th:first-child,
.table td:first-child {
  text-align: center;
  padding: 0.75rem 0.5rem;
}

.table th:first-child input[type="checkbox"],
.table td:first-child input[type="checkbox"] {
  cursor: pointer;
  width: 18px;
  height: 18px;
}

@media (max-width: 768px) {
  .bulk-actions-toolbar {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }
  
  .bulk-actions-buttons {
    width: 100%;
  }
  
  .bulk-actions-buttons .btn {
    flex: 1;
    min-width: 0;
  }
}

/* Add Market Modal Styles */
.required {
  color: #e74c3c;
  font-weight: bold;
}

.form-help {
  display: block;
  margin-top: 0.25rem;
  font-size: 0.8125rem;
  color: var(--text-secondary);
  opacity: 0.8;
}

.alert {
  padding: 0.75rem 1rem;
  border-radius: 8px;
  margin-bottom: 1rem;
  font-size: 0.875rem;
}

.alert-danger {
  background-color: #fee;
  border: 1px solid #fcc;
  color: #c33;
}

/* Category Badge Colors */
.badge-purple {
  background-color: #9b59b6;
  color: white;
}

.badge-blue {
  background-color: #3498db;
  color: white;
}

.badge-cyan {
  background-color: #1abc9c;
  color: white;
}

/* Sub-markets Styles */
.sub-markets-info {
  margin-top: 12px;
}

/* Event Header in Sub-markets Modal */
.event-header {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding: 16px 20px;
  margin-bottom: 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  color: white;
}

.event-icon {
  font-size: 2.5em;
  line-height: 1;
}

.event-info {
  flex: 1;
}

.event-label {
  font-size: 0.75em;
  text-transform: uppercase;
  letter-spacing: 1px;
  opacity: 0.8;
  margin-bottom: 4px;
}

.event-title-text {
  font-size: 1.25em;
  font-weight: 600;
  line-height: 1.3;
  margin-bottom: 8px;
}

.event-market-count {
  font-size: 0.85em;
  opacity: 0.9;
  background: rgba(255,255,255,0.2);
  padding: 4px 10px;
  border-radius: 20px;
  display: inline-block;
}

.sub-markets-alert {
  background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
  border: 1px solid #f39c12;
  border-radius: 8px;
  padding: 16px;
  color: #856404;
}

.sub-markets-alert strong {
  display: block;
  font-size: 1.1em;
  margin-bottom: 8px;
}

.sub-markets-alert p {
  margin: 4px 0;
  font-size: 0.9em;
}

.modal-large {
  max-width: 800px;
  max-height: 90vh;
}

.sub-markets-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border-color);
}

.sub-markets-stats {
  font-size: 0.95em;
  color: var(--text-secondary);
}

.sub-markets-buttons {
  display: flex;
  gap: 8px;
}

.sub-markets-list {
  max-height: 400px;
  overflow-y: auto;
  border: 1px solid var(--border-color);
  border-radius: 8px;
}

.sub-market-item {
  display: flex;
  align-items: flex-start;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-color);
  cursor: pointer;
  transition: background-color 0.2s;
}

.sub-market-item:last-child {
  border-bottom: none;
}

.sub-market-item:hover {
  background-color: var(--bg-hover);
}

.sub-market-item.selected {
  background-color: rgba(39, 174, 96, 0.1);
  border-left: 3px solid #27ae60;
}

.sub-market-item.missing-data {
  opacity: 0.6;
}

.sub-market-checkbox {
  margin-right: 12px;
  padding-top: 2px;
}

.sub-market-checkbox input[type="checkbox"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
}

.sub-market-info {
  flex: 1;
}

.sub-market-question {
  font-weight: 500;
  margin-bottom: 8px;
  line-height: 1.4;
}

.sub-market-details {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.sub-market-details .badge {
  font-size: 0.75em;
  padding: 2px 8px;
}

/* Market Question Cell with Event Tag */
.market-question-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.market-event-tag {
  display: inline-block;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  font-size: 0.7em;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 4px;
  max-width: fit-content;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 300px;
}

.market-question-text {
  line-height: 1.4;
}

/* Group Controls */
.group-controls {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.group-controls .btn {
  font-size: 0.8em;
}

/* Grouped Markets Styles */
.markets-grouped {
  border: 1px solid var(--border-color);
  border-radius: 8px;
  overflow: hidden;
}

.market-group {
  border-bottom: 1px solid var(--border-color);
}

.market-group:last-child {
  border-bottom: none;
}

.market-group-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  cursor: pointer;
  transition: all 0.2s ease;
  user-select: none;
}

.market-group-header:hover {
  filter: brightness(1.1);
}

.market-group-header.expanded {
  border-bottom: 2px solid rgba(255,255,255,0.3);
}

.market-group-header.standalone {
  background: linear-gradient(135deg, #636e72 0%, #2d3436 100%);
}

.group-header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.group-expand-icon {
  font-size: 0.8em;
  width: 16px;
  text-align: center;
  transition: transform 0.2s;
}

.group-header-left input[type="checkbox"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
}

.group-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.group-event-icon {
  font-size: 1.2em;
}

.group-event-name {
  font-weight: 600;
  font-size: 1em;
}

.group-header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.group-market-count {
  font-size: 0.85em;
  opacity: 0.9;
}

.group-active-count {
  font-size: 0.75em;
  background: rgba(255,255,255,0.2);
  padding: 3px 10px;
  border-radius: 12px;
}

.group-active-count.all-active {
  background: rgba(39, 174, 96, 0.4);
}

.group-header-right .badge {
  font-size: 0.7em;
}

/* Sub-markets table inside group */
.market-group-content {
  background: var(--bg-secondary);
  padding: 0;
}

.sub-markets-table {
  margin: 0;
  border: none;
}

.sub-markets-table thead {
  background: var(--bg-primary);
}

.sub-markets-table thead th {
  font-size: 0.8em;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--text-secondary);
  padding: 10px 12px;
  border-bottom: 1px solid var(--border-color);
}

.sub-market-row {
  transition: background 0.2s;
}

.sub-market-row:hover {
  background: var(--bg-hover);
}

.sub-market-row td {
  padding: 12px;
  border-bottom: 1px solid var(--border-color);
  vertical-align: middle;
}

.sub-market-row:last-child td {
  border-bottom: none;
}

.sub-market-question {
  font-weight: 500;
  margin-bottom: 4px;
  line-height: 1.3;
}

.sub-market-answers {
  display: flex;
  gap: 6px;
}

.answer-tag {
  font-size: 0.7em;
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 500;
}

.answer-tag.yes {
  background: #d4edda;
  color: #155724;
}

.answer-tag.no {
  background: #f8d7da;
  color: #721c24;
}

/* Markets Summary */
.markets-summary {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 8px;
  padding: 12px;
  font-size: 0.85em;
  color: var(--text-secondary);
  border-top: 1px solid var(--border-color);
  background: var(--bg-secondary);
}

.markets-summary .separator {
  opacity: 0.5;
}
</style>

