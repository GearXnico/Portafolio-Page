import type { PublicSkill, SkillCategory } from "../api/bootstrap";
import { useLang } from "../i18n";

interface Props {
  skills: PublicSkill[];
}

/** Skills grouped by category, in the order they arrive from the API. */
export function SkillsSection({ skills }: Props) {
  const { t } = useLang();
  if (skills.length === 0) return null;

  const byCategory = new Map<SkillCategory, string[]>();
  for (const skill of skills) {
    byCategory.set(skill.category, [...(byCategory.get(skill.category) ?? []), skill.name]);
  }

  return (
    <section id="skills" aria-labelledby="skills-title">
      <h2 id="skills-title">{t("section.skills")}</h2>
      <dl className="skills">
        {[...byCategory].map(([category, names]) => (
          <div key={category} className="cut">
            <dt>{t(`skills.${category}`)}</dt>
            <dd>
              <ul className="tags">
                {names.map((name) => (
                  <li key={name}>{name}</li>
                ))}
              </ul>
            </dd>
          </div>
        ))}
      </dl>
    </section>
  );
}
