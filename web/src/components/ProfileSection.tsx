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
  // The last word of the name is drawn in outline, like the approved design.
  const cut = name.lastIndexOf(" ");
  const [first, last] = cut > 0 ? [name.slice(0, cut), name.slice(cut + 1)] : [name, ""];
  const links = Object.entries(profile?.links ?? {}).flatMap(([label, url]) => {
    const href = httpsUrl(url);
    return href ? [{ label, href }] : [];
  });

  return (
    <header className="hero">
      <City />
      <div className="hero-inner">
        <div className="hero-text">
          {profile && (
            <div className="boot">
              <p>&gt; {t("hero.boot.open")}</p>
              {role && (
                <p>
                  &gt; {t("hero.boot.role")}: <span className="role">{role}</span>
                </p>
              )}
              <p>&gt; {t("hero.boot.status")}</p>
            </div>
          )}
          <h1>
            {first}
            {last && (
              <>
                {" "}
                <span className="outline">{last}</span>
              </>
            )}
          </h1>
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
            {/* The figure reads its colour once, so a new palette draws a new figure. */}
            <Entity key={profile?.palette ?? "mint"} />
          </Suspense>
        )}
      </div>
    </header>
  );
}
