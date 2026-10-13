// Envío del formulario de contacto: POST /api/contact (tarea 2.6).
import { useMutation } from "@tanstack/react-query";

import type { Lang } from "../i18n";

export interface ContactInput {
  name: string;
  email: string;
  message: string;
  lang: Lang;
  // Origen del enlace con que llegó el visitante; solo van si vienen en la URL (tarea 3.5).
  utm_source?: string;
  utm_campaign?: string;
  // Campo trampa (honeypot): una persona lo deja vacío; si llega con algo, la API no guarda nada.
  website: string;
}

/** Lo que el formulario necesita saber de un envío fallido para elegir el mensaje. */
export type ContactErrorKind = "invalid" | "rateLimit" | "generic";

export class ContactError extends Error {
  constructor(readonly kind: ContactErrorKind) {
    super(`contacto falló: ${kind}`);
  }
}

export async function sendContact(input: ContactInput): Promise<void> {
  let response: Response;
  try {
    response = await fetch("/api/contact", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(input),
    });
  } catch {
    throw new ContactError("generic");
  }
  if (response.ok) return;
  if (response.status === 422) throw new ContactError("invalid");
  if (response.status === 429) throw new ContactError("rateLimit");
  throw new ContactError("generic");
}

export function useSendContact() {
  return useMutation({ mutationFn: sendContact });
}
