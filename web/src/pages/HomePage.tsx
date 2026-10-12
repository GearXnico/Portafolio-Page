import type { Bootstrap } from "../api/bootstrap";
import { ContactSection } from "../components/ContactSection";
import { ExperienceSection } from "../components/ExperienceSection";
import { LanguageSwitcher } from "../components/LanguageSwitcher";
import { ProfileSection } from "../components/ProfileSection";
import { ProjectsSection } from "../components/ProjectsSection";
import { SkillsSection } from "../components/SkillsSection";
import { useLang } from "../i18n";

interface Props {
  data: Bootstrap | undefined;
  isError: boolean;
}

/**
 * La página pública. El contenido llega de App, que hace la única llamada a `bootstrap`
 * (cada llamada registra una visita, así que no se pide de nuevo desde aquí).
 */
export function HomePage({ data, isError }: Props) {
  const { t } = useLang();

  return (
    <main className="page">
      <nav className="top">
        <LanguageSwitcher />
      </nav>
      <ProfileSection profile={data?.profile ?? null} />
      {isError && <p role="alert">{t("page.error")}</p>}
      {data && (
        <>
          <ProjectsSection projects={data.projects} />
          <ExperienceSection experience={data.experience} />
          <SkillsSection skills={data.skills} />
          <ContactSection links={data.profile?.links ?? {}} />
        </>
      )}
    </main>
  );
}
