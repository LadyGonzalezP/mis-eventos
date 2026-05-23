import { create } from "zustand"
import { persist } from "zustand/middleware"
import type { TokenResponse, User } from "@/api/types"

interface AuthState {
  token: string | null
  user: User | null
  isAuthenticated: boolean
  login: (data: TokenResponse) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      isAuthenticated: false,
      login: (data) => {
        localStorage.setItem("auth_token", data.access_token)
        set({
          token: data.access_token,
          user: data.user,
          isAuthenticated: true,
        })
      },
      logout: () => {
        localStorage.removeItem("auth_token")
        set({ token: null, user: null, isAuthenticated: false })
      },
    }),
    {
      name: "mis-eventos-auth",
      partialize: (state) => ({ user: state.user, token: state.token }),
      onRehydrateStorage: () => (state) => {
        if (state?.token) {
          state.isAuthenticated = true
        }
      },
    },
  ),
)
