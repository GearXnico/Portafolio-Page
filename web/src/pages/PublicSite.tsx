import { useEffect, useMemo, useState } from "react";

import { useBootstrap } from "../api/bootstrap";
import { DEFAULT_LANG, isLang, LangContext, storedLang, storeLang, type Lang } from "../i18n";
import { HomePage } from "./HomePage";

/** La página pública: carga `bootstrap` una vez y decide el idioma. */
export function PublicSite() {
  const { data, isPending, isError } = useBootstrap();
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
      <HomePage data={data} isError={isError} />
    </LangContext>
  );
}
