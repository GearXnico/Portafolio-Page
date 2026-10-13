import { Link } from "react-router";

import { useProjects } from "../api/projects";
import { localized, useLang } from "../i18n";

/** Lista de proyectos del panel, en el orden de la página pública, con los ocultos marcados. */
export function AdminProjectsPage() {
  const { lang, t } = useLang();
  const { data: projects, isPending, isError } = useProjects();

  return (
    <>
      <p>
        <Link to="/admin">{t("admin.back")}</Link>
      </p>
      <h1>{t("admin.projects.title")}</h1>
      <p>
        <Link to="new">{t("admin.projects.new")}</Link>
      </p>
      {isError && <p role="alert">{t("admin.error")}</p>}
      {!isPending && projects?.length === 0 && <p>{t("admin.projects.empty")}</p>}
      {projects && projects.length > 0 && (
        <ol>
          {projects.map((project) => (
            <li key={project.id}>
              <Link to={String(project.id)}>{localized(project, "title", lang)}</Link>{" "}
              <span className="muted">
                {t("admin.projects.position")} {project.position}
                {!project.visible && ` · ${t("admin.projects.hidden")}`}
              </span>
            </li>
          ))}
        </ol>
      )}
    </>
  );
}
