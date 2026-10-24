// UTM: read from the page URL.

export const UTM_KEYS = ["utm_source", "utm_medium", "utm_campaign", "utm_content"] as const;
export type UtmKey = (typeof UTM_KEYS)[number];
export type Utm = Partial<Record<UtmKey, string>>;

// The same length and the same characters that `POST /api/contact` rejects (schemas/text.py): an
// odd link must not leave the visitor unable to write.
const UTM_MAX_LENGTH = 200;
// eslint-disable-next-line no-control-regex
const CONTROL = /[\u0000-\u001f\u007f-\u009f\u2028\u2029]/g;

/** The UTM parameters from the URL, cleaned and trimmed. Missing or empty ones are left out. */
export function readUtm(search: string = window.location.search): Utm {
  const params = new URLSearchParams(search);
  const utm: Utm = {};
  for (const key of UTM_KEYS) {
    const raw = params.get(key);
    if (raw === null) continue;
    // Trimmed by characters, not by UTF-16 code units, so an emoji isn't split.
    const value = Array.from(raw.replace(CONTROL, "").trim())
      .slice(0, UTM_MAX_LENGTH)
      .join("")
      .trim();
    if (value) utm[key] = value;
  }
  return utm;
}
