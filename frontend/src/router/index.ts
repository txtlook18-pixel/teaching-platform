import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  {
    path: '/',
    redirect: '/login',
  },
  {
    path: '/login',
    component: () => import('@/pages/LoginPage.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/forgot-password',
    component: () => import('@/pages/ForgotPasswordPage.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/reset-password',
    component: () => import('@/pages/ResetPasswordPage.vue'),
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
    path: '/wait/:sessionId',
    component: () => import('@/pages/StudentWaitPage.vue'),
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
    path: '/lessons/:id/questions',
    component: () => import('@/pages/QuestionsPreviewPage.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/lessons/:id/assignment/:assignmentId',
    component: () => import('@/pages/AssignmentPage.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/lessons/:id/retelling/:assignmentId',
    component: () => import('@/pages/RetellingPage.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/lessons/:id/screen-test/:assignmentId',
    component: () => import('@/pages/ScreenTestPage.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/lessons/:id/phone-test/:assignmentId',
    component: () => import('@/pages/PhoneTestPage.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/lessons/:id/cards-group/:assignmentId',
    component: () => import('@/pages/CardsGroupPage.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/lessons/:id/analysis-group/:assignmentId',
    component: () => import('@/pages/AnalysisGroupPage.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/lessons/:id/battle-screen/:assignmentId',
    component: () => import('@/pages/BattleScreenPage.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/archive',
    component: () => import('@/pages/ArchivePage.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/profile',
    component: () => import('@/pages/ProfilePage.vue'),
    meta: { requiresAuth: true },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  const authStore = useAuthStore()
  if (to.path === '/login' && authStore.isAuthenticated) {
    return '/dashboard'
  }
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    return '/login'
  }
})

export default router
