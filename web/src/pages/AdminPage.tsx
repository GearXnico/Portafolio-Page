import { Link, useNavigate } from "react-router";

import { useLogout } from "../api/admin";
import { useLang, type MessageKey } from "../i18n";

// Admin panel sections: each new screen adds its link here.
const SECTIONS: readonly [string, MessageKey][] = [
  ["projects", "admin.projects.title"],
  ["profile", "admin.profile.title"],
  ["skills", "admin.skills.title"],
  ["experience", "admin.experience.title"],
  ["messages", "admin.messages.title"],
  ["visits", "admin.visits.title"],
];

/** Admin panel home: the section menu and logout. */
export function AdminPage() {
  const { t } = useLang();
  const navigate = useNavigate();
  const logout = useLogout();

  return (
    <>
      <h1>{t("admin.title")}</h1>
      <nav aria-label={t("admin.sections")}>
        <ul>
          {SECTIONS.map(([path, label]) => (
            <li key={path}>
              <Link to={path}>{t(label)}</Link>
            </li>
          ))}
        </ul>
      </nav>
      {logout.isError && <p role="alert">{t("admin.error")}</p>}
      <button
        type="button"
        disabled={logout.isPending}
        onClick={() => {
          logout.mutate(undefined, {
            onSuccess: () => {
              void navigate("/admin/login", { replace: true });
            },
          });
        }}
      >
        {t("admin.logout")}
      </button>
    </>
  );
}
