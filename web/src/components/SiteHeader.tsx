import { useLang } from "../i18n";
import { LanguageSwitcher } from "./LanguageSwitcher";

export type SectionId = "projects" | "experience" | "skills" | "contact";

interface Props {
  name: string;
  sections: SectionId[];
}

/** Sticky bar with the name, links to the sections on the page and the language switcher. */
export function SiteHeader({ name, sections }: Props) {
  const { t } = useLang();

  return (
    <header className="site-header">
      <nav aria-label={t("nav.label")}>
        <a className="brand" href="#top">
          {name}
        </a>
        <ul className="nav-links">
          {sections.map((id) => (
            <li key={id}>
              <a href={`#${id}`}>{t(`section.${id}`)}</a>
            </li>
          ))}
        </ul>
        <LanguageSwitcher />
      </nav>
    </header>
  );
}
