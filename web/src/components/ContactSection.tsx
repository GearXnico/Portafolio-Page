import { httpsUrl } from "../content";
import { useLang } from "../i18n";
import { ContactForm } from "./ContactForm";

interface Props {
  links: Record<string, string>;
}

/**
 * Contacto: enlaces del perfil (GitHub, LinkedIn, CV…) y el formulario. El correo no se
 * publica; el contacto directo es solo por el formulario.
 */
export function ContactSection({ links }: Props) {
  const { t } = useLang();
  const safeLinks = Object.entries(links).flatMap(([label, url]) => {
    const href = httpsUrl(url);
    return href ? [{ label, href }] : [];
  });

  return (
    <section id="contact" aria-labelledby="contact-title">
      <h2 id="contact-title">{t("section.contact")}</h2>
      {safeLinks.length > 0 && (
        <ul className="links">
          {safeLinks.map(({ label, href }) => (
            <li key={label}>
              <a href={href} target="_blank" rel="noopener noreferrer">
                {label}
              </a>
            </li>
          ))}
        </ul>
      )}
      <p>{t("contact.intro")}</p>
      <ContactForm />
    </section>
  );
}
