# deploy/

Archivos de producción. Se completan en estas tareas del plan:

- 1.6: `compose.prod.yml` y `Caddyfile`, probados en CI (integración continua) con `deploy-check`.
- 5.3: `deploy.sh`, con respaldo, migraciones, health check y rollback.
- 5.4: `backup.sh`, con `pg_dump` diario.
