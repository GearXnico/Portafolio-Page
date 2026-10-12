# deploy/

Archivos de producción. Se completan en estas tareas del plan:

- 1.6: `compose.prod.yml` y `Caddyfile`, probados en CI (integración continua) con `deploy-check`. `TRUSTED_PROXIES` debe incluir la red interna de Docker de Caddy, para que la API vea la IP real del visitante (límite de contacto y visitantes únicos de `/api/bootstrap`).
- 5.3: `deploy.sh`, con respaldo, migraciones, health check y rollback.
- 5.4: `backup.sh`, con `pg_dump` diario.
