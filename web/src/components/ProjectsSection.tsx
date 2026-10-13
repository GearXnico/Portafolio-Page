import type { PublicProject } from "../api/bootstrap";
import { httpsUrl } from "../content";
import { localized, useLang } from "../i18n";

interface Props {
  projects: PublicProject[];
}

/**
 * Published projects (the API (application programming interface) already leaves out hidden
 * ones), with their first screenshot as the cover, the stack and the demo and repository links.
 */
export function ProjectsSection({ projects }: Props) {
  const { lang, t } = useLang();
  if (projects.length === 0) return null;

  return (
    <section id="projects" aria-labelledby="projects-title">
      <h2 id="projects-title">{t("section.projects")}</h2>
      <ul className="projects">
        {projects.map((project) => {
          // The API returns the screenshots in order; the first one is the cover.
          const cover = project.images[0];
          const demo = httpsUrl(project.demo_url);
          const repo = httpsUrl(project.repo_url);
          return (
            <li key={project.slug}>
              <article>
                {cover && (
                  <img src={cover.url} alt={localized(cover, "alt", lang)} loading="lazy" />
                )}
                <h3>{localized(project, "title", lang)}</h3>
                <p>{localized(project, "summary", lang)}</p>
                {project.stack.length > 0 && (
                  <ul className="tags" aria-label={t("project.stack")}>
                    {/* The API doesn't prevent repeated names, so the key includes the position. */}
                    {project.stack.map((name, i) => (
                      <li key={`${String(i)}-${name}`}>{name}</li>
                    ))}
                  </ul>
                )}
                {(demo ?? repo) && (
                  <p className="project-links">
                    {demo && (
                      <a href={demo} target="_blank" rel="noopener noreferrer">
                        {t("project.demo")}
                      </a>
                    )}
                    {repo && (
                      <a href={repo} target="_blank" rel="noopener noreferrer">
                        {t("project.repo")}
                      </a>
                    )}
                  </p>
                )}
              </article>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
