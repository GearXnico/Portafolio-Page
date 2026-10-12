import { useNavigate } from "react-router";

import { useLogout } from "../api/admin";
import { useLang } from "../i18n";

/** Inicio del panel. Las pantallas de edición llegan en las tareas 4.2 a 4.5. */
export function AdminPage() {
  const { t } = useLang();
  const navigate = useNavigate();
  const logout = useLogout();

  return (
    <>
      <h1>{t("admin.title")}</h1>
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
