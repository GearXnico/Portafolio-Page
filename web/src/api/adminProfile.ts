// Perfil, habilidades y experiencia desde el panel (tarea 4.4), sobre las rutas de la tarea 2.4.
// La cookie de sesión viaja sola (mismo origen); sin ella la API responde 401.
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { ApiError } from "./admin";
import type { SkillCategory } from "./bootstrap";

export interface ProfileInput {
  headline_es: string;
  headline_en: string;
  about_es: string;
  about_en: string;
  contact_email: string;
  links: Record<string, string>;
}

export interface SkillInput {
  name: string;
  category: SkillCategory;
  position: number;
}

export interface Skill extends SkillInput {
  id: number;
}

export interface ExperienceInput {
  company: string;
  role_es: string;
  role_en: string;
  description_es: string;
  description_en: string;
  start_date: string;
  end_date: string | null;
  position: number;
}

export interface Experience extends ExperienceInput {
  id: number;
}

const PROFILE_KEY = ["admin", "profile"] as const;
const SKILLS_KEY = ["admin", "skills"] as const;
const EXPERIENCE_KEY = ["admin", "experience"] as const;

async function request<T>(method: string, url: string, body?: unknown): Promise<T> {
  const response = await fetch(url, {
    method,
    headers: body === undefined ? undefined : { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!response.ok) throw new ApiError(response.status);
  return (response.status === 204 ? undefined : await response.json()) as T;
}

/** El perfil, o null si todavía no se crea (la API responde 404 hasta el primer PUT). */
async function fetchProfile(): Promise<ProfileInput | null> {
  try {
    return await request<ProfileInput>("GET", "/api/admin/profile");
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) return null;
    throw error;
  }
}

export function useAdminProfile() {
  return useQuery({ queryKey: PROFILE_KEY, queryFn: fetchProfile });
}

export function useSaveProfile() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (profile: ProfileInput) =>
      request<ProfileInput>("PUT", "/api/admin/profile", profile),
    onSuccess: (saved) => {
      queryClient.setQueryData(PROFILE_KEY, saved);
    },
  });
}

export function useAdminSkills() {
  return useQuery({
    queryKey: SKILLS_KEY,
    queryFn: () => request<Skill[]>("GET", "/api/admin/skills"),
  });
}

/** Crea la habilidad si no trae id; si trae, la reemplaza. */
export function useSaveSkill() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...skill }: SkillInput & { id?: number }) =>
      id === undefined
        ? request<Skill>("POST", "/api/admin/skills", skill)
        : request<Skill>("PUT", `/api/admin/skills/${String(id)}`, skill),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: SKILLS_KEY }),
  });
}

export function useDeleteSkill() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => request<undefined>("DELETE", `/api/admin/skills/${String(id)}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: SKILLS_KEY }),
  });
}

export function useAdminExperience() {
  return useQuery({
    queryKey: EXPERIENCE_KEY,
    queryFn: () => request<Experience[]>("GET", "/api/admin/experience"),
  });
}

/** Crea el trabajo si no trae id; si trae, lo reemplaza. */
export function useSaveExperience() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...item }: ExperienceInput & { id?: number }) =>
      id === undefined
        ? request<Experience>("POST", "/api/admin/experience", item)
        : request<Experience>("PUT", `/api/admin/experience/${String(id)}`, item),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: EXPERIENCE_KEY }),
  });
}

export function useDeleteExperience() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => request<undefined>("DELETE", `/api/admin/experience/${String(id)}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: EXPERIENCE_KEY }),
  });
}
