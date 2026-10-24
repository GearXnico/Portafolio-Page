// The page's HTTP security headers. Locally Vite sets them; in production Caddy sets them with
// these same values (deploy/Caddyfile). The E2E test (e2e/security.spec.ts) checks them, also
// against Caddy in the CI deploy-check job.

/** CSP: only content from the same domain is loaded. */
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

/** Headers sent on every response, in development too. */
export const securityHeaders: Record<string, string> = {
  // The browser doesn't guess the file type (avoids running text as a script).
  "X-Content-Type-Options": "nosniff",
  // Nobody can show the page inside an iframe (clickjacking).
  "X-Frame-Options": "DENY",
  // When following a link to another site, only the domain is sent, not the full path.
  "Referrer-Policy": "strict-origin-when-cross-origin",
  // The page doesn't use the camera, microphone, location or payments.
  "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=()",
  // Isolates the window from windows it opens or that open it (cross-tab attacks).
  "Cross-Origin-Opener-Policy": "same-origin",
};

/**
 * Headers for the served build (vite preview and production): the ones above plus the CSP. `npm run
 * dev` doesn't send the CSP, because Vite and React inject an inline script for live reload and the
 * CSP would block it.
 */
export const productionHeaders: Record<string, string> = {
  ...securityHeaders,
  "Content-Security-Policy": contentSecurityPolicy,
};
