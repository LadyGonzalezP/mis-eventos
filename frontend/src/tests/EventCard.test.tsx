import { describe, expect, it } from "vitest"
import { render, screen } from "@testing-library/react"
import { MemoryRouter } from "react-router-dom"
import { EventCard } from "@/components/EventCard"
import type { Event } from "@/api/types"

const baseEvent: Event = {
  id: "00000000-0000-0000-0000-000000000001",
  name: "Conf 2026",
  description: "Una conferencia tecnica",
  start_date: "2030-06-01T10:00:00",
  end_date: "2030-06-01T18:00:00",
  location: "Bogota",
  capacity: 100,
  status: "publicado",
  organizer_id: "00000000-0000-0000-0000-000000000002",
  created_at: "2026-01-01T00:00:00",
  updated_at: "2026-01-01T00:00:00",
}

function renderCard(event: Event) {
  return render(
    <MemoryRouter>
      <EventCard event={event} />
    </MemoryRouter>,
  )
}

describe("EventCard", () => {
  it("muestra el nombre del evento", () => {
    renderCard(baseEvent)
    expect(screen.getByText("Conf 2026")).toBeInTheDocument()
  })

  it("muestra el estado del evento", () => {
    renderCard(baseEvent)
    expect(screen.getByText("publicado")).toBeInTheDocument()
  })

  it("muestra la capacidad", () => {
    renderCard(baseEvent)
    expect(screen.getByText(/Capacidad: 100/)).toBeInTheDocument()
  })

  it("incluye link al detalle del evento", () => {
    renderCard(baseEvent)
    const link = screen.getByRole("link")
    expect(link).toHaveAttribute("href", `/events/${baseEvent.id}`)
  })

  it("muestra 'Sin descripcion' si no hay description", () => {
    renderCard({ ...baseEvent, description: "" })
    expect(screen.getByText("Sin descripcion")).toBeInTheDocument()
  })
})
