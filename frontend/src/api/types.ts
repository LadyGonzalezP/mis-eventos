/** Tipos compartidos con el backend - reflejan los Pydantic schemas. */

export type UserRole = "asistente" | "organizador" | "admin"

export type EventStatus = "borrador" | "publicado" | "cancelado" | "finalizado"

export interface User {
  id: string
  name: string
  email: string
  role: UserRole
  created_at: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  user: User
}

export interface Event {
  id: string
  name: string
  description: string
  start_date: string
  end_date: string
  location: string
  capacity: number
  status: EventStatus
  organizer_id: string
  created_at: string
  updated_at: string
}

export interface EventListResponse {
  items: Event[]
  total: number
  page: number
  limit: number
}

export interface Speaker {
  id: string
  name: string
  bio: string
  email: string | null
  created_at: string
}

export interface SessionItem {
  id: string
  event_id: string
  title: string
  description: string
  start_time: string
  end_time: string
  capacity: number
  speaker_id: string | null
}

export interface Registration {
  id: string
  event_id: string
  user_id: string
  registered_at: string
}

export interface MyEvent {
  event_id: string
  event_name: string
  event_status: EventStatus
  start_date: string
  end_date: string
  location: string
  registered_at: string
}
