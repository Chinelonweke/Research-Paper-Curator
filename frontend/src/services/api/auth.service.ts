import api from '@/plugins/axios'
import type { LoginCredentials, RegisterData, User, TokenResponse } from '@/types/auth.types'

class AuthService {
  async login(credentials: LoginCredentials): Promise<TokenResponse> {
    const formData = new URLSearchParams()
    formData.append('username', credentials.email)
    formData.append('password', credentials.password)

    const response = await api.post('/auth/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    })
    return response.data
  }

  async register(data: RegisterData): Promise<User> {
    const response = await api.post('/auth/register', data)
    return response.data
  }

  async getCurrentUser(): Promise<User> {
    const response = await api.get('/auth/me')
    return response.data
  }
}

export default new AuthService()
