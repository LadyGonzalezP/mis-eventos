import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { eventsApi } from "@/api/events"
import { EventCard } from "@/components/EventCard"

export function EventListPage() {
  const [q, setQ] = useState("")
  const [page, setPage] = useState(1)
  const limit = 10

  const { data, isLoading, error } = useQuery({
    queryKey: ["events", { q, page, limit }],
    queryFn: () => eventsApi.list({ q: q || undefined, page, limit }),
  })

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Eventos publicados</h1>
      </div>

      <div className="mb-6">
        <input
          type="search"
          placeholder="Buscar por nombre..."
          value={q}
          onChange={(e) => {
            setQ(e.target.value)
            setPage(1)
          }}
          className="w-full md:w-80 px-3 py-2 border border-input rounded-md bg-background"
          aria-label="Buscar eventos"
        />
      </div>

      {isLoading && (
        <div className="text-center py-12 text-muted-foreground">Cargando eventos...</div>
      )}

      {error && (
        <div
          role="alert"
          className="rounded-md bg-destructive/10 border border-destructive text-destructive px-4 py-3"
        >
          Error cargando eventos
        </div>
      )}

      {data && data.items.length === 0 && (
        <div className="text-center py-12 text-muted-foreground">
          No hay eventos publicados que coincidan con tu busqueda.
        </div>
      )}

      {data && data.items.length > 0 && (
        <>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {data.items.map((event) => (
              <EventCard key={event.id} event={event} />
            ))}
          </div>

          <div className="mt-6 flex items-center justify-between text-sm">
            <span className="text-muted-foreground">
              Total: {data.total} eventos
            </span>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-3 py-1.5 border rounded-md disabled:opacity-50"
              >
                Anterior
              </button>
              <span className="px-3 py-1.5">
                Pagina {page} de {Math.max(1, Math.ceil(data.total / limit))}
              </span>
              <button
                type="button"
                onClick={() =>
                  setPage((p) =>
                    p < Math.ceil(data.total / limit) ? p + 1 : p,
                  )
                }
                disabled={page >= Math.ceil(data.total / limit)}
                className="px-3 py-1.5 border rounded-md disabled:opacity-50"
              >
                Siguiente
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
