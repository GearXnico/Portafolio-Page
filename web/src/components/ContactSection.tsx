import { httpsUrl } from "../content";
import { useLang } from "../i18n";
import { ContactForm } from "./ContactForm";

interface Props {
  links: Record<string, string>;
}

/**
 * Contact: profile links (GitHub, LinkedIn, CV…) and the form. The email address isn't published;
 * direct contact is only through the form.
 */
export function ContactSection({ links }: Props) {
  const { t } = useLang();
  const safeLinks = Object.entries(links).flatMap(([label, url]) => {
    const href = httpsUrl(url);
    return href ? [{ label, href }] : [];
  });

  return (
    <section id="contact" aria-labelledby="contact-title" className="contact cut">
      <div>
        <h2 id="contact-title">{t("contact.title")}</h2>
        <p>{t("contact.intro")}</p>
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
      </div>
      <ContactForm />
    </section>
  );
}
