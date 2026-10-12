import { useEffect, useMemo, useState } from "react";

import { useBootstrap } from "./api/bootstrap";
import { ApiStatus } from "./components/ApiStatus";
import { LanguageSwitcher } from "./components/LanguageSwitcher";
import {
  DEFAULT_LANG,
  isLang,
  LangContext,
  storedLang,
  storeLang,
  translate,
  type Lang,
} from "./i18n";

export function App() {
  const { data, isPending } = useBootstrap();
  const [chosen, setChosen] = useState<Lang | null>(storedLang);

  // Manda la elección del selector; si no hay, el idioma que decidió la API.
  const apiLang = isLang(data?.lang) ? data.lang : null;
  const lang = chosen ?? apiLang ?? DEFAULT_LANG;

  useEffect(() => {
    document.documentElement.lang = lang;
  }, [lang]);

  const value = useMemo(
    () => ({
      lang,
      setLang: (next: Lang) => {
        storeLang(next);
        setChosen(next);
      },
    }),
    [lang],
  );

  // Sin elección guardada, se espera a la API para no mostrar un idioma y luego cambiarlo.
  if (chosen === null && isPending) return null;

  return (
    <LangContext value={value}>
      <main>
        <LanguageSwitcher />
        <h1>{translate(lang, "app.title")}</h1>
        <ApiStatus />
      </main>
    </LangContext>
  );
}
