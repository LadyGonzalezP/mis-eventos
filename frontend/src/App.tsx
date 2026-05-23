/**
 * Componente raiz de la app.
 *
 * Pagina de bienvenida temporal - las rutas reales se agregan en Slice 1+:
 *   /login, /register, /events, /events/:id, /me/events, etc.
 */
function App() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-8">
      <div className="max-w-2xl text-center space-y-6">
        <div className="space-y-2">
          <h1 className="text-4xl md:text-5xl font-bold tracking-tight text-foreground">
            Mis Eventos
          </h1>
          <p className="text-lg text-muted-foreground">
            Plataforma de gestion de eventos
          </p>
          <p className="text-sm text-muted-foreground">
            Reto tecnico Serviinformacion 2026
          </p>
        </div>

        <div className="rounded-lg border bg-card p-6 text-left">
          <h2 className="font-semibold text-card-foreground mb-3">
            Estado del proyecto
          </h2>
          <ul className="space-y-2 text-sm text-muted-foreground">
            <li>✅ Backend FastAPI corriendo</li>
            <li>✅ PostgreSQL conectada</li>
            <li>✅ Frontend React + Vite + Tailwind listo</li>
            <li>⏳ Auth + RBAC (siguiente slice)</li>
          </ul>
        </div>

        <div className="text-xs text-muted-foreground">
          <a
            href="http://localhost:8000/docs"
            className="underline hover:text-foreground"
            target="_blank"
            rel="noopener noreferrer"
          >
            Ver API Swagger →
          </a>
        </div>
      </div>
    </div>
  )
}

export default App
