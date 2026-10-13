import type { ContactMessage } from "../api/activity";
import { useLang } from "../i18n";

interface Props {
  message: ContactMessage;
  busy: boolean;
  onToggleRead: () => void;
}

/** A contact message in the admin panel. The text is shown as text (React escapes it). */
export function MessageItem({ message, busy, onToggleRead }: Props) {
  const { lang, t } = useLang();
  const origin =
    [message.utm_source, message.utm_campaign].filter(Boolean).join(" / ") ||
    t("admin.visits.direct");

  return (
    <article className={message.read ? "message" : "message message-unread"}>
      <h2>
        {message.name} · {message.email}
      </h2>
      <p>
        {new Date(message.created_at).toLocaleString(lang)} · {origin} ·{" "}
        {t(message.read ? "admin.messages.read" : "admin.messages.unread")}
      </p>
      <p className="message-text">{message.message}</p>
      <button type="button" disabled={busy} onClick={onToggleRead}>
        {t(message.read ? "admin.messages.markUnread" : "admin.messages.markRead")}
      </button>
    </article>
  );
}
