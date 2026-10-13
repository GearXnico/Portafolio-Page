import { useState, type SubmitEvent } from "react";
import { useNavigate } from "react-router";

import { ApiError, useLogin } from "../api/admin";
import { useLang, type MessageKey } from "../i18n";

function errorKey(error: Error): MessageKey {
  if (error instanceof ApiError && error.status === 401) return "admin.login.invalid";
  if (error instanceof ApiError && error.status === 429) return "admin.login.tooMany";
  return "admin.error";
}

/** Admin panel login form. With the correct credentials, it enters the panel. */
export function AdminLoginPage() {
  const { t } = useLang();
  const navigate = useNavigate();
  const login = useLogin();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  function handleSubmit(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    login.mutate(
      { email, password },
      {
        onSuccess: () => {
          void navigate("/admin", { replace: true });
        },
      },
    );
  }

  return (
    <>
      <h1>{t("admin.login.title")}</h1>
      <form className="form" onSubmit={handleSubmit}>
        <label>
          {t("admin.login.email")}
          <input
            type="email"
            autoComplete="username"
            required
            maxLength={254}
            value={email}
            onChange={(event) => {
              setEmail(event.target.value);
            }}
          />
        </label>
        <label>
          {t("admin.login.password")}
          <input
            type="password"
            autoComplete="current-password"
            required
            maxLength={256}
            value={password}
            onChange={(event) => {
              setPassword(event.target.value);
            }}
          />
        </label>
        {login.error && <p role="alert">{t(errorKey(login.error))}</p>}
        <button type="submit" disabled={login.isPending}>
          {t("admin.login.submit")}
        </button>
      </form>
    </>
  );
}
