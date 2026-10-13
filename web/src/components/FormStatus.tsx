import { ApiError } from "../api/admin";
import { useLang } from "../i18n";

interface Props {
  error: Error | null;
  saved: boolean;
}

/** Result of saving an admin panel form: saved, invalid data (422) or another error. */
export function FormStatus({ error, saved }: Props) {
  const { t } = useLang();
  if (error) {
    const invalid = error instanceof ApiError && error.status === 422;
    return <p role="alert">{t(invalid ? "admin.form.invalid" : "admin.error")}</p>;
  }
  return saved ? <p role="status">{t("admin.form.saved")}</p> : null;
}
