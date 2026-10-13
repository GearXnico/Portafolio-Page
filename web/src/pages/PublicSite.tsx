import { useMemo, useState } from "react";

import { useBootstrap } from "../api/bootstrap";
import {
  DEFAULT_LANG,
  isLang,
  LangContext,
  localized,
  storedLang,
  storeLang,
  translate,
  useDocumentMeta,
  type Lang,
} from "../i18n";
import { HomePage } from "./HomePage";

/** The public page: loads `bootstrap` once and decides the language. */
export function PublicSite() {
  const { data, isPending, isError } = useBootstrap();
  const [chosen, setChosen] = useState<Lang | null>(storedLang);

  // The switcher choice wins; if there is none, the language the API (application programming
  // interface) decided.
  const apiLang = isLang(data?.lang) ? data.lang : null;
  const lang = chosen ?? apiLang ?? DEFAULT_LANG;

  // Title for the browser tab and search engines: the profile headline, if it has arrived.
  const metaTitle = translate(lang, "meta.title");
  const profile = data?.profile;
  useDocumentMeta(
    lang,
    profile ? `${localized(profile, "headline", lang)} · ${metaTitle}` : metaTitle,
  );

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

  // With no saved choice, it waits for the API so it doesn't show one language and then switch.
  if (chosen === null && isPending) return null;

  return (
    <LangContext value={value}>
      <HomePage data={data} isError={isError} />
    </LangContext>
  );
}
