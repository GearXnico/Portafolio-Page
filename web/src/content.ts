// Ayudas para mostrar el contenido que llega de `bootstrap`.
import type { Lang } from "./i18n";

/**
 * Devuelve la URL solo si es https. La API ya lo exige al guardar, pero un enlace con
 * `javascript:` en un `href` ejecutaría código, así que la página también lo revisa.
 */
export function httpsUrl(value: string | null | undefined): string | null {
  if (!value) return null;
  try {
    return new URL(value).protocol === "https:" ? value : null;
  } catch {
    return null;
  }
}

/** Mes y año de una fecha `YYYY-MM-DD`, en UTC para que no cambie de mes según la zona. */
export function monthYear(isoDate: string, lang: Lang): string {
  return new Intl.DateTimeFormat(lang, {
    month: "short",
    year: "numeric",
    timeZone: "UTC",
  }).format(new Date(isoDate));
}
