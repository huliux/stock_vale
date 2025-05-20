import './assets/main.css'

import { createPinia } from 'pinia'
import { createApp } from 'vue'

import App from './App.vue'
import router from './router'
import { useHistoryStore } from './stores/historyStore'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)

// Initialize the history store by loading data from localStorage
const historyStore = useHistoryStore(pinia)
historyStore.loadFromLocalStorage()

app.mount('#app')
