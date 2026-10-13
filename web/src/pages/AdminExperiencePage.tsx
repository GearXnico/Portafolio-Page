import { Link } from "react-router";

import { useAdminExperience } from "../api/adminProfile";
import { ExperienceForm } from "../components/ExperienceForm";
import { useLang } from "../i18n";

/** Experiencia: un formulario por cada trabajo y uno para agregar otro. */
export function AdminExperiencePage() {
  const { t } = useLang();
  const { data, isError } = useAdminExperience();

  return (
    <>
      <Link to="/admin">{t("admin.back")}</Link>
      <h1>{t("admin.experience.title")}</h1>
      {isError && <p role="alert">{t("admin.error")}</p>}
      {data?.map((item) => (
        <ExperienceForm key={item.id} item={item} />
      ))}
      <h2>{t("admin.experience.new")}</h2>
      <ExperienceForm />
    </>
  );
}
