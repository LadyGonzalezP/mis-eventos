import { Link } from "react-router-dom"

interface NotFoundProps {
  code?: 404 | 403
}

export function NotFoundPage({ code = 404 }: NotFoundProps) {
  const isForbidden = code === 403
  return (
    <div className="max-w-md mx-auto px-4 py-16 text-center">
      <h1 className="text-6xl font-bold text-muted-foreground mb-4">{code}</h1>
      <p className="text-xl mb-6">
        {isForbidden ? "No tienes permisos para esta pagina" : "Pagina no encontrada"}
      </p>
      <Link to="/events" className="text-primary hover:underline">
        Volver al inicio
      </Link>
    </div>
  )
}
