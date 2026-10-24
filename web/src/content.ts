// Helpers to display the content that comes from `bootstrap`.
import type { Lang } from "./i18n";

/**
 * Returns the URL only if it is https. The API already requires it on save, but a `javascript:`
 * link in an `href` would run code, so the page checks it too.
 */
export function httpsUrl(value: string | null | undefined): string | null {
  if (!value) return null;
  try {
    return new URL(value).protocol === "https:" ? value : null;
  } catch {
    return null;
  }
}

/** Month and year of a `YYYY-MM-DD` date, in UTC so the month doesn't change with the time zone. */
export function monthYear(isoDate: string, lang: Lang): string {
  return new Intl.DateTimeFormat(lang, {
    month: "short",
    year: "numeric",
    timeZone: "UTC",
  }).format(new Date(isoDate));
}
