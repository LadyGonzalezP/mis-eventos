/**
 * Smoke test del componente raiz.
 *
 * Verifica que la app monta sin errores con Router + QueryClient.
 */
import { describe, expect, it } from "vitest"
import { render, screen } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { MemoryRouter } from "react-router-dom"
import App from "../App"

function renderApp(initialPath = "/login") {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[initialPath]}>
        <App />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe("App", () => {
  it("muestra el header con el branding", () => {
    renderApp()
    expect(screen.getAllByText("Mis Eventos")[0]).toBeInTheDocument()
  })

  it("muestra la pagina de login en /login", () => {
    renderApp("/login")
    expect(screen.getByRole("heading", { name: /Iniciar sesion/i })).toBeInTheDocument()
  })

  it("muestra la pagina de registro en /register", () => {
    renderApp("/register")
    expect(screen.getByRole("heading", { name: /Crear cuenta/i })).toBeInTheDocument()
  })

  it("redirige / a /events", () => {
    renderApp("/")
    expect(screen.getByRole("heading", { name: /Eventos publicados/i })).toBeInTheDocument()
  })

  it("muestra 404 en ruta desconocida", () => {
    renderApp("/ruta-que-no-existe")
    expect(screen.getByText("404")).toBeInTheDocument()
  })
})
