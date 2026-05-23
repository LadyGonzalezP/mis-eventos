/**
 * Smoke test del componente raiz.
 *
 * Verifica que la app monta sin errores y muestra los elementos clave.
 * Los tests reales de componentes (forms, listados) vienen en Slice 6.
 */
import { describe, expect, it } from "vitest"
import { render, screen } from "@testing-library/react"
import App from "../App"

describe("App", () => {
  it("muestra el titulo del proyecto", () => {
    render(<App />)
    expect(screen.getByText("Mis Eventos")).toBeInTheDocument()
  })

  it("muestra el contexto del reto", () => {
    render(<App />)
    expect(
      screen.getByText(/Reto tecnico Serviinformacion 2026/i),
    ).toBeInTheDocument()
  })

  it("incluye un link a Swagger", () => {
    render(<App />)
    const link = screen.getByText(/Ver API Swagger/i)
    expect(link).toBeInTheDocument()
    expect(link.closest("a")).toHaveAttribute(
      "href",
      "http://localhost:8000/docs",
    )
  })
})
