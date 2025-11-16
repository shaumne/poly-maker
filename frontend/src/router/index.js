import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import Markets from '../views/Markets.vue'
import Positions from '../views/Positions.vue'
import Orders from '../views/Orders.vue'
import Settings from '../views/Settings.vue'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: Dashboard
  },
  {
    path: '/markets',
    name: 'Markets',
    component: Markets
  },
  {
    path: '/positions',
    name: 'Positions',
    component: Positions
  },
  {
    path: '/orders',
    name: 'Orders',
    component: Orders
  },
  {
    path: '/settings',
    name: 'Settings',
    component: Settings
  }
]

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes
})

export default router

