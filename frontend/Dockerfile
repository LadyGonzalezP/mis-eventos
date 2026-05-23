# syntax=docker/dockerfile:1.6

# --- Stage 1: build ---
FROM node:20-alpine AS build

WORKDIR /app

# Copiar archivos de deps primero (cache layer)
COPY package.json package-lock.json* ./
RUN npm ci --no-audit --no-fund

# Copiar codigo y build
COPY . .
RUN npm run build

# --- Stage 2: serve ---
FROM nginx:alpine

# Copiar el build estatico
COPY --from=build /app/dist /usr/share/nginx/html

# Config de nginx para SPA (manejo de rutas client-side)
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
