import { useLang } from "../i18n";

interface Props {
  name: string;
  repoUrl: string | null;
}

export function SiteFooter({ name, repoUrl }: Props) {
  const { t } = useLang();

  return (
    <footer className="site-footer">
      <div>
        <span>
          © {new Date().getFullYear()} {name}
        </span>
        {repoUrl && (
          <a href={repoUrl} target="_blank" rel="noopener noreferrer">
            {t("footer.code")}
          </a>
        )}
      </div>
    </footer>
  );
}
