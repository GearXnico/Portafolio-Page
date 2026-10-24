import { Navigate, Outlet } from "react-router";

import { useAdminSession } from "../api/admin";
import { useLang } from "../i18n";

/**
 * Guards the admin panel screens: without a session, it redirects to the login. The API still
 * requires the cookie.
 */
export function RequireAdmin() {
  const { t } = useLang();
  const { data: hasSession, isPending, isError } = useAdminSession();

  if (isPending) return null;
  if (isError) return <p role="alert">{t("admin.error")}</p>;
  if (!hasSession) return <Navigate to="/admin/login" replace />;
  return <Outlet />;
}
