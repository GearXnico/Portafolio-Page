import { useEffect, useState } from "react";

import { useLang } from "../i18n";

type Status = "loading" | "ok" | "error";

const labels = {
  loading: "apiStatus.loading",
  ok: "apiStatus.ok",
  error: "apiStatus.error",
} as const;

/** Muestra si la API (y su base) responde en /api/health. */
export function ApiStatus() {
  const { t } = useLang();
  const [status, setStatus] = useState<Status>("loading");

  useEffect(() => {
    const controller = new AbortController();
    fetch("/api/health", { signal: controller.signal })
      .then((response) => {
        setStatus(response.ok ? "ok" : "error");
      })
      .catch(() => {
        if (!controller.signal.aborted) setStatus("error");
      });
    return () => {
      controller.abort();
    };
  }, []);

  return (
    <p>
      {t("apiStatus.label")}: <span data-testid="api-status">{t(labels[status])}</span>
    </p>
  );
}
