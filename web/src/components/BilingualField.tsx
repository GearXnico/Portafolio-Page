import { LANGS, useLang, type Lang } from "../i18n";

interface Props {
  label: string;
  values: Record<Lang, string>;
  onChange: (lang: Lang, value: string) => void;
  maxLength: number;
  multiline?: boolean;
  required?: boolean;
}

/** Un campo en los dos idiomas, lado a lado (ADR 0003): «Titular · Español» y «Titular · English». */
export function BilingualField({ label, values, onChange, maxLength, multiline, required }: Props) {
  const { t } = useLang();
  return (
    <div className="bilingual">
      {LANGS.map((lang) => {
        const props = {
          value: values[lang],
          maxLength,
          required,
          onChange: (event: { target: { value: string } }) => {
            onChange(lang, event.target.value);
          },
        };
        return (
          <label key={lang}>
            {`${label} · ${t(`lang.${lang}`)}`}
            {multiline ? <textarea rows={5} {...props} /> : <input {...props} />}
          </label>
        );
      })}
    </div>
  );
}
