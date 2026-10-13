import { useState, type SubmitEvent } from "react";

import { useDeleteSkill, useSaveSkill, type Skill, type SkillInput } from "../api/adminProfile";
import type { SkillCategory } from "../api/bootstrap";
import { useLang } from "../i18n";
import { FormStatus } from "./FormStatus";

const CATEGORIES: readonly SkillCategory[] = ["language", "framework", "tool"];
const EMPTY: SkillInput = { name: "", category: "language", position: 0 };

/** Una habilidad del panel: sin `skill`, crea una nueva y deja el formulario en blanco. */
export function SkillForm({ skill }: { skill?: Skill }) {
  const { t } = useLang();
  const save = useSaveSkill();
  const remove = useDeleteSkill();
  const [form, setForm] = useState<SkillInput>(skill ?? EMPTY);

  function handleSubmit(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    const { name, category, position } = form;
    save.mutate(
      { id: skill?.id, name, category, position },
      {
        onSuccess: () => {
          if (!skill) setForm(EMPTY);
        },
      },
    );
  }

  return (
    <form className="form row" onSubmit={handleSubmit}>
      <label>
        {t("admin.skills.name")}
        <input
          required
          maxLength={100}
          value={form.name}
          onChange={(event) => {
            setForm({ ...form, name: event.target.value });
          }}
        />
      </label>
      <label>
        {t("admin.skills.category")}
        <select
          value={form.category}
          onChange={(event) => {
            setForm({ ...form, category: event.target.value as SkillCategory });
          }}
        >
          {CATEGORIES.map((category) => (
            <option key={category} value={category}>
              {t(`skills.${category}`)}
            </option>
          ))}
        </select>
      </label>
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
      <FormStatus error={save.error ?? remove.error} saved={save.isSuccess && !!skill} />
      <button type="submit" disabled={save.isPending}>
        {t(skill ? "admin.form.save" : "admin.form.add")}
      </button>
      {skill && (
        <button
          type="button"
          disabled={remove.isPending}
          onClick={() => {
            if (window.confirm(t("admin.form.confirmDelete"))) remove.mutate(skill.id);
          }}
        >
          {t("admin.form.delete")}
        </button>
      )}
    </form>
  );
}
