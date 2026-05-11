import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import { i18n, setLocale, getCurrentLocale } from './i18n'
import './styles/main.css'
import 'flag-icons/css/flag-icons.min.css'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.use(i18n)

// Apply stored locale to <html lang="..."> on startup
setLocale(getCurrentLocale())

app.mount('#app')
