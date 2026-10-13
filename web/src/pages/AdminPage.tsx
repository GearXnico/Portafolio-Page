import { Link, useNavigate } from "react-router";

import { useLogout } from "../api/admin";
import { useLang } from "../i18n";

/** Inicio del panel: enlaces a cada sección y el botón para cerrar sesión. */
export function AdminPage() {
  const { t } = useLang();
  const navigate = useNavigate();
  const logout = useLogout();

  return (
    <>
      <h1>{t("admin.title")}</h1>
      {/* Una sección por línea. */}
      <nav aria-label={t("admin.sections")}>
        <ul>
          <li>
            <Link to="projects">{t("admin.projects.title")}</Link>
          </li>
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
