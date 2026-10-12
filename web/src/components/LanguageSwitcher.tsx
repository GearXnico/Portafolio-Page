import { LANGS, useLang } from "../i18n";

/** Botones para cambiar el idioma de la página; la elección se recuerda. */
export function LanguageSwitcher() {
  const { lang, setLang, t } = useLang();

  return (
    <div role="group" aria-label={t("lang.label")}>
      {LANGS.map((option) => (
        <button
          key={option}
          type="button"
          lang={option}
          aria-pressed={option === lang}
          onClick={() => {
            setLang(option);
          }}
        >
          {t(`lang.${option}`)}
        </button>
      ))}
    </div>
  );
}
