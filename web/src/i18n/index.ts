// Textos de la interfaz. La elección del idioma según el navegador llega en el hito 3 (ADR 0002).
import es from "./es.json";

export type MessageKey = keyof typeof es;

export function t(key: MessageKey): string {
  return es[key];
}
