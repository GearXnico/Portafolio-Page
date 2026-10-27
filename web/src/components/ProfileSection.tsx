import { lazy, Suspense, useState, type ComponentType } from "react";

import type { PublicProfile } from "../api/bootstrap";
import { headlineName, httpsUrl } from "../content";
import { localized, useLang } from "../i18n";
import { canShow3D } from "../motion";
import { City } from "./City";

// three.js is only downloaded when the figure is shown, after the page content. If the download
// fails (for example, after a deploy replaced the chunk), the hero shows without the figure.
const Entity = lazy<ComponentType>(() => import("./Entity").catch(() => ({ default: () => null })));

interface Props {
  profile: PublicProfile | null;
}

/** Hero: name, role, introduction and links over a night city, with the 3D figure on wide screens. */
export function ProfileSection({ profile }: Props) {
  const { lang, t } = useLang();
  const [show3D] = useState(canShow3D);
  const headline = profile ? localized(profile, "headline", lang) : t("app.title");
  const name = headlineName(headline);
  const role = headline.slice(name.length).replace(/^\s*·\s*/, "");
  const links = Object.entries(profile?.links ?? {}).flatMap(([label, url]) => {
    const href = httpsUrl(url);
    return href ? [{ label, href }] : [];
  });

  return (
    <header className="hero">
      <City />
      <div className="hero-inner">
        <div className="hero-text">
          <h1>{name}</h1>
          {role && <p className="role">{role}</p>}
          {profile && <p className="about">{localized(profile, "about", lang)}</p>}
          {profile && (
            <p className="actions">
              <a className="button cut" href="#projects">
                {t("hero.projects")}
              </a>
              {links.map(({ label, href }) => (
                <a
                  key={label}
                  className="button ghost"
                  href={href}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  {label}
                </a>
              ))}
            </p>
          )}
        </div>
        {show3D && (
          <Suspense fallback={null}>
            <Entity />
          </Suspense>
        )}
      </div>
    </header>
  );
}
