import { createRouter, createWebHistory } from 'vue-router'
import DcfValuationView from '../views/DcfValuationView.vue'
import StockScreenerView from '../views/StockScreenerView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'dcf-valuation',
      component: DcfValuationView
    },
    {
      path: '/screener',
      name: 'stock-screener',
      component: StockScreenerView
    },
    {
      path: '/valuation-assistant',
      name: 'valuation-assistant',
      component: () => import('../views/ValuationAssistantView.vue')
    },
    {
      path: '/deep-research',
      name: 'deep-research',
      component: DcfValuationView // Placeholder
    },
    {
      path: '/strategy-research',
      name: 'strategy-research',
      component: DcfValuationView // Placeholder
    },
    {
      path: '/backtest',
      name: 'backtest',
      component: DcfValuationView // Placeholder
    },
    {
      path: '/trading-log',
      name: 'trading-log',
      component: DcfValuationView // Placeholder
    }
  ]
})

export default router
