# Production image for the site: Caddy with the web build (deploy/compose.prod.yml).
# It needs the extra `deploy` build context with the Caddyfile:
#   docker build --build-context deploy=deploy web

# 1. Static build of the page.
FROM node:24-alpine AS build

WORKDIR /code
COPY package.json package-lock.json .npmrc ./
RUN npm ci
COPY . .
RUN npm run build

# 2. Final image: Caddy, the page and the Caddyfile, without Node or npm.
FROM caddy:2.11-alpine

# The binary ships with a permission to bind ports 80 and 443; Docker already allows binding them
# without it, and removing it lets the container run with no capabilities. /data and /config hold
# the certificates.
RUN setcap -r /usr/bin/caddy \
    && adduser -S -D -H -u 10002 caddy \
    && chown caddy /data /config

COPY --from=deploy Caddyfile /etc/caddy/Caddyfile
COPY --from=build /code/dist /srv/web

USER caddy
