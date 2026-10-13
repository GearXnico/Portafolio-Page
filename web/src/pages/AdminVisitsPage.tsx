import { Link } from "react-router";

import { useVisits } from "../api/activity";
import { useLang } from "../i18n";

/** Visitas agrupadas por `utm_source` y `utm_campaign`: qué enlace trajo cuántas visitas. */
export function AdminVisitsPage() {
  const { t } = useLang();
  const visits = useVisits();

  return (
    <>
      <Link to="/admin">{t("admin.back")}</Link>
      <h1>{t("admin.visits.title")}</h1>
      {visits.isError && <p role="alert">{t("admin.error")}</p>}
      {visits.data?.length === 0 && <p>{t("admin.visits.empty")}</p>}
      {visits.data && visits.data.length > 0 && (
        <table className="visits">
          <thead>
            <tr>
              <th scope="col">{t("admin.visits.source")}</th>
              <th scope="col">{t("admin.visits.campaign")}</th>
              <th scope="col">{t("admin.visits.visits")}</th>
              <th scope="col">{t("admin.visits.unique")}</th>
            </tr>
          </thead>
          <tbody>
            {visits.data.map((row) => (
              <tr key={`${row.utm_source ?? ""}|${row.utm_campaign ?? ""}`}>
                <td>{row.utm_source ?? t("admin.visits.direct")}</td>
                <td>{row.utm_campaign ?? "—"}</td>
                <td>{row.visits}</td>
                <td>{row.unique_visitors}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </>
  );
}
