import { Link, useNavigate, useParams } from "react-router";

import { useProject } from "../api/projects";
import { ProjectForm } from "../components/ProjectForm";
import { ProjectImages } from "../components/ProjectImages";
import { useLang } from "../i18n";

/** Creates a project (`/admin/projects/new`) or edits an existing one (`/admin/projects/:id`). */
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
      {/* The form waits for fresh data: saving replaces the whole project, and a stale copy from
          the cache would overwrite newer changes. `key` rebuilds it for another project. */}
      {project && !isFetching && (
        <ProjectForm key={project.id} project={project} onSaved={backToList} />
      )}
      {projectId === undefined && <p>{t("admin.images.saveFirst")}</p>}
      {project && <ProjectImages project={project} />}
    </>
  );
}
