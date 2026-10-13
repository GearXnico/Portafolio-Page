import { Link } from "react-router";

import { useMarkMessage, useMessages } from "../api/activity";
import { MessageItem } from "../components/MessageItem";
import { useLang } from "../i18n";

/** Contact form messages, newest first, with their read status. */
export function AdminMessagesPage() {
  const { t } = useLang();
  const messages = useMessages();
  const mark = useMarkMessage();

  return (
    <>
      <Link to="/admin">{t("admin.back")}</Link>
      <h1>{t("admin.messages.title")}</h1>
      {(messages.isError || mark.isError) && <p role="alert">{t("admin.error")}</p>}
      {messages.data?.length === 0 && <p>{t("admin.messages.empty")}</p>}
      {messages.data?.map((message) => (
        <MessageItem
          key={message.id}
          message={message}
          busy={mark.isPending}
          onToggleRead={() => {
            mark.mutate({ id: message.id, read: !message.read });
          }}
        />
      ))}
    </>
  );
}
