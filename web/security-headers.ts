// Cabeceras HTTP de seguridad de la página. En local las pone Vite; en producción las pone
// Caddy con estos mismos valores (deploy/Caddyfile). El E2E (e2e/security.spec.ts) las verifica,
// también contra Caddy en el job deploy-check de CI.

/** CSP (política de seguridad de contenido): solo se carga lo que viene del mismo dominio. */
export const contentSecurityPolicy = [
  "default-src 'self'",
  "script-src 'self'",
  "style-src 'self'",
  "img-src 'self' data:",
  "font-src 'self'",
  "connect-src 'self'",
  "object-src 'none'",
  "base-uri 'self'",
  "form-action 'self'",
  "frame-ancestors 'none'",
].join("; ");

/** Cabeceras que van en todas las respuestas, también en desarrollo. */
export const securityHeaders: Record<string, string> = {
  // El navegador no adivina el tipo de archivo (evita ejecutar texto como script).
  "X-Content-Type-Options": "nosniff",
  // Nadie puede mostrar la página dentro de un iframe (clickjacking).
  "X-Frame-Options": "DENY",
  // Al seguir un enlace a otro sitio, solo se envía el dominio, no la ruta completa.
  "Referrer-Policy": "strict-origin-when-cross-origin",
  // La página no usa cámara, micrófono, ubicación ni pagos.
  "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=()",
  // Aísla la ventana de las que abra o la abran (ataques entre pestañas).
  "Cross-Origin-Opener-Policy": "same-origin",
};

/**
 * Cabeceras del build servido (vite preview y producción): las anteriores más la CSP.
 * En `npm run dev` no va la CSP, porque Vite y React inyectan un script en línea para la
 * recarga en vivo y la CSP lo bloquearía.
 */
export const productionHeaders: Record<string, string> = {
  ...securityHeaders,
  "Content-Security-Policy": contentSecurityPolicy,
};
