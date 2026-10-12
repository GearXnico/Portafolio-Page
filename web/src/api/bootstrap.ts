// Primera carga de la página: GET /api/bootstrap (tarea 2.2).
import { useQuery } from "@tanstack/react-query";

import { storedLang, type Lang } from "../i18n";

export interface PublicProfile {
  headline_es: string;
  headline_en: string;
  about_es: string;
  about_en: string;
  links: Record<string, string>;
}

export interface PublicSkill {
  name: string;
  category: string;
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

// Si la API no responde a tiempo, la página sale con el idioma por defecto en vez de quedar en blanco.
export const BOOTSTRAP_TIMEOUT_MS = 5000;

export async function fetchBootstrap(
  signal?: AbortSignal,
  timeoutMs = BOOTSTRAP_TIMEOUT_MS,
): Promise<Bootstrap> {
  // El idioma guardado viaja como `lang` para que la API lo use y lo registre en la visita.
  const params = new URLSearchParams();
  const lang = storedLang();
  if (lang) params.set("lang", lang);
  const query = params.toString();
  const timeout = AbortSignal.timeout(timeoutMs);
  const response = await fetch(query ? `/api/bootstrap?${query}` : "/api/bootstrap", {
    signal: signal ? AbortSignal.any([signal, timeout]) : timeout,
  });
  if (!response.ok) throw new Error(`bootstrap respondió ${String(response.status)}`);
  return (await response.json()) as Bootstrap;
}

/** Se pide una sola vez por visita: cada llamada registra una visita en la API. */
export function useBootstrap() {
  return useQuery({
    queryKey: ["bootstrap"],
    queryFn: ({ signal }) => fetchBootstrap(signal),
    staleTime: Infinity,
    retry: false,
  });
}
