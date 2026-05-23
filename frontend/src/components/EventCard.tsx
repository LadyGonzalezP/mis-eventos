import { Link } from "react-router-dom"
import type { Event } from "@/api/types"

interface EventCardProps {
  event: Event
}

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

const statusColors: Record<Event["status"], string> = {
  borrador: "bg-muted text-muted-foreground",
  publicado: "bg-green-100 text-green-800",
  cancelado: "bg-destructive/10 text-destructive",
  finalizado: "bg-secondary text-secondary-foreground",
}

export function EventCard({ event }: EventCardProps) {
  return (
    <Link
      to={`/events/${event.id}`}
      className="block border rounded-lg p-4 bg-card hover:shadow-md transition-shadow"
    >
      <div className="flex items-start justify-between gap-2 mb-2">
        <h3 className="font-semibold text-card-foreground line-clamp-1">{event.name}</h3>
        <span
          className={`text-xs px-2 py-0.5 rounded-full ${statusColors[event.status]}`}
        >
          {event.status}
        </span>
      </div>

      <p className="text-sm text-muted-foreground line-clamp-2 mb-3">
        {event.description || "Sin descripcion"}
      </p>

      <div className="text-xs text-muted-foreground space-y-1">
        <div>📅 {formatDate(event.start_date)}</div>
        {event.location && <div>📍 {event.location}</div>}
        <div>👥 Capacidad: {event.capacity}</div>
      </div>
    </Link>
  )
}
