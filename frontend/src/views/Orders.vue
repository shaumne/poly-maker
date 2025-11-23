<template>
  <div class="orders">
    <div class="orders-header">
      <h2>Orders</h2>
      <div class="controls">
        <button @click="showActiveOnly = !showActiveOnly" class="btn btn-primary">
          {{ showActiveOnly ? 'Show All' : 'Show Active Only' }}
        </button>
        <button @click="refreshOrders" class="btn btn-secondary">🔄 Refresh</button>
      </div>
    </div>

    <!-- Orders Table -->
    <div class="card">
      <div v-if="loading" class="loading">Loading orders...</div>
      <div v-else-if="displayedOrders.length > 0">
        <table class="table">
          <thead>
            <tr>
              <th>Order ID</th>
              <th>Market ID</th>
              <th>Token ID</th>
              <th>Side Type</th>
              <th>Side</th>
              <th>Price</th>
              <th>Size</th>
              <th>Filled</th>
              <th>Status</th>
              <th>Created</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="order in displayedOrders" :key="order.id">
              <td>{{ order.order_id ? order.order_id.slice(0, 8) + '...' : 'N/A' }}</td>
              <td>{{ order.market_id }}</td>
              <td>{{ order.token_id.slice(0, 8) }}...</td>
              <td>
                <span :class="['badge', order.side_type === 'BUY' ? 'badge-success' : 'badge-danger']">
                  {{ order.side_type }}
                </span>
              </td>
              <td>
                <span class="badge badge-primary">{{ order.side || 'N/A' }}</span>
              </td>
              <td>${{ order.price.toFixed(3) }}</td>
              <td>{{ order.size.toFixed(2) }}</td>
              <td>{{ order.filled_size.toFixed(2) }}</td>
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
        <div class="empty-state-icon">📋</div>
        <p>{{ showActiveOnly ? 'No active orders' : 'No orders found' }}</p>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { useStore } from 'vuex'

export default {
  name: 'Orders',
  setup() {
    const store = useStore()
    
    const orders = computed(() => store.state.orders.orders)
    const loading = computed(() => store.state.orders.loading)
    
    const showActiveOnly = ref(false)
    
    const displayedOrders = computed(() => {
      if (showActiveOnly.value) {
        return orders.value.filter(o => o.status === 'PENDING')
      }
      return orders.value
    })
    
    const refreshOrders = () => {
      if (showActiveOnly.value) {
        store.dispatch('orders/fetchActiveOrders')
      } else {
        store.dispatch('orders/fetchOrders')
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
    
    onMounted(() => {
      refreshOrders()
      
      // Auto-refresh every 10 seconds
      setInterval(refreshOrders, 10000)
    })
    
    return {
      orders,
      loading,
      showActiveOnly,
      displayedOrders,
      refreshOrders,
      getStatusBadge,
      formatDate
    }
  }
}
</script>

<style scoped>
.orders-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.controls {
  display: flex;
  gap: 1rem;
}
</style>

