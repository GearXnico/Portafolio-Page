// UTM (parámetros de origen del enlace): se leen de la URL de la página (tarea 3.5).

export const UTM_KEYS = ["utm_source", "utm_medium", "utm_campaign", "utm_content"] as const;
export type UtmKey = (typeof UTM_KEYS)[number];
export type Utm = Partial<Record<UtmKey, string>>;

// El mismo largo y los mismos caracteres que rechaza `POST /api/contact` (schemas/text.py):
// un enlace raro no debe dejar al visitante sin poder escribir.
const UTM_MAX_LENGTH = 200;
// eslint-disable-next-line no-control-regex
const CONTROL = /[\u0000-\u001f\u007f-\u009f\u2028\u2029]/g;

/** Las UTM de la URL, limpias y recortadas. Las que no vienen o quedan vacías no salen. */
export function readUtm(search: string = window.location.search): Utm {
  const params = new URLSearchParams(search);
  const utm: Utm = {};
  for (const key of UTM_KEYS) {
    const raw = params.get(key);
    if (raw === null) continue;
    // Se recorta por caracteres y no por unidades UTF-16, para no partir un emoji.
    const value = Array.from(raw.replace(CONTROL, "").trim())
      .slice(0, UTM_MAX_LENGTH)
      .join("")
      .trim();
    if (value) utm[key] = value;
  }
  return utm;
}
