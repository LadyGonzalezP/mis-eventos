import { Link, Outlet, useNavigate } from "react-router-dom"
import { useAuthStore } from "@/stores/authStore"

export function Layout() {
  const { isAuthenticated, user, logout } = useAuthStore()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate("/login")
  }

  return (
    <div className="min-h-screen bg-background flex flex-col">
      <header className="border-b bg-card">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
          <Link to="/" className="text-xl font-bold text-foreground">
            Mis Eventos
          </Link>

          <nav className="flex items-center gap-4 text-sm">
            <Link to="/events" className="hover:text-foreground text-muted-foreground">
              Eventos
            </Link>

            {isAuthenticated && user ? (
              <>
                <Link
                  to="/me/events"
                  className="hover:text-foreground text-muted-foreground"
                >
                  Mis eventos
                </Link>
                {(user.role === "organizador" || user.role === "admin") && (
                  <Link
                    to="/events/new"
                    className="hover:text-foreground text-muted-foreground"
                  >
                    Crear evento
                  </Link>
                )}
                <span className="text-xs px-2 py-1 rounded-full bg-secondary text-secondary-foreground">
                  {user.name} · {user.role}
                </span>
                <button
                  onClick={handleLogout}
                  className="text-muted-foreground hover:text-destructive"
                  type="button"
                >
                  Salir
                </button>
              </>
            ) : (
              <>
                <Link to="/login" className="hover:text-foreground text-muted-foreground">
                  Iniciar sesion
                </Link>
                <Link
                  to="/register"
                  className="px-3 py-1.5 rounded-md bg-primary text-primary-foreground hover:opacity-90"
                >
                  Crear cuenta
                </Link>
              </>
            )}
          </nav>
        </div>
      </header>

      <main className="flex-1">
        <Outlet />
      </main>

      <footer className="border-t bg-card mt-auto">
        <div className="max-w-6xl mx-auto px-4 py-4 text-xs text-center text-muted-foreground">
          Mis Eventos · Reto Serviinformacion 2026 · Construido por Lady Katherine Gonzalez
        </div>
      </footer>
    </div>
  )
}
