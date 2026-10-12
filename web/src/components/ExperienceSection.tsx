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
      <h2 id="experience-title">{t("section.experience")}</h2>
      <ol className="experience">
        {experience.map((job) => (
          <li key={`${job.company}-${job.start_date}`}>
            <h3>
              {localized(job, "role", lang)} · {job.company}
            </h3>
            <p className="dates">
              <time dateTime={job.start_date}>{monthYear(job.start_date, lang)}</time>
              {" – "}
              {job.end_date ? (
                <time dateTime={job.end_date}>{monthYear(job.end_date, lang)}</time>
              ) : (
                t("experience.present")
              )}
            </p>
            <p>{localized(job, "description", lang)}</p>
          </li>
        ))}
      </ol>
    </section>
  );
}
