import { useState, type SubmitEvent } from "react";

import { useSaveProfile, type ProfileInput } from "../api/adminProfile";
import { useLang } from "../i18n";
import { BilingualField } from "./BilingualField";
import { FormStatus } from "./FormStatus";

// Los enlaces se editan como texto, uno por línea: «github https://github.com/…».
// Una línea que no trae justo nombre y URL, o un nombre repetido, no se envía: se avisa antes,
// en vez de perder un enlace en silencio. Lo demás lo valida la API (422).
function linksToText(links: Record<string, string>): string {
  return Object.entries(links)
    .map(([name, url]) => `${name} ${url}`)
    .join("\n");
}

function textToLinks(text: string): Record<string, string> | null {
  const links: Record<string, string> = {};
  for (const line of text.split("\n")) {
    const parts = line.trim().split(/\s+/).filter(Boolean);
    if (parts.length === 0) continue;
    const [name = "", url = ""] = parts;
    if (parts.length !== 2 || Object.hasOwn(links, name)) return null;
    links[name] = url;
  }
  return links;
}

/** Formulario del perfil; `initial` es lo guardado (o vacío si aún no hay perfil). */
export function ProfileForm({ initial }: { initial: ProfileInput }) {
  const { t } = useLang();
  const save = useSaveProfile();
  const [profile, setProfile] = useState(initial);
  const [links, setLinks] = useState(() => linksToText(initial.links));
  const [invalidLinks, setInvalidLinks] = useState(false);

  function handleSubmit(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    const parsedLinks = textToLinks(links);
    setInvalidLinks(parsedLinks === null);
    if (parsedLinks === null) return;
    // Solo los campos que acepta la API: la respuesta trae además `updated_at`.
    const { headline_es, headline_en, about_es, about_en, contact_email } = profile;
    save.mutate({
      headline_es,
      headline_en,
      about_es,
      about_en,
      contact_email,
      links: parsedLinks,
    });
  }

  return (
    <form className="form" onSubmit={handleSubmit}>
      <BilingualField
        label={t("admin.profile.headline")}
        values={{ es: profile.headline_es, en: profile.headline_en }}
        onChange={(lang, value) => {
          setProfile({ ...profile, [`headline_${lang}`]: value });
        }}
        maxLength={200}
        required
      />
      <BilingualField
        label={t("admin.profile.about")}
        values={{ es: profile.about_es, en: profile.about_en }}
        onChange={(lang, value) => {
          setProfile({ ...profile, [`about_${lang}`]: value });
        }}
        maxLength={5000}
        multiline
        required
      />
      <label>
        {t("admin.profile.email")}
        <input
          type="email"
          required
          maxLength={320}
          value={profile.contact_email}
          onChange={(event) => {
            setProfile({ ...profile, contact_email: event.target.value });
          }}
        />
      </label>
      <label>
        {t("admin.profile.links")}
        <textarea
          rows={4}
          value={links}
          onChange={(event) => {
            setLinks(event.target.value);
          }}
        />
      </label>
      {invalidLinks ? (
        <p role="alert">{t("admin.form.invalid")}</p>
      ) : (
        <FormStatus error={save.error} saved={save.isSuccess} />
      )}
      <button type="submit" disabled={save.isPending}>
        {t("admin.form.save")}
      </button>
    </form>
  );
}
