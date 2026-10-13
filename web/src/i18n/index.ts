// Fixed UI (user interface) text and page language (ADR (architecture decision record) 0002).
// The API (application programming interface) decides the initial language based on the browser;
// the switcher choice is saved in localStorage and takes precedence.
import { createContext, useContext, useEffect } from "react";

import en from "./en.json";
import es from "./es.json";

export type Lang = "es" | "en";
export type MessageKey = keyof typeof es;

// The type forces en.json to have the same keys as es.json.
const messages: Record<Lang, Record<MessageKey, string>> = { es, en };

export const LANGS: readonly Lang[] = ["es", "en"];
export const DEFAULT_LANG: Lang = "es";
const STORAGE_KEY = "lang";

export function isLang(value: unknown): value is Lang {
  return value === "es" || value === "en";
}

export function translate(lang: Lang, key: MessageKey): string {
  return messages[lang][key];
}

/**
 * Picks the text for the language from an API object: `localized(project, "title", "en")` →
 * `title_en`.
 */
export function localized<F extends string>(
  item: Record<`${F}_${Lang}`, string>,
  field: F,
  lang: Lang,
): string {
  return item[`${field}_${lang}`];
}

// localStorage can fail (private or blocked mode); then the choice lasts only for the visit.
export function storedLang(): Lang | null {
  try {
    const value = localStorage.getItem(STORAGE_KEY);
    return isLang(value) ? value : null;
  } catch {
    return null;
  }
}

export function storeLang(lang: Lang): void {
  try {
    localStorage.setItem(STORAGE_KEY, lang);
  } catch {
    // No storage available: ignored.
  }
}

interface LangState {
  lang: Lang;
  setLang: (lang: Lang) => void;
}

export const LangContext = createContext<LangState>({
  lang: DEFAULT_LANG,
  setLang: () => undefined,
});

export function useLang() {
  const { lang, setLang } = useContext(LangContext);
  return { lang, setLang, t: (key: MessageKey) => translate(lang, key) };
}

/**
 * Document language, title and description (SEO (search engine optimization) and screen
 * readers). There is a single URL for both languages, so `hreflang` isn't used: the language goes
 * in `<html lang>`.
 */
export function useDocumentMeta(lang: Lang, title: string, noindex = false): void {
  useEffect(() => {
    document.documentElement.lang = lang;
    document.title = title;
    let meta = document.querySelector<HTMLMetaElement>('meta[name="description"]');
    if (!meta) {
      meta = document.createElement("meta");
      meta.name = "description";
      document.head.append(meta);
    }
    meta.content = translate(lang, "meta.description");
    // The admin panel isn't indexed: robots.txt only asks crawlers not to crawl it, and an
    // external link would be enough.
    if (!noindex) return;
    const robots = document.createElement("meta");
    robots.name = "robots";
    robots.content = "noindex";
    document.head.append(robots);
    return () => {
      robots.remove();
    };
  }, [lang, title, noindex]);
}
