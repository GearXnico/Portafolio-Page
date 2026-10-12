# 0004 · Administrador único con credenciales en variables de entorno

Estado: aceptada · Fecha: 2026-10-11 · Propuso: Claude, aprobada con la arquitectura

## Contexto

El panel de administración tiene un solo usuario, Nicolas. Varios administradores o roles quedaron fuera del MVP (producto mínimo viable).

## Opciones consideradas

| Opción | Costo | Contras |
|---|---|---|
| A. Correo y hash Argon2 de la contraseña en variables de entorno; sesión con JWT (JSON Web Token, un token firmado) en una cookie `httpOnly` | ~3 h | Cambiar la contraseña requiere editar el `.env` del servidor y reiniciar |
| B. Tabla de usuarios con registro y recuperación de contraseña | ~8 h | Código y riesgos que no se necesitan |
| C. Login con GitHub (OAuth, autorización delegada) | ~5 h | Depende de GitHub y suma configuración |

## Decisión

A. La cookie es `httpOnly`, `Secure` y `SameSite=Strict`, y dura 7 días. El login permite como máximo 5 intentos fallidos cada 15 minutos por IP (dirección de red).

## Consecuencias

- No hay tabla de usuarios ni flujo de recuperación de contraseña. Si se olvida la contraseña, se genera un hash nuevo con un comando y se actualiza el `.env`.
- La cookie `SameSite=Strict` y el hecho de que frontend y API compartan dominio evitan tener que configurar CORS (restricción del navegador entre dominios) y protección CSRF (falsificación de peticiones entre sitios) aparte.
- Si más adelante hacen falta más administradores, se migra a B sin cambiar el resto de la API.
