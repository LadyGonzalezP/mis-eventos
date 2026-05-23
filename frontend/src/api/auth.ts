import { apiClient } from "./client"
import type { TokenResponse, UserRole } from "./types"

export interface RegisterPayload {
  name: string
  email: string
  password: string
  role: UserRole
}

export interface LoginPayload {
  email: string
  password: string
}

export const authApi = {
  register: (payload: RegisterPayload) =>
    apiClient.post<TokenResponse>("/api/v1/auth/register", payload).then((r) => r.data),

  login: (payload: LoginPayload) =>
    apiClient.post<TokenResponse>("/api/v1/auth/login", payload).then((r) => r.data),
}
