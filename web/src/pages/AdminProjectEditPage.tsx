import { Link, useNavigate, useParams } from "react-router";

import { useProject } from "../api/projects";
import { ProjectForm } from "../components/ProjectForm";
import { ProjectImages } from "../components/ProjectImages";
import { useLang } from "../i18n";

/** Crea un proyecto (`/admin/projects/new`) o edita uno existente (`/admin/projects/:id`). */
export function AdminProjectEditPage() {
  const { t } = useLang();
  const navigate = useNavigate();
  const { id } = useParams();
  const projectId = id === undefined ? undefined : Number(id);
  const { data: project, isError, isFetching } = useProject(projectId);

  function backToList() {
    void navigate("/admin/projects");
  }

  return (
    <>
      <p>
        <Link to="/admin/projects">{t("admin.projects.title")}</Link>
      </p>
      <h1>{t(projectId === undefined ? "admin.projects.new" : "admin.projects.edit")}</h1>
      {isError && <p role="alert">{t("admin.projects.notFound")}</p>}
      {projectId === undefined && <ProjectForm onSaved={backToList} />}
      {/* El formulario espera el dato fresco: guardar reemplaza el proyecto completo, y una copia
          vieja de la cache pisaría cambios más nuevos. `key` lo rearma con otro proyecto. */}
      {project && !isFetching && (
        <ProjectForm key={project.id} project={project} onSaved={backToList} />
      )}
      {projectId === undefined && <p>{t("admin.images.saveFirst")}</p>}
      {project && <ProjectImages project={project} />}
    </>
  );
}
