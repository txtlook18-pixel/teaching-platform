import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  { path: '/', redirect: '/dashboard' },
  {
    path: '/login',
    component: () => import('@/pages/LoginPage.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/register',
    component: () => import('@/pages/RegisterPage.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/join',
    component: () => import('@/pages/StudentJoinPage.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/play/:sessionId',
    component: () => import('@/pages/StudentPlayPage.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/dashboard',
    component: () => import('@/pages/DashboardPage.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/lessons/create',
    component: () => import('@/pages/CreateLessonPage.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/lessons/:id',
    component: () => import('@/pages/LessonPage.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/lessons/:id/assignment/:assignmentId',
    component: () => import('@/pages/AssignmentPage.vue'),
    meta: { requiresAuth: true },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  const authStore = useAuthStore()
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    return '/login'
  }
})

export default router
