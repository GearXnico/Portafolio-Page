import type { PublicProfile } from "../api/bootstrap";
import { localized, useLang } from "../i18n";

interface Props {
  profile: PublicProfile | null;
}

/** Encabezado de la página: titular y presentación. Sin perfil cargado, solo el título. */
export function ProfileSection({ profile }: Props) {
  const { lang, t } = useLang();
  return (
    <header className="profile">
      <h1>{profile ? localized(profile, "headline", lang) : t("app.title")}</h1>
      {profile && <p className="about">{localized(profile, "about", lang)}</p>}
    </header>
  );
}
