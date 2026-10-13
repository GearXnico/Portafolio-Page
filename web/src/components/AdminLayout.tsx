import { useMemo, useState } from "react";
import { Outlet } from "react-router";

import {
  DEFAULT_LANG,
  LangContext,
  storedLang,
  storeLang,
  translate,
  useDocumentMeta,
  type Lang,
} from "../i18n";
import { LanguageSwitcher } from "./LanguageSwitcher";

/**
 * Frame for every admin panel screen. It doesn't call `bootstrap` (that would record a visit), so
 * the language is the one picked in the switcher, or Spanish.
 */
export function AdminLayout() {
  const [lang, setLang] = useState<Lang>(() => storedLang() ?? DEFAULT_LANG);

  useDocumentMeta(lang, translate(lang, "admin.title"), true);

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
