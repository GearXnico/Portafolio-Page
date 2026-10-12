# Imagen de producción del sitio: Caddy con el build de web (deploy/compose.prod.yml).
# Necesita el contexto extra `deploy` con el Caddyfile:
#   docker build --build-context deploy=deploy web

# 1. Build estático de la página.
FROM node:24-alpine AS build

WORKDIR /code
COPY package.json package-lock.json .npmrc ./
RUN npm ci
COPY . .
RUN npm run build

# 2. Imagen final: Caddy, la página y el Caddyfile, sin Node ni npm.
FROM caddy:2.11-alpine

# El binario trae un permiso para abrir los puertos 80 y 443; Docker ya deja abrirlos sin él,
# y quitarlo permite correr sin ninguna capability. /data y /config guardan los certificados.
RUN setcap -r /usr/bin/caddy \
    && adduser -S -D -H -u 10002 caddy \
    && chown caddy /data /config

COPY --from=deploy Caddyfile /etc/caddy/Caddyfile
COPY --from=build /code/dist /srv/web

USER caddy
