<template>
  <div class="settings">
    <h2>Settings</h2>

    <!-- API Configuration -->
    <div class="card">
      <div class="card-header">
        <h3 class="card-title">API Configuration</h3>
      </div>
      <div class="card-body">
        <div class="form-group">
          <label class="form-label">Private Key (PK)</label>
          <input 
            v-model="settings.pk" 
            type="password" 
            class="form-input" 
            placeholder="Enter your private key"
          />
          <p class="help-text">Your Polymarket wallet private key</p>
        </div>

        <div class="form-group">
          <label class="form-label">Wallet Address</label>
          <input 
            v-model="settings.browser_address" 
            type="text" 
            class="form-input" 
            placeholder="0x..."
          />
          <p class="help-text">Your Polymarket wallet address</p>
        </div>

        <button @click="saveApiSettings" class="btn btn-primary">Save API Settings</button>
      </div>
    </div>

    <!-- Default Trading Parameters -->
    <div class="card">
      <div class="card-header">
        <h3 class="card-title">Default Trading Parameters</h3>
      </div>
      <div class="card-body">
        <div class="form-row">
          <div class="form-group">
            <label class="form-label">Trade Size</label>
            <input v-model.number="defaults.trade_size" type="number" class="form-input" />
          </div>

          <div class="form-group">
            <label class="form-label">Max Size</label>
            <input v-model.number="defaults.max_size" type="number" class="form-input" />
          </div>

          <div class="form-group">
            <label class="form-label">Min Size</label>
            <input v-model.number="defaults.min_size" type="number" class="form-input" />
          </div>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label class="form-label">Stop Loss Threshold (%)</label>
            <input v-model.number="defaults.stop_loss_threshold" type="number" class="form-input" />
          </div>

          <div class="form-group">
            <label class="form-label">Take Profit Threshold (%)</label>
            <input v-model.number="defaults.take_profit_threshold" type="number" class="form-input" />
          </div>

          <div class="form-group">
            <label class="form-label">Volatility Threshold</label>
            <input v-model.number="defaults.volatility_threshold" type="number" class="form-input" />
          </div>
        </div>

        <button @click="saveDefaults" class="btn btn-primary">Save Defaults</button>
      </div>
    </div>

    <!-- Bot Behavior -->
    <div class="card">
      <div class="card-header">
        <h3 class="card-title">Bot Behavior</h3>
      </div>
      <div class="card-body">
        <div class="form-group checkbox-group">
          <label class="checkbox-label">
            <input v-model="behavior.order_front_running" type="checkbox" />
            <span>Enable Order Front Running</span>
          </label>
          <p class="help-text">Place orders ahead of competing bots</p>
        </div>

        <div class="form-group">
          <label class="form-label">Tick Improvement</label>
          <input v-model.number="behavior.tick_improvement" type="number" class="form-input" min="0" max="5" />
          <p class="help-text">Number of ticks to improve price (0-5)</p>
        </div>

        <div class="form-group">
          <label class="form-label">Position Patience (hours)</label>
          <input v-model.number="behavior.position_patience" type="number" class="form-input" />
          <p class="help-text">How long to hold positions before forced exit</p>
        </div>

        <button @click="saveBehavior" class="btn btn-primary">Save Behavior Settings</button>
      </div>
    </div>

    <!-- System Info -->
    <div class="card">
      <div class="card-header">
        <h3 class="card-title">System Information</h3>
      </div>
      <div class="card-body">
        <div class="info-item">
          <strong>Database:</strong> {{ dbStatus }}
        </div>
        <div class="info-item">
          <strong>API Status:</strong> {{ apiStatus }}
        </div>
        <div class="info-item">
          <strong>Version:</strong> 1.0.0
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import api from '../api/client'

