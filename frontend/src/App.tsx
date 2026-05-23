import { Navigate, Route, Routes } from "react-router-dom"
import { Layout } from "@/components/Layout"
import { ProtectedRoute } from "@/components/ProtectedRoute"
import { EventDetailPage } from "@/pages/EventDetail"
import { EventFormPage } from "@/pages/EventForm"
import { EventListPage } from "@/pages/EventList"
import { LoginPage } from "@/pages/Login"
import { MyEventsPage } from "@/pages/MyEvents"
import { NotFoundPage } from "@/pages/NotFound"
import { RegisterPage } from "@/pages/Register"

function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Navigate to="/events" replace />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />

        <Route path="/events" element={<EventListPage />} />
        <Route path="/events/:id" element={<EventDetailPage />} />

        <Route
          path="/events/new"
          element={
            <ProtectedRoute roles={["organizador", "admin"]}>
              <EventFormPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/events/:id/edit"
          element={
            <ProtectedRoute roles={["organizador", "admin"]}>
              <EventFormPage />
            </ProtectedRoute>
          }
        />

        <Route
          path="/me/events"
          element={
            <ProtectedRoute>
              <MyEventsPage />
            </ProtectedRoute>
          }
        />

        <Route path="/403" element={<NotFoundPage code={403} />} />
        <Route path="*" element={<NotFoundPage code={404} />} />
      </Route>
    </Routes>
  )
}

export default App
