import { type FormEvent, useEffect, useState } from "react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useNavigate, useParams } from "react-router-dom"
import { extractErrorMessage } from "@/api/client"
import { eventsApi, type EventCreatePayload } from "@/api/events"

type FormState = EventCreatePayload

const empty: FormState = {
  name: "",
  description: "",
  start_date: "",
  end_date: "",
  location: "",
  capacity: 50,
}

export function EventFormPage() {
  const { id } = useParams<{ id: string }>()
  const isEdit = !!id
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [form, setForm] = useState<FormState>(empty)
  const [error, setError] = useState<string | null>(null)

  const editQuery = useQuery({
    queryKey: ["event", id],
    queryFn: () => eventsApi.get(id!),
    enabled: isEdit,
  })

  useEffect(() => {
    if (editQuery.data) {
      const e = editQuery.data
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setForm({
        name: e.name,
        description: e.description,
        start_date: e.start_date.slice(0, 16),
        end_date: e.end_date.slice(0, 16),
        location: e.location,
        capacity: e.capacity,
      })
    }
  }, [editQuery.data])

  const createMutation = useMutation({
    mutationFn: (payload: EventCreatePayload) => eventsApi.create(payload),
    onSuccess: (event) => {
      queryClient.invalidateQueries({ queryKey: ["events"] })
      navigate(`/events/${event.id}`, { replace: true })
    },
    onError: (err) => setError(extractErrorMessage(err, "No se pudo crear el evento")),
  })

  const updateMutation = useMutation({
    mutationFn: (payload: Partial<EventCreatePayload>) => eventsApi.update(id!, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["event", id] })
      queryClient.invalidateQueries({ queryKey: ["events"] })
      navigate(`/events/${id}`, { replace: true })
    },
    onError: (err) => setError(extractErrorMessage(err, "No se pudo actualizar")),
  })

  const onSubmit = (e: FormEvent) => {
    e.preventDefault()
    setError(null)
    const payload: EventCreatePayload = {
      name: form.name,
      description: form.description,
      start_date: new Date(form.start_date).toISOString(),
      end_date: new Date(form.end_date).toISOString(),
      location: form.location,
      capacity: Number(form.capacity),
    }
    if (isEdit) updateMutation.mutate(payload)
    else createMutation.mutate(payload)
  }

  const submitting = createMutation.isPending || updateMutation.isPending

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold mb-6">
        {isEdit ? "Editar evento" : "Crear evento"}
      </h1>

      <form onSubmit={onSubmit} className="space-y-4">
        <div>
          <label htmlFor="name" className="block text-sm font-medium mb-1">
            Nombre
          </label>
          <input
            id="name"
            type="text"
            required
            minLength={2}
            maxLength={200}
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            className="w-full px-3 py-2 border border-input rounded-md bg-background"
          />
        </div>

        <div>
          <div className="flex items-center justify-between mb-1">
            <label htmlFor="description" className="block text-sm font-medium">
              Descripcion
            </label>
            <button
              type="button"
              onClick={async () => {
                if (form.name.length < 3) {
                  setError("Escribe el nombre primero (minimo 3 caracteres)")
                  return
                }
                try {
                  setError(null)
                  const { description } = await eventsApi.generateDescription(form.name)
                  setForm((prev) => ({ ...prev, description }))
                } catch (err) {
                  setError(extractErrorMessage(err, "No se pudo generar"))
                }
              }}
              className="text-xs px-2 py-1 rounded-md border hover:bg-secondary"
              title="Genera la descripcion del evento con IA (Bonus)"
            >
              ✨ Generar con IA
            </button>
          </div>
          <textarea
            id="description"
            rows={4}
            maxLength={2000}
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
            className="w-full px-3 py-2 border border-input rounded-md bg-background"
          />
        </div>

        <div className="grid sm:grid-cols-2 gap-4">
          <div>
            <label htmlFor="start_date" className="block text-sm font-medium mb-1">
              Inicio
            </label>
            <input
              id="start_date"
              type="datetime-local"
              required
              value={form.start_date}
              onChange={(e) => setForm({ ...form, start_date: e.target.value })}
              className="w-full px-3 py-2 border border-input rounded-md bg-background"
            />
          </div>
          <div>
            <label htmlFor="end_date" className="block text-sm font-medium mb-1">
              Fin
            </label>
            <input
              id="end_date"
              type="datetime-local"
              required
              value={form.end_date}
              onChange={(e) => setForm({ ...form, end_date: e.target.value })}
              className="w-full px-3 py-2 border border-input rounded-md bg-background"
            />
          </div>
        </div>

        <div className="grid sm:grid-cols-2 gap-4">
          <div>
            <label htmlFor="location" className="block text-sm font-medium mb-1">
              Lugar
            </label>
            <input
              id="location"
              type="text"
              value={form.location}
              onChange={(e) => setForm({ ...form, location: e.target.value })}
              className="w-full px-3 py-2 border border-input rounded-md bg-background"
            />
          </div>
          <div>
            <label htmlFor="capacity" className="block text-sm font-medium mb-1">
              Capacidad
            </label>
            <input
              id="capacity"
              type="number"
              required
              min={1}
              value={form.capacity}
              onChange={(e) =>
                setForm({ ...form, capacity: Number(e.target.value) })
              }
              className="w-full px-3 py-2 border border-input rounded-md bg-background"
            />
          </div>
        </div>

        {error && (
          <div
            role="alert"
            className="rounded-md bg-destructive/10 border border-destructive text-destructive px-3 py-2 text-sm"
          >
            {error}
          </div>
        )}

        <div className="flex gap-2 pt-2">
          <button
            type="submit"
            disabled={submitting}
            className="px-4 py-2 rounded-md bg-primary text-primary-foreground hover:opacity-90 disabled:opacity-50"
          >
            {submitting
              ? "Guardando..."
              : isEdit
                ? "Guardar cambios"
                : "Crear evento"}
          </button>
          <button
            type="button"
            onClick={() => navigate(-1)}
            className="px-4 py-2 rounded-md border hover:bg-secondary"
          >
            Cancelar
          </button>
        </div>
      </form>
    </div>
  )
}
