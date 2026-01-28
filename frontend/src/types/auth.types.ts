export interface User {
  id: number
  email: string
  username: string
  full_name?: string
  is_active: boolean
  is_admin: boolean
}

export interface LoginCredentials {
  email: string
  password: string
}

export interface RegisterData {
  email: string
  username: string
  password: string
  full_name?: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  user: User
}
