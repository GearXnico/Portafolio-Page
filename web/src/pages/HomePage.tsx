import type { Bootstrap } from "../api/bootstrap";
import { ContactSection } from "../components/ContactSection";
import { ExperienceSection } from "../components/ExperienceSection";
import { ProfileSection } from "../components/ProfileSection";
import { ProjectsSection } from "../components/ProjectsSection";
import { SiteFooter } from "../components/SiteFooter";
import { SiteHeader, type SectionId } from "../components/SiteHeader";
import { SkillsSection } from "../components/SkillsSection";
import { headlineName, ownRepoUrl } from "../content";
import { localized, useLang } from "../i18n";

interface Props {
  data: Bootstrap | undefined;
  isError: boolean;
}

/**
 * The public page. Content comes from App, which makes the only call to `bootstrap`
 * (each call records a visit, so it isn't fetched again from here).
 */
export function HomePage({ data, isError }: Props) {
  const { lang, t } = useLang();
  const profile = data?.profile ?? null;
  const name = profile ? headlineName(localized(profile, "headline", lang)) : t("app.title");

  const sections: SectionId[] = [];
  if (data?.projects.length) sections.push("projects");
  if (data?.experience.length) sections.push("experience");
  if (data?.skills.length) sections.push("skills");
  if (data) sections.push("contact");

  return (
    <>
      <SiteHeader name={name} sections={sections} />
      <main id="top">
        <ProfileSection profile={profile} />
        <div className="page">
          {isError && <p role="alert">{t("page.error")}</p>}
          {data && (
            <>
              <ProjectsSection projects={data.projects} />
              <ExperienceSection experience={data.experience} />
              <SkillsSection skills={data.skills} />
              <ContactSection links={profile?.links ?? {}} />
            </>
          )}
        </div>
      </main>
      <SiteFooter name={name} repoUrl={ownRepoUrl(data?.projects ?? [], window.location.host)} />
    </>
  );
}
