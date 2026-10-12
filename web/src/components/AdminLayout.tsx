import { useEffect, useMemo, useState } from "react";
import { Outlet } from "react-router";

import { DEFAULT_LANG, LangContext, storedLang, storeLang, type Lang } from "../i18n";
import { LanguageSwitcher } from "./LanguageSwitcher";

/**
 * Marco de todas las pantallas del panel. No llama a `bootstrap` (registraría una visita), así
 * que el idioma es el que se eligió en el selector, o español.
 */
export function AdminLayout() {
  const [lang, setLang] = useState<Lang>(() => storedLang() ?? DEFAULT_LANG);

  useEffect(() => {
    document.documentElement.lang = lang;
  }, [lang]);

  const value = useMemo(
    () => ({
      lang,
      setLang: (next: Lang) => {
        storeLang(next);
        setLang(next);
      },
    }),
    [lang],
  );

  return (
    <LangContext value={value}>
      <main className="page">
        <nav className="top">
          <LanguageSwitcher />
        </nav>
        <Outlet />
      </main>
    </LangContext>
  );
}
