import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { User, LoginCredentials, RegisterData } from '@/types/auth.types'
import authService from '@/services/api/auth.service'
import router from '@/router'

export const useAuthStore = defineStore('auth', () => {
  // State
  const user = ref<User | null>(null)
  const token = ref<string | null>(localStorage.getItem('access_token'))
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Getters
  const isAuthenticated = computed(() => !!token.value && !!user.value)
  const isAdmin = computed(() => user.value?.is_admin ?? false)

  // Actions
  async function login(credentials: LoginCredentials) {
    loading.value = true
    error.value = null
    try {
      const response = await authService.login(credentials)
      token.value = response.access_token
      user.value = response.user
      localStorage.setItem('access_token', response.access_token)
      return true
    } catch (e: any) {
      error.value = e.response?.data?.detail || 'Login failed'
      return false
    } finally {
      loading.value = false
    }
  }

  async function register(data: RegisterData) {
    loading.value = true
    error.value = null
    try {
      await authService.register(data)
      return true
    } catch (e: any) {
      error.value = e.response?.data?.detail || 'Registration failed'
      return false
    } finally {
      loading.value = false
    }
  }

  async function fetchCurrentUser() {
    if (!token.value) return
    try {
      user.value = await authService.getCurrentUser()
    } catch {
      logout()
    }
  }

  function logout() {
    user.value = null
    token.value = null
    localStorage.removeItem('access_token')
    router.push('/')
  }

  function clearError() {
    error.value = null
  }

  return {
    user,
    token,
    loading,
    error,
    isAuthenticated,
    isAdmin,
    login,
    register,
    fetchCurrentUser,
    logout,
    clearError
  }
})