export default {
  name: 'Settings',
  setup() {
    const settings = ref({
      pk: '',
      browser_address: ''
    })
    
    const defaults = ref({
      trade_size: 10,
      max_size: 100,
      min_size: 5,
      stop_loss_threshold: -5,
      take_profit_threshold: 2,
      volatility_threshold: 50
    })
    
    const behavior = ref({
      order_front_running: true,
      tick_improvement: 1,
      position_patience: 24
    })
    
    const dbStatus = ref('Connected')
    const apiStatus = ref('Online')
    
    const loadSettings = async () => {
      try {
        const allSettings = await api.getSettings()
        
        allSettings.forEach(setting => {
          if (setting.key === 'pk' || setting.key === 'PK') {
            settings.value.pk = setting.value
          }
          if (setting.key === 'browser_address' || setting.key === 'BROWSER_ADDRESS') {
            settings.value.browser_address = setting.value
          }
        })
        
        // If not found in database, try to load from .env (via wallet info endpoint)
        if (!settings.value.browser_address) {
          try {
            const walletInfo = await api.getWalletInfo()
            if (walletInfo.wallet_address && walletInfo.wallet_address !== 'your_actual_wallet_address') {
              settings.value.browser_address = walletInfo.wallet_address
            }
          } catch (e) {
            // Ignore if wallet info endpoint fails
          }
        }
      } catch (error) {
        console.error('Error loading settings:', error)
      }
    }
    
    const saveApiSettings = async () => {
      try {
        // Validate inputs
        if (!settings.value.pk || settings.value.pk.trim() === '') {
          alert('Please enter a private key')
          return
        }
        
        if (!settings.value.browser_address || settings.value.browser_address.trim() === '') {
          alert('Please enter a wallet address')
          return
        }
        
        // Validate wallet address format
        if (!settings.value.browser_address.startsWith('0x') || settings.value.browser_address.length !== 42) {
          alert('Invalid wallet address format. Must start with 0x and be 42 characters long.')
          return
        }
        
        // Try to update existing settings
        try {
          await api.updateSetting('pk', { value: settings.value.pk })
          await api.updateSetting('browser_address', { value: settings.value.browser_address })
          alert('✅ API settings saved successfully!\n\n⚠️ Please restart the backend server for changes to take effect.')
        } catch (updateError) {
          // Try creating if update failed (settings don't exist yet)
          await api.createSetting({ key: 'pk', value: settings.value.pk })
          await api.createSetting({ key: 'browser_address', value: settings.value.browser_address })
          alert('✅ API settings saved successfully!\n\n⚠️ Please restart the backend server for changes to take effect.')
        }
      } catch (error) {
        const errorMsg = error.response?.data?.detail || error.message || 'Unknown error'
        alert('❌ Failed to save API settings:\n\n' + errorMsg)
        console.error('Error saving API settings:', error)
      }
    }
    
    const saveDefaults = () => {
      localStorage.setItem('defaultParams', JSON.stringify(defaults.value))
      alert('Default parameters saved!')
    }
    
    const saveBehavior = () => {
      localStorage.setItem('botBehavior', JSON.stringify(behavior.value))
      alert('Behavior settings saved!')
    }
    
    onMounted(() => {
      loadSettings()
      
      // Load from localStorage
      const savedDefaults = localStorage.getItem('defaultParams')
      if (savedDefaults) {
        defaults.value = JSON.parse(savedDefaults)
      }
      
      const savedBehavior = localStorage.getItem('botBehavior')
      if (savedBehavior) {
        behavior.value = JSON.parse(savedBehavior)
      }
    })
    
    return {
      settings,
      defaults,
      behavior,
      dbStatus,
      apiStatus,
      saveApiSettings,
      saveDefaults,
      saveBehavior
    }
  }
}
</script>

<style scoped>
.card-body {
  padding: 1.5rem;
}

.form-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 1rem;
}

.help-text {
  font-size: 0.875rem;
  color: var(--text-secondary);
  margin-top: 0.25rem;
}

.checkbox-group {
  margin-bottom: 1.5rem;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
}

.checkbox-label input[type="checkbox"] {
  width: auto;
}

.info-item {
  padding: 0.75rem 0;
  border-bottom: 1px solid var(--border-color);
}

.info-item:last-child {
  border-bottom: none;
}
</style>

