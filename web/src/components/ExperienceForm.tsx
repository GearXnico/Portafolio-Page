import { useState, type SubmitEvent } from "react";

import {
  useDeleteExperience,
  useSaveExperience,
  type Experience,
  type ExperienceInput,
} from "../api/adminProfile";
import { useLang } from "../i18n";
import { BilingualField } from "./BilingualField";
import { FormStatus } from "./FormStatus";

const EMPTY: ExperienceInput = {
  company: "",
  role_es: "",
  role_en: "",
  description_es: "",
  description_en: "",
  start_date: "",
  end_date: null,
  position: 0,
};

/** One admin panel job: without `item`, it creates a new one and leaves the form blank. */
export function ExperienceForm({ item }: { item?: Experience }) {
  const { t } = useLang();
  const save = useSaveExperience();
  const remove = useDeleteExperience();
  const [form, setForm] = useState<ExperienceInput>(item ?? EMPTY);

  function handleSubmit(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    // Only the fields the API (application programming interface) accepts (the response also
    // includes the id).
    const { company, role_es, role_en, description_es, description_en } = form;
    const { start_date, end_date, position } = form;
    save.mutate(
      {
        id: item?.id,
        company,
        role_es,
        role_en,
        description_es,
        description_en,
        start_date,
        end_date,
        position,
      },
      {
        onSuccess: () => {
          if (!item) setForm(EMPTY);
        },
      },
    );
  }

  return (
    <form className="form card" onSubmit={handleSubmit}>
      <label>
        {t("admin.experience.company")}
        <input
          required
          maxLength={200}
          value={form.company}
          onChange={(event) => {
            setForm({ ...form, company: event.target.value });
          }}
        />
      </label>
      <BilingualField
        label={t("admin.experience.role")}
        values={{ es: form.role_es, en: form.role_en }}
        onChange={(lang, value) => {
          setForm({ ...form, [`role_${lang}`]: value });
        }}
        maxLength={200}
        required
      />
      <BilingualField
        label={t("admin.experience.description")}
        values={{ es: form.description_es, en: form.description_en }}
        onChange={(lang, value) => {
          setForm({ ...form, [`description_${lang}`]: value });
        }}
        maxLength={5000}
        multiline
      />
      <div className="bilingual">
        <label>
          {t("admin.experience.start")}
          <input
            type="date"
            required
            value={form.start_date}
            onChange={(event) => {
              setForm({ ...form, start_date: event.target.value });
            }}
          />
        </label>
        <label>
          {t("admin.experience.end")}
          <input
            type="date"
            value={form.end_date ?? ""}
            onChange={(event) => {
              setForm({ ...form, end_date: event.target.value || null });
            }}
          />
        </label>
      </div>
      <label>
        {t("admin.form.position")}
        <input
          type="number"
          min={0}
          required
          value={form.position}
          onChange={(event) => {
            setForm({ ...form, position: event.target.valueAsNumber || 0 });
          }}
        />
      </label>
      <FormStatus error={save.error ?? remove.error} saved={save.isSuccess && !!item} />
      <button type="submit" disabled={save.isPending}>
        {t(item ? "admin.form.save" : "admin.form.add")}
      </button>
      {item && (
        <button
          type="button"
          disabled={remove.isPending}
          onClick={() => {
            if (window.confirm(t("admin.form.confirmDelete"))) remove.mutate(item.id);
          }}
        >
          {t("admin.form.delete")}
        </button>
      )}
    </form>
  );
}
