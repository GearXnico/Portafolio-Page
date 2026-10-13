import { ApiError } from "../api/admin";
import { useLang } from "../i18n";

interface Props {
  error: Error | null;
  saved: boolean;
}

/** Resultado de guardar un formulario del panel: guardado, datos inválidos (422) u otro error. */
export function FormStatus({ error, saved }: Props) {
  const { t } = useLang();
  if (error) {
    const invalid = error instanceof ApiError && error.status === 422;
    return <p role="alert">{t(invalid ? "admin.form.invalid" : "admin.error")}</p>;
  }
  return saved ? <p role="status">{t("admin.form.saved")}</p> : null;
}
