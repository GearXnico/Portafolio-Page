import { useState, type SubmitEvent } from "react";

import { ContactError, useSendContact } from "../api/contact";
import { useLang, type MessageKey } from "../i18n";
import { readUtm } from "../utm";

// Largos máximos de la API (docs/api.md): el navegador corta antes de enviar.
const MAX = { name: 200, email: 320, message: 5000 } as const;

const ERROR_KEYS: Record<ContactError["kind"], MessageKey> = {
  invalid: "contact.error.invalid",
  rateLimit: "contact.error.rateLimit",
  generic: "contact.error.generic",
};

/**
 * Formulario de contacto. La validación de los campos la hace el navegador (obligatorios,
 * largo y formato de correo) y la API vuelve a validar todo; si la API rechaza algo, se
 * muestra un mensaje según la causa, sin repetir el detalle técnico.
 */
export function ContactForm() {
  const { lang, t } = useLang();
  const send = useSendContact();
  const [sent, setSent] = useState(false);

  function handleSubmit(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    const field = (name: string) => {
      const value = data.get(name);
      return typeof value === "string" ? value : "";
    };
    setSent(false);
    // La API de contacto solo guarda estas dos UTM; cualquier otro campo lo rechaza.
    const { utm_source, utm_campaign } = readUtm();
    send.mutate(
      {
        name: field("name"),
        email: field("email"),
        message: field("message"),
        website: field("hp_field"),
        lang,
        ...(utm_source && { utm_source }),
        ...(utm_campaign && { utm_campaign }),
      },
      {
        onSuccess: () => {
          form.reset();
          setSent(true);
        },
      },
    );
  }

  const errorKind = send.error instanceof ContactError ? send.error.kind : "generic";

  return (
    <form className="contact-form" onSubmit={handleSubmit}>
      <label>
        {t("contact.name")}
        <input name="name" required maxLength={MAX.name} autoComplete="name" />
      </label>
      <label>
        {t("contact.email")}
        <input name="email" type="email" required maxLength={MAX.email} autoComplete="email" />
      </label>
      <label>
        {t("contact.message")}
        <textarea name="message" required maxLength={MAX.message} rows={6} />
      </label>
      {/* Campo trampa: fuera de la pantalla y sin foco, para que solo un bot lo llene. El nombre y
          la etiqueta no son comunes para que el autocompletado del navegador no lo llene. Viaja como `website`. */}
      <div className="trap" aria-hidden="true">
        <label>
          {t("contact.website")}
          <input name="hp_field" tabIndex={-1} autoComplete="off" />
        </label>
      </div>
      <button type="submit" disabled={send.isPending}>
        {send.isPending ? t("contact.sending") : t("contact.send")}
      </button>
      <p role="status">{sent ? t("contact.success") : ""}</p>
      {send.isError && <p role="alert">{t(ERROR_KEYS[errorKind])}</p>}
    </form>
  );
}
