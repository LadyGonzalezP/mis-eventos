import type { ReactNode } from "react"
import { Navigate, useLocation } from "react-router-dom"
import type { UserRole } from "@/api/types"
import { useAuthStore } from "@/stores/authStore"

interface ProtectedRouteProps {
  children: ReactNode
  /** Si se especifica, solo usuarios con uno de estos roles pueden acceder. */
  roles?: UserRole[]
}

export function ProtectedRoute({ children, roles }: ProtectedRouteProps) {
  const { isAuthenticated, user } = useAuthStore()
  const location = useLocation()

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  if (roles && user && !roles.includes(user.role)) {
    return <Navigate to="/403" replace />
  }

  return <>{children}</>
}
