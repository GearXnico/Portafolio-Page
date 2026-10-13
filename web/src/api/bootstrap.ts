// First page load: GET /api/bootstrap (task 2.2).
import { useQuery } from "@tanstack/react-query";

import { storedLang, type Lang } from "../i18n";
import { readUtm } from "../utm";

export interface PublicProfile {
  headline_es: string;
  headline_en: string;
  about_es: string;
  about_en: string;
  links: Record<string, string>;
}

// The allowed categories are set by the database (ck_skill_category).
export type SkillCategory = "language" | "framework" | "tool";

export interface PublicSkill {
  name: string;
  category: SkillCategory;
}

export interface PublicExperience {
  company: string;
  role_es: string;
  role_en: string;
  description_es: string;
  description_en: string;
  start_date: string;
  end_date: string | null;
}

export interface PublicImage {
  url: string;
  alt_es: string;
  alt_en: string;
}

export interface PublicProject {
  slug: string;
  title_es: string;
  title_en: string;
  summary_es: string;
  summary_en: string;
  body_es: string;
  body_en: string;
  stack: string[];
  demo_url: string | null;
  repo_url: string | null;
  images: PublicImage[];
}

export interface Bootstrap {
  lang: Lang;
  profile: PublicProfile | null;
  skills: PublicSkill[];
  experience: PublicExperience[];
  projects: PublicProject[];
}

// If the API (application programming interface) doesn't respond in time, the page renders in the
// default language instead of staying blank.
export const BOOTSTRAP_TIMEOUT_MS = 5000;

export async function fetchBootstrap(
  signal?: AbortSignal,
  timeoutMs = BOOTSTRAP_TIMEOUT_MS,
): Promise<Bootstrap> {
  // The UTM (Urchin Tracking Module) parameters from the URL and the referrer domain are recorded
  // with the visit (task 3.5). The saved language is sent as `lang` so the API uses it and records
  // it with the visit.
  const params = new URLSearchParams(readUtm());
  if (document.referrer) params.set("referrer", document.referrer);
  const lang = storedLang();
  if (lang) params.set("lang", lang);
  const query = params.toString();
  const timeout = AbortSignal.timeout(timeoutMs);
  const response = await fetch(query ? `/api/bootstrap?${query}` : "/api/bootstrap", {
    signal: signal ? AbortSignal.any([signal, timeout]) : timeout,
  });
  if (!response.ok) throw new Error(`bootstrap responded ${String(response.status)}`);
  return (await response.json()) as Bootstrap;
}

/** Fetched only once per visit: each call records a visit in the API. */
export function useBootstrap() {
  return useQuery({
    queryKey: ["bootstrap"],
    queryFn: ({ signal }) => fetchBootstrap(signal),
    staleTime: Infinity,
    retry: false,
  });
}
