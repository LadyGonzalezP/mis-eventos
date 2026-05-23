import { type FormEvent, useState } from "react"
import { Link, useLocation, useNavigate } from "react-router-dom"
import { authApi } from "@/api/auth"
import { extractErrorMessage } from "@/api/client"
import { useAuthStore } from "@/stores/authStore"

export function LoginPage() {
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const login = useAuthStore((s) => s.login)
  const navigate = useNavigate()
  const location = useLocation()
  const from = (location.state as { from?: { pathname: string } } | null)?.from?.pathname

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      const data = await authApi.login({ email, password })
      login(data)
      navigate(from ?? "/events", { replace: true })
    } catch (err) {
      setError(extractErrorMessage(err, "No se pudo iniciar sesion"))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-md mx-auto px-4 py-12">
      <h1 className="text-2xl font-bold mb-6">Iniciar sesion</h1>
      <form onSubmit={onSubmit} className="space-y-4">
        <div>
          <label htmlFor="email" className="block text-sm font-medium mb-1">
            Email
          </label>
          <input
            id="email"
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full px-3 py-2 border border-input rounded-md bg-background"
          />
        </div>
        <div>
          <label htmlFor="password" className="block text-sm font-medium mb-1">
            Contrasena
          </label>
          <input
            id="password"
            type="password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full px-3 py-2 border border-input rounded-md bg-background"
          />
        </div>

        {error && (
          <div
            role="alert"
            className="rounded-md bg-destructive/10 border border-destructive text-destructive px-3 py-2 text-sm"
          >
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          className="w-full py-2 rounded-md bg-primary text-primary-foreground hover:opacity-90 disabled:opacity-50"
        >
          {loading ? "Iniciando..." : "Iniciar sesion"}
        </button>

        <p className="text-sm text-muted-foreground text-center">
          No tienes cuenta?{" "}
          <Link to="/register" className="underline hover:text-foreground">
            Registrate
          </Link>
        </p>
      </form>
    </div>
  )
}
