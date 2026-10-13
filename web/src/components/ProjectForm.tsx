import { useState, type SubmitEvent } from "react";

import { ApiError } from "../api/admin";
import { useSaveProject, type AdminProject, type ProjectInput } from "../api/projects";
import { LANGS, useLang, type MessageKey } from "../i18n";

const EMPTY: ProjectInput = {
  slug: "",
  title_es: "",
  title_en: "",
  summary_es: "",
  summary_en: "",
  body_es: "",
  body_en: "",
  stack: [],
  demo_url: null,
  repo_url: null,
  visible: false,
  position: 0,
};

function errorKey(error: Error): MessageKey {
  if (error instanceof ApiError && error.status === 409) return "admin.projects.slugTaken";
  if (error instanceof ApiError && error.status === 422) return "admin.projects.invalid";
  return "admin.error";
}

interface Props {
  /** Without a project, the form creates a new one. */
  project?: AdminProject;
  onSaved: () => void;
}

/**
 * Project form: the Spanish and English texts side by side, and below them the slug, the stack,
 * the links, the order and whether it shows on the page. The API (application programming
 * interface) validates everything again on save.
 */
export function ProjectForm({ project, onSaved }: Props) {
  const { t } = useLang();
  const save = useSaveProject(project?.id);
  // The API rejects extra fields (id, screenshots, dates), so only the editable ones are copied.
  const [values, setValues] = useState<ProjectInput>(() =>
    project
      ? (Object.fromEntries(
          Object.keys(EMPTY).map((key) => [key, project[key as keyof ProjectInput]]),
        ) as unknown as ProjectInput)
      : EMPTY,
  );
  const [stack, setStack] = useState(values.stack.join(", "));

  function set<K extends keyof ProjectInput>(key: K, value: ProjectInput[K]) {
    setValues((current) => ({ ...current, [key]: value }));
  }

  function handleSubmit(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    const names = stack
      .split(",")
      .map((name) => name.trim())
      .filter(Boolean);
    save.mutate({ ...values, stack: names }, { onSuccess: onSaved });
  }

  return (
    <form className="form project-form" onSubmit={handleSubmit}>
      <div className="langs">
        {LANGS.map((lang) => (
          <fieldset key={lang}>
            <legend>{t(`lang.${lang}`)}</legend>
            <label>
              {t("admin.projects.titleField")}
              <input
                required
                maxLength={200}
                value={values[`title_${lang}`]}
                onChange={(e) => {
                  set(`title_${lang}`, e.target.value);
                }}
              />
            </label>
            <label>
              {t("admin.projects.summary")}
              <textarea
                required
                rows={3}
                maxLength={500}
                value={values[`summary_${lang}`]}
                onChange={(e) => {
                  set(`summary_${lang}`, e.target.value);
                }}
              />
            </label>
            <label>
              {t("admin.projects.body")}
              <textarea
                rows={8}
                maxLength={10000}
                value={values[`body_${lang}`]}
                onChange={(e) => {
                  set(`body_${lang}`, e.target.value);
                }}
              />
            </label>
          </fieldset>
        ))}
      </div>
      <label>
        {t("admin.projects.slug")}
        <input
          required
          maxLength={100}
          pattern="[a-z0-9]+(-[a-z0-9]+)*"
          value={values.slug}
          onChange={(e) => {
            set("slug", e.target.value);
          }}
        />
      </label>
      <label>
        {t("admin.projects.stack")}
        <input
          value={stack}
          onChange={(e) => {
            setStack(e.target.value);
          }}
        />
      </label>
      <label>
        {t("admin.projects.demoUrl")}
        <input
          type="url"
          maxLength={2048}
          value={values.demo_url ?? ""}
          onChange={(e) => {
            set("demo_url", e.target.value || null);
          }}
        />
      </label>
      <label>
        {t("admin.projects.repoUrl")}
        <input
          type="url"
          maxLength={2048}
          value={values.repo_url ?? ""}
          onChange={(e) => {
            set("repo_url", e.target.value || null);
          }}
        />
      </label>
      <label>
        {t("admin.projects.position")}
        <input
          type="number"
          required
          min={0}
          max={1000000}
          value={values.position}
          onChange={(e) => {
            set("position", e.target.valueAsNumber);
          }}
        />
      </label>
      <label className="check">
        <input
          type="checkbox"
          checked={values.visible}
          onChange={(e) => {
            set("visible", e.target.checked);
          }}
        />
        {t("admin.projects.visible")}
      </label>
      {save.error && <p role="alert">{t(errorKey(save.error))}</p>}
      <button type="submit" disabled={save.isPending}>
        {t("admin.projects.save")}
      </button>
    </form>
  );
}
