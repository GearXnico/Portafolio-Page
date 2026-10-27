import type { PublicProject } from "../api/bootstrap";
import { httpsUrl } from "../content";
import { localized, useLang } from "../i18n";

interface Props {
  projects: PublicProject[];
}

/**
 * Published projects (the API already leaves out hidden ones) as case files: the first screenshot
 * framed like a film still, then the summary and a metadata column with the stack and the links.
 */
export function ProjectsSection({ projects }: Props) {
  const { lang, t } = useLang();
  if (projects.length === 0) return null;

  return (
    <section id="projects" aria-labelledby="projects-title">
      <h2 id="projects-title">{t("section.projects")}</h2>
      <ol className="projects">
        {projects.map((project, i) => {
          // The API returns the screenshots in order; the first one is the cover.
          const cover = project.images[0];
          const title = localized(project, "title", lang);
          const demo = httpsUrl(project.demo_url);
          const repo = httpsUrl(project.repo_url);
          return (
            <li key={project.slug}>
              <article>
                <div className="frame">
                  {cover ? (
                    <img src={cover.url} alt={localized(cover, "alt", lang)} loading="lazy" />
                  ) : (
                    <div className="frame-blank" aria-hidden="true">
                      {title}
                    </div>
                  )}
                  <span className="frame-label" aria-hidden="true">
                    {t("project.file")} {String(i + 1).padStart(3, "0")}
                  </span>
                  {demo && (
                    <span className="frame-label live" aria-hidden="true">
                      ● {t("project.live")}
                    </span>
                  )}
                </div>
                <div className="case">
                  <div>
                    <h3>{title}</h3>
                    <p>{localized(project, "summary", lang)}</p>
                  </div>
                  {(project.stack.length > 0 || demo || repo) && (
                    <dl className="case-meta">
                      {project.stack.length > 0 && (
                        <>
                          <dt>{t("project.stack")}</dt>
                          <dd>
                            <ul className="tags" aria-label={t("project.stack")}>
                              {/* The API doesn't prevent repeated names, so the key includes the position. */}
                              {project.stack.map((name, j) => (
                                <li key={`${String(j)}-${name}`}>{name}</li>
                              ))}
                            </ul>
                          </dd>
                        </>
                      )}
                      {(demo ?? repo) && (
                        <>
                          <dt>{t("project.access")}</dt>
                          <dd className="project-links">
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
                          </dd>
                        </>
                      )}
                    </dl>
                  )}
                </div>
              </article>
            </li>
          );
        })}
      </ol>
    </section>
  );
}
