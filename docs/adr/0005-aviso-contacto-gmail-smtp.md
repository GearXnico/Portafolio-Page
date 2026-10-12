# 0005 · Aviso de contacto por SMTP de Gmail

Estado: aceptada · Fecha: 2026-10-11 · Decidió: Nicolas

## Contexto

Cada mensaje del formulario de contacto se guarda en la base y además tiene que llegarle a Nicolas por correo. El único destinatario es él.

## Opciones consideradas

| Opción | Costo | Contras |
|---|---|---|
| A. SMTP (protocolo de envío de correo) de Gmail con contraseña de aplicación | Gratis, ~30 min | Requiere verificación en dos pasos; el correo sale desde su propia cuenta |
| B. Resend (3.000 correos al mes y 100 al día gratis) | Gratis, ~1 h | Hay que verificar el dominio con registros DNS (sistema de nombres de dominio) |

## Decisión

A. El envío corre en una tarea de fondo de FastAPI y queda detrás de una sola función.

## Consecuencias

- Si el correo falla, el mensaje igual queda guardado y se ve en el panel (columna `emailed`).
- Si más adelante hace falta enviar correos a terceros, se cambia a B tocando solo esa función.
- La contraseña de aplicación vive solo en el `.env` del servidor.
