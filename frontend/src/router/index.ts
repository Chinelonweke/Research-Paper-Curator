import { createRouter, createWebHistory, type RouteLocationNormalized } from 'vue-router'
import { useAuthStore } from '@/stores/auth.store'

// Layouts
import DefaultLayout from '@/layouts/DefaultLayout.vue'
import AuthLayout from '@/layouts/AuthLayout.vue'

// Pages (lazy loaded)
const HomePage = () => import('@/pages/HomePage.vue')
const SearchPage = () => import('@/pages/SearchPage.vue')
const AskPage = () => import('@/pages/AskPage.vue')
const BrowsePage = () => import('@/pages/BrowsePage.vue')
const LoginPage = () => import('@/pages/LoginPage.vue')
const RegisterPage = () => import('@/pages/RegisterPage.vue')
const ProfilePage = () => import('@/pages/ProfilePage.vue')
const CollectionsPage = () => import('@/pages/CollectionsPage.vue')
const HistoryPage = () => import('@/pages/HistoryPage.vue')
const NotFoundPage = () => import('@/pages/NotFoundPage.vue')

const routes = [
  {
    path: '/',
    component: DefaultLayout,
    meta: { requiresAuth: true },
    children: [
      { path: '', name: 'home', component: HomePage },
      { path: 'search', name: 'search', component: SearchPage },
      { path: 'ask', name: 'ask', component: AskPage },
      { path: 'browse', name: 'browse', component: BrowsePage },
      {
        path: 'profile',
        name: 'profile',
        component: ProfilePage
      },
      {
        path: 'collections',
        name: 'collections',
        component: CollectionsPage
      },
      {
        path: 'history',
        name: 'history',
        component: HistoryPage
      }
    ]
  },
  {
    path: '/auth',
    component: AuthLayout,
    children: [
      { path: 'login', name: 'login', component: LoginPage },
      { path: 'register', name: 'register', component: RegisterPage }
    ]
  },
  { path: '/:pathMatch(.*)*', name: 'not-found', component: NotFoundPage }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Navigation guard
router.beforeEach(async (to: RouteLocationNormalized, _from, next) => {
  const authStore = useAuthStore()

  // Try to fetch user if we have token but no user
  if (authStore.token && !authStore.user) {
    await authStore.fetchCurrentUser()
  }

  // Check protected routes
  if (to.matched.some(record => record.meta.requiresAuth)) {
    if (!authStore.isAuthenticated) {
      next({ name: 'login', query: { redirect: to.fullPath } })
    } else {
      next()
    }
  } else if ((to.name === 'login' || to.name === 'register') && authStore.isAuthenticated) {
    next({ name: 'home' })
  } else {
    next()
  }
})

export default router
