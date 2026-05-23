import { apiClient } from "./client"
import type {
  Event,
  EventListResponse,
  EventStatus,
  MyEvent,
  Registration,
  SessionItem,
} from "./types"

export interface ListEventsParams {
  q?: string
  status?: EventStatus
  date_from?: string
  date_to?: string
  page?: number
  limit?: number
}

export interface EventCreatePayload {
  name: string
  description: string
  start_date: string
  end_date: string
  location: string
  capacity: number
}

export const eventsApi = {
  list: (params?: ListEventsParams) =>
    apiClient.get<EventListResponse>("/api/v1/events", { params }).then((r) => r.data),

  get: (id: string) =>
    apiClient.get<Event>(`/api/v1/events/${id}`).then((r) => r.data),

  create: (payload: EventCreatePayload) =>
    apiClient.post<Event>("/api/v1/events", payload).then((r) => r.data),

  update: (id: string, payload: Partial<EventCreatePayload>) =>
    apiClient.patch<Event>(`/api/v1/events/${id}`, payload).then((r) => r.data),

  delete: (id: string) => apiClient.delete(`/api/v1/events/${id}`),

  publish: (id: string) =>
    apiClient.post<Event>(`/api/v1/events/${id}/publish`).then((r) => r.data),

  cancel: (id: string) =>
    apiClient.post<Event>(`/api/v1/events/${id}/cancel`).then((r) => r.data),

  listSessions: (eventId: string) =>
    apiClient.get<SessionItem[]>(`/api/v1/events/${eventId}/sessions`).then((r) => r.data),

  register: (eventId: string) =>
    apiClient.post<Registration>(`/api/v1/events/${eventId}/register`).then((r) => r.data),

  cancelRegistration: (eventId: string) =>
    apiClient.delete(`/api/v1/events/${eventId}/register`),

  myRegistrations: () =>
    apiClient.get<MyEvent[]>("/api/v1/me/registrations").then((r) => r.data),

  generateDescription: (title: string) =>
    apiClient
      .post<{ description: string }>("/api/v1/ai/generate-description", { title })
      .then((r) => r.data),
}
