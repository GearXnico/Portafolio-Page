import type { PublicProject } from "../api/bootstrap";
import { localized, useLang } from "../i18n";

interface Props {
  projects: PublicProject[];
}

/**
 * Proyectos publicados (la API ya deja fuera los ocultos). Las capturas, el stack y los
 * enlaces a demo y repositorio llegan en la tarea 3.3.
 */
export function ProjectsSection({ projects }: Props) {
  const { lang, t } = useLang();
  if (projects.length === 0) return null;

  return (
    <section id="projects" aria-labelledby="projects-title">
      <h2 id="projects-title">{t("section.projects")}</h2>
      <ul className="projects">
        {projects.map((project) => (
          <li key={project.slug}>
            <article>
              <h3>{localized(project, "title", lang)}</h3>
              <p>{localized(project, "summary", lang)}</p>
            </article>
          </li>
        ))}
      </ul>
    </section>
  );
}
