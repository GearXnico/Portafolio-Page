import { useState, type SubmitEvent } from "react";

import { ApiError } from "../api/admin";
import { useDeleteImage, useUploadImage, type AdminProject } from "../api/projects";
import { useLang, type MessageKey } from "../i18n";

function errorKey(error: Error): MessageKey {
  if (error instanceof ApiError && error.status === 413) return "admin.images.tooLarge";
  if (error instanceof ApiError && error.status === 415) return "admin.images.badType";
  if (error instanceof ApiError && error.status === 422) return "admin.images.invalid";
  return "admin.error";
}

/**
 * Screenshots of a saved project: the current ones, each with its delete button, and a form to
 * upload another. The first one is the cover on the public page. The API validates and converts the
 * file.
 */
export function ProjectImages({ project }: { project: AdminProject }) {
  const { t } = useLang();
  const upload = useUploadImage(project.id);
  const remove = useDeleteImage(project.id);
  const [file, setFile] = useState<File | null>(null);
  const [altEs, setAltEs] = useState("");
  const [altEn, setAltEn] = useState("");

  function handleSubmit(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!file) return;
    const form = event.currentTarget;
    // Only the error from the last action is shown.
    remove.reset();
    upload.mutate(
      { file, alt_es: altEs, alt_en: altEn },
      {
        onSuccess: () => {
          form.reset();
          setFile(null);
          setAltEs("");
          setAltEn("");
        },
      },
    );
  }

  function handleDelete(imageId: number) {
    if (!window.confirm(t("admin.images.confirmDelete"))) return;
    upload.reset();
    remove.mutate(imageId);
  }

  const error = upload.error ?? remove.error;

  return (
    <section className="project-images" aria-labelledby="project-images-title">
      <h2 id="project-images-title">{t("admin.images.title")}</h2>
      {project.images.length === 0 ? (
        <p>{t("admin.images.empty")}</p>
      ) : (
        <ul>
          {project.images.map((image) => (
            <li key={image.id}>
              <img src={image.url} alt={image.alt_es} />
              <button
                type="button"
                onClick={() => {
                  handleDelete(image.id);
                }}
                disabled={remove.isPending}
              >
                {t("admin.images.delete")}
              </button>
            </li>
          ))}
        </ul>
      )}
      <form className="form" onSubmit={handleSubmit}>
        <label>
          {t("admin.images.file")}
          <input
            type="file"
            accept="image/jpeg,image/png,image/webp"
            onChange={(e) => {
              setFile(e.target.files?.[0] ?? null);
            }}
          />
        </label>
        <label>
          {t("admin.images.altEs")}
          <input
            value={altEs}
            required
            maxLength={300}
            onChange={(e) => {
              setAltEs(e.target.value);
            }}
          />
        </label>
        <label>
          {t("admin.images.altEn")}
          <input
            value={altEn}
            required
            maxLength={300}
            onChange={(e) => {
              setAltEn(e.target.value);
            }}
          />
        </label>
        {error && <p role="alert">{t(errorKey(error))}</p>}
        <button type="submit" disabled={!file || upload.isPending}>
          {t("admin.images.upload")}
        </button>
      </form>
    </section>
  );
}
