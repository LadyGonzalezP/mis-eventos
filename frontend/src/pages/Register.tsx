import { type FormEvent, useState } from "react"
import { Link, useNavigate } from "react-router-dom"
import type { UserRole } from "@/api/types"
import { authApi } from "@/api/auth"
import { extractErrorMessage } from "@/api/client"
import { useAuthStore } from "@/stores/authStore"

export function RegisterPage() {
  const [name, setName] = useState("")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [role, setRole] = useState<UserRole>("asistente")
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const login = useAuthStore((s) => s.login)
  const navigate = useNavigate()

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      const data = await authApi.register({ name, email, password, role })
      login(data)
      navigate("/events", { replace: true })
    } catch (err) {
      setError(extractErrorMessage(err, "No se pudo crear la cuenta"))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-md mx-auto px-4 py-12">
      <h1 className="text-2xl font-bold mb-6">Crear cuenta</h1>
      <form onSubmit={onSubmit} className="space-y-4">
        <div>
          <label htmlFor="name" className="block text-sm font-medium mb-1">
            Nombre completo
          </label>
          <input
            id="name"
            type="text"
            required
            minLength={2}
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full px-3 py-2 border border-input rounded-md bg-background"
          />
        </div>
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
            minLength={8}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full px-3 py-2 border border-input rounded-md bg-background"
          />
          <p className="text-xs text-muted-foreground mt-1">
            Minimo 8 caracteres con al menos 1 numero
          </p>
        </div>
        <div>
          <label htmlFor="role" className="block text-sm font-medium mb-1">
            Soy
          </label>
          <select
            id="role"
            value={role}
            onChange={(e) => setRole(e.target.value as UserRole)}
            className="w-full px-3 py-2 border border-input rounded-md bg-background"
          >
            <option value="asistente">Asistente (me inscribo a eventos)</option>
            <option value="organizador">Organizador (gestiono eventos)</option>
          </select>
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
          {loading ? "Creando cuenta..." : "Crear cuenta"}
        </button>

        <p className="text-sm text-muted-foreground text-center">
          Ya tienes cuenta?{" "}
          <Link to="/login" className="underline hover:text-foreground">
            Inicia sesion
          </Link>
        </p>
      </form>
    </div>
  )
}
