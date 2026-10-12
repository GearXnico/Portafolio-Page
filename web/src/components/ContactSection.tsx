import { httpsUrl } from "../content";
import { useLang } from "../i18n";

interface Props {
  links: Record<string, string>;
}

/**
 * Enlaces del perfil (GitHub, LinkedIn, CV…). El formulario llega en la tarea 3.4; el correo
 * no se publica (el contacto será solo por el formulario).
 */
export function ContactSection({ links }: Props) {
  const { t } = useLang();
  const safeLinks = Object.entries(links).flatMap(([label, url]) => {
    const href = httpsUrl(url);
    return href ? [{ label, href }] : [];
  });
  if (safeLinks.length === 0) return null;

  return (
    <section id="contact" aria-labelledby="contact-title">
      <h2 id="contact-title">{t("section.contact")}</h2>
      <ul className="links">
        {safeLinks.map(({ label, href }) => (
          <li key={label}>
            <a href={href} target="_blank" rel="noopener noreferrer">
              {label}
            </a>
          </li>
        ))}
      </ul>
    </section>
  );
}
