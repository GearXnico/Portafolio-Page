// Contact form submission: POST /api/contact (task 2.6).
import { useMutation } from "@tanstack/react-query";

import type { Lang } from "../i18n";

export interface ContactInput {
  name: string;
  email: string;
  message: string;
  lang: Lang;
  // Source of the link the visitor came from; only sent if present in the URL (task 3.5).
  utm_source?: string;
  utm_campaign?: string;
  // Honeypot field: a person leaves it empty; if it arrives with a value, the API saves nothing.
  website: string;
}

/** What the form needs to know about a failed submission to pick the message. */
export type ContactErrorKind = "invalid" | "rateLimit" | "generic";

export class ContactError extends Error {
  constructor(readonly kind: ContactErrorKind) {
    super(`contact failed: ${kind}`);
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
