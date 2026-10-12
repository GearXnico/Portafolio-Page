import { ApiStatus } from "./components/ApiStatus";
import { t } from "./i18n";

export function App() {
  return (
    <main>
      <h1>{t("app.title")}</h1>
      <ApiStatus />
    </main>
  );
}
