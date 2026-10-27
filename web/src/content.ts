// Helpers to display the content that comes from `bootstrap`.
import type { PublicProject } from "./api/bootstrap";
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

/** The name at the start of a headline like `Ana Pérez · Backend developer`. */
export function headlineName(headline: string): string {
  return (headline.split(" · ")[0] ?? headline).trim();
}

/** The repository of the project whose demo is this same site, for the footer link. */
export function ownRepoUrl(projects: PublicProject[], host: string): string | null {
  const own = projects.find((project) => {
    const demo = httpsUrl(project.demo_url);
    return demo !== null && new URL(demo).host === host;
  });
  return httpsUrl(own?.repo_url);
}
