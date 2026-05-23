import { useState } from "react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useNavigate, useParams } from "react-router-dom"
import { extractErrorMessage } from "@/api/client"
import { eventsApi } from "@/api/events"
import { useAuthStore } from "@/stores/authStore"

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleString("es-CO", {
      dateStyle: "long",
      timeStyle: "short",
    })
  } catch {
    return iso
  }
}

export function EventDetailPage() {
  const { id = "" } = useParams<{ id: string }>()
  const { user, isAuthenticated } = useAuthStore()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [message, setMessage] = useState<{ kind: "ok" | "err"; text: string } | null>(null)

  const eventQuery = useQuery({
    queryKey: ["event", id],
    queryFn: () => eventsApi.get(id),
    enabled: !!id,
  })

  const sessionsQuery = useQuery({
    queryKey: ["event-sessions", id],
    queryFn: () => eventsApi.listSessions(id),
    enabled: !!id,
  })

  const registerMutation = useMutation({
    mutationFn: () => eventsApi.register(id),
    onSuccess: () => {
      setMessage({ kind: "ok", text: "Te has inscrito al evento" })
      queryClient.invalidateQueries({ queryKey: ["my-events"] })
    },
    onError: (err) => {
      setMessage({ kind: "err", text: extractErrorMessage(err, "No se pudo inscribir") })
    },
  })

  const publishMutation = useMutation({
    mutationFn: () => eventsApi.publish(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["event", id] })
      queryClient.invalidateQueries({ queryKey: ["events"] })
    },
    onError: (err) =>
      setMessage({ kind: "err", text: extractErrorMessage(err, "No se pudo publicar") }),
  })

  const cancelMutation = useMutation({
    mutationFn: () => eventsApi.cancel(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["event", id] })
    },
    onError: (err) =>
      setMessage({ kind: "err", text: extractErrorMessage(err, "No se pudo cancelar") }),
  })

  if (eventQuery.isLoading) {
    return <div className="max-w-4xl mx-auto px-4 py-8 text-muted-foreground">Cargando...</div>
  }

  if (eventQuery.error || !eventQuery.data) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="rounded-md bg-destructive/10 border border-destructive text-destructive px-4 py-3">
          Evento no encontrado
        </div>
      </div>
    )
  }

  const event = eventQuery.data
  const isOwnerOrAdmin = user && (user.id === event.organizer_id || user.role === "admin")

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold">{event.name}</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Estado:{" "}
            <span className="font-medium text-foreground">{event.status}</span>
          </p>
        </div>
        <div className="flex gap-2">
          {isAuthenticated && event.status === "publicado" && (
            <button
              type="button"
              onClick={() => registerMutation.mutate()}
              disabled={registerMutation.isPending}
              className="px-4 py-2 rounded-md bg-primary text-primary-foreground disabled:opacity-50"
            >
              {registerMutation.isPending ? "Inscribiendo..." : "Inscribirme"}
            </button>
          )}
          {isOwnerOrAdmin && (
            <>
              <button
                type="button"
                onClick={() => navigate(`/events/${event.id}/edit`)}
                className="px-4 py-2 rounded-md border hover:bg-secondary"
              >
                Editar
              </button>
              {event.status === "borrador" && (
                <button
                  type="button"
                  onClick={() => publishMutation.mutate()}
                  className="px-4 py-2 rounded-md bg-green-600 text-white hover:opacity-90"
                >
                  Publicar
                </button>
              )}
              {(event.status === "borrador" || event.status === "publicado") && (
                <button
                  type="button"
                  onClick={() => {
                    if (confirm("Seguro que quieres cancelar el evento?")) {
                      cancelMutation.mutate()
                    }
                  }}
                  className="px-4 py-2 rounded-md bg-destructive text-destructive-foreground hover:opacity-90"
                >
                  Cancelar
                </button>
              )}
            </>
          )}
        </div>
      </div>

      {message && (
        <div
          role="alert"
          className={`rounded-md px-4 py-3 ${
            message.kind === "ok"
              ? "bg-green-50 border border-green-300 text-green-800"
              : "bg-destructive/10 border border-destructive text-destructive"
          }`}
        >
          {message.text}
        </div>
      )}

      <div className="rounded-lg border bg-card p-6">
        <h2 className="font-semibold mb-2">Descripcion</h2>
        <p className="text-sm text-muted-foreground whitespace-pre-line">
          {event.description || "Sin descripcion"}
        </p>
      </div>

      <div className="rounded-lg border bg-card p-6 grid sm:grid-cols-2 gap-4 text-sm">
        <div>
          <p className="text-muted-foreground">Inicio</p>
          <p className="font-medium">{formatDate(event.start_date)}</p>
        </div>
        <div>
          <p className="text-muted-foreground">Fin</p>
          <p className="font-medium">{formatDate(event.end_date)}</p>
        </div>
        <div>
          <p className="text-muted-foreground">Lugar</p>
          <p className="font-medium">{event.location || "—"}</p>
        </div>
        <div>
          <p className="text-muted-foreground">Capacidad</p>
          <p className="font-medium">{event.capacity}</p>
        </div>
      </div>

      <div>
        <h2 className="text-xl font-semibold mb-3">Sesiones</h2>
        {sessionsQuery.isLoading && (
          <div className="text-muted-foreground text-sm">Cargando sesiones...</div>
        )}
        {sessionsQuery.data && sessionsQuery.data.length === 0 && (
          <div className="text-muted-foreground text-sm">
            Este evento aun no tiene sesiones programadas.
          </div>
        )}
        {sessionsQuery.data && sessionsQuery.data.length > 0 && (
          <div className="space-y-2">
            {sessionsQuery.data.map((s) => (
              <div key={s.id} className="rounded-md border bg-card p-4">
                <div className="flex items-start justify-between gap-2">
                  <h3 className="font-medium">{s.title}</h3>
                  <span className="text-xs text-muted-foreground">
                    Cupo: {s.capacity}
                  </span>
                </div>
                <p className="text-sm text-muted-foreground mt-1">
                  {formatDate(s.start_time)} — {formatDate(s.end_time)}
                </p>
                {s.description && (
                  <p className="text-sm mt-2 whitespace-pre-line">{s.description}</p>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
