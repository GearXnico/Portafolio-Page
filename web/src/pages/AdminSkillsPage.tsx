import { Link } from "react-router";

import { useAdminSkills } from "../api/adminProfile";
import { SkillForm } from "../components/SkillForm";
import { useLang } from "../i18n";

/** Habilidades: una fila editable por cada una y un formulario para agregar otra. */
export function AdminSkillsPage() {
  const { t } = useLang();
  const { data, isError } = useAdminSkills();

  return (
    <>
      <Link to="/admin">{t("admin.back")}</Link>
      <h1>{t("admin.skills.title")}</h1>
      {isError && <p role="alert">{t("admin.error")}</p>}
      {data?.map((skill) => (
        <SkillForm key={skill.id} skill={skill} />
      ))}
      <h2>{t("admin.skills.new")}</h2>
      <SkillForm />
    </>
  );
}
