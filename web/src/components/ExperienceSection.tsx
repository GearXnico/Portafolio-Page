import type { PublicExperience } from "../api/bootstrap";
import { monthYear } from "../content";
import { localized, useLang } from "../i18n";

interface Props {
  experience: PublicExperience[];
}

export function ExperienceSection({ experience }: Props) {
  const { lang, t } = useLang();
  if (experience.length === 0) return null;

  return (
    <section id="experience" aria-labelledby="experience-title">
      <p className="kicker" aria-hidden="true">
        {t("section.kicker.experience")}
      </p>
      <h2 id="experience-title">{t("section.experience")}</h2>
      <ol className="experience">
        {experience.map((job) => (
          <li key={`${job.company}-${job.start_date}`}>
            <p className="dates">
              <time dateTime={job.start_date}>{monthYear(job.start_date, lang)}</time>
              {" – "}
              {job.end_date ? (
                <time dateTime={job.end_date}>{monthYear(job.end_date, lang)}</time>
              ) : (
                t("experience.present")
              )}
            </p>
            <div>
              <h3>{job.company}</h3>
              <p className="job-role">{localized(job, "role", lang)}</p>
              <p>{localized(job, "description", lang)}</p>
            </div>
          </li>
        ))}
      </ol>
    </section>
  );
}
