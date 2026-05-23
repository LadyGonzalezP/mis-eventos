import { useQuery } from "@tanstack/react-query"
import { Link } from "react-router-dom"
import { eventsApi } from "@/api/events"

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleString("es-CO", {
      dateStyle: "medium",
      timeStyle: "short",
    })
  } catch {
    return iso
  }
}

export function MyEventsPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["my-events"],
    queryFn: () => eventsApi.myRegistrations(),
  })

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold mb-6">Mis eventos inscritos</h1>

      {isLoading && (
        <div className="text-center py-12 text-muted-foreground">Cargando...</div>
      )}

      {error && (
        <div
          role="alert"
          className="rounded-md bg-destructive/10 border border-destructive text-destructive px-4 py-3"
        >
          Error cargando tus eventos
        </div>
      )}

      {data && data.length === 0 && (
        <div className="rounded-lg border bg-card p-8 text-center">
          <p className="text-muted-foreground mb-4">
            Aun no estas inscrito a ningun evento.
          </p>
          <Link
            to="/events"
            className="text-primary hover:underline font-medium"
          >
            Ver eventos disponibles →
          </Link>
        </div>
      )}

      {data && data.length > 0 && (
        <div className="space-y-3">
          {data.map((item) => (
            <Link
              key={item.event_id}
              to={`/events/${item.event_id}`}
              className="block border rounded-lg p-4 bg-card hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between gap-2">
                <h3 className="font-semibold">{item.event_name}</h3>
                <span className="text-xs px-2 py-0.5 rounded-full bg-secondary text-secondary-foreground">
                  {item.event_status}
                </span>
              </div>
              <p className="text-sm text-muted-foreground mt-1">
                📅 {formatDate(item.start_date)}
                {item.location && ` · 📍 ${item.location}`}
              </p>
              <p className="text-xs text-muted-foreground mt-1">
                Inscrito el {formatDate(item.registered_at)}
              </p>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
