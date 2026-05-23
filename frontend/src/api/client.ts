import axios, { type AxiosError } from "axios"

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000"

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: { "Content-Type": "application/json" },
})

// Interceptor de request: agrega Authorization Bearer si hay token
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem("auth_token")
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Tipo del error estandar del backend
export interface ApiError {
  error: string
  detail: string
  context?: Record<string, unknown>
}

// Interceptor de response: extrae mensaje legible de errores
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<ApiError>) => {
    // Si el token expiro o es invalido, limpiamos y mandamos a login
    if (error.response?.status === 401) {
      localStorage.removeItem("auth_token")
    }
    return Promise.reject(error)
  },
)

/** Helper para extraer el mensaje de error legible desde un AxiosError */
export function extractErrorMessage(error: unknown, fallback = "Error inesperado"): string {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data as ApiError | undefined
    return data?.detail ?? fallback
  }
  if (error instanceof Error) return error.message
  return fallback
}
