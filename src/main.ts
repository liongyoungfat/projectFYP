import './assets/main.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'

const app = createApp(App)

app.use(createPinia())
app.use(router)

app.mount('#app')


window.addEventListener('error', function (event) {
  if (
    event.message &&
    event.message.includes("Cannot read properties of null (reading 'save')")
  ) {
    alert("A chart rendering error occurred. Please refresh the page to continue.");
  }
});