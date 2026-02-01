import { createRouter, createWebHistory } from 'vue-router'
import PtpMap from '../components/PtpMap.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: PtpMap
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
