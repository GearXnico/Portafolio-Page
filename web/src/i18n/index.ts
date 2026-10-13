// Textos fijos de la interfaz e idioma de la página (ADR 0002). La API decide el idioma
// inicial según el navegador; la elección del selector se guarda en localStorage y manda.
import { createContext, useContext, useEffect } from "react";

import en from "./en.json";
import es from "./es.json";

export type Lang = "es" | "en";
export type MessageKey = keyof typeof es;

// El tipo obliga a que en.json tenga las mismas claves que es.json.
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

/** Elige el texto del idioma en un objeto de la API: `localized(project, "title", "en")` → `title_en`. */
export function localized<F extends string>(
  item: Record<`${F}_${Lang}`, string>,
  field: F,
  lang: Lang,
): string {
  return item[`${field}_${lang}`];
}

// localStorage puede fallar (modo privado o bloqueado); entonces la elección dura solo la visita.
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
    // Sin almacenamiento disponible: se ignora.
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
 * Idioma, título y descripción del documento (SEO y lectores de pantalla). Hay una sola URL
 * para los dos idiomas, así que no se usa `hreflang`: el idioma va en `<html lang>`.
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
    // El panel no se indexa: robots.txt solo pide no rastrearlo, y un enlace externo bastaría.
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
