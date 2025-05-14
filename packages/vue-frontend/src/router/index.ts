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
    }
  ]
})

export default router
