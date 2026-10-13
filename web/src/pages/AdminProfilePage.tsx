import { Link } from "react-router";

import { useAdminProfile, type ProfileInput } from "../api/adminProfile";
import { ProfileForm } from "../components/ProfileForm";
import { useLang } from "../i18n";

const EMPTY: ProfileInput = {
  headline_es: "",
  headline_en: "",
  about_es: "",
  about_en: "",
  contact_email: "",
  links: {},
};

/** Profile editing: headline and introduction in both languages, email and links. */
export function AdminProfilePage() {
  const { t } = useLang();
  const { data, isPending, isError } = useAdminProfile();

  return (
    <>
      <Link to="/admin">{t("admin.back")}</Link>
      <h1>{t("admin.profile.title")}</h1>
      {isError && <p role="alert">{t("admin.error")}</p>}
      {!isPending && !isError && <ProfileForm initial={data ?? EMPTY} />}
    </>
  );
}
