// Proyectos del panel (tarea 4.2): CRUD de /api/admin/projects (tarea 2.4). El panel ve también
// los ocultos; la página pública solo los visibles, en la siguiente carga de `bootstrap`.
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { ApiError } from "./admin";

/** Lo que acepta la API al crear o editar (ProjectIn); no admite campos de más. */
export interface ProjectInput {
  slug: string;
  title_es: string;
  title_en: string;
  summary_es: string;
  summary_en: string;
  body_es: string;
  body_en: string;
  stack: string[];
  demo_url: string | null;
  repo_url: string | null;
  visible: boolean;
  position: number;
}

export interface AdminProject extends ProjectInput {
  id: number;
}

export const PROJECTS_KEY = ["admin", "projects"] as const;

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, init);
  if (!response.ok) throw new ApiError(response.status);
  return (await response.json()) as T;
}

function json(method: string, body: ProjectInput): RequestInit {
  return { method, headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) };
}

export function useProjects() {
  return useQuery({
    queryKey: PROJECTS_KEY,
    queryFn: ({ signal }) => request<AdminProject[]>("/api/admin/projects", { signal }),
  });
}

/** Sin `id` (proyecto nuevo) no pide nada. */
export function useProject(id: number | undefined) {
  return useQuery({
    queryKey: [...PROJECTS_KEY, id],
    queryFn: ({ signal }) => request<AdminProject>(`/api/admin/projects/${String(id)}`, { signal }),
    enabled: id !== undefined,
  });
}

/** Crea (sin `id`) o reemplaza el proyecto completo (con `id`). */
export function useSaveProject(id?: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: ProjectInput) =>
      id === undefined
        ? request<AdminProject>("/api/admin/projects", json("POST", input))
        : request<AdminProject>(`/api/admin/projects/${String(id)}`, json("PUT", input)),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: PROJECTS_KEY }),
  });
}
