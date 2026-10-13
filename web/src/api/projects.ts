// Proyectos del panel (tarea 4.2): CRUD de /api/admin/projects (tarea 2.4). El panel ve también
// los ocultos; la página pública solo los visibles, en la siguiente carga de `bootstrap`.
// Las capturas (tarea 4.3) usan las rutas de la tarea 2.5.
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

/** Una captura ya guardada (ImageOut): la API la dejó en WebP bajo /media. */
export interface ProjectImage {
  id: number;
  url: string;
  alt_es: string;
  alt_en: string;
  position: number;
}

export interface AdminProject extends ProjectInput {
  id: number;
  images: ProjectImage[];
}

export interface ImageUpload {
  file: File;
  alt_es: string;
  alt_en: string;
}

export const PROJECTS_KEY = ["admin", "projects"] as const;

async function send(url: string, init?: RequestInit): Promise<Response> {
  const response = await fetch(url, init);
  if (!response.ok) throw new ApiError(response.status);
  return response;
}

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  return (await (await send(url, init)).json()) as T;
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

/**
 * Las capturas actualizan el proyecto en la cache en vez de pedirlo de nuevo: así el formulario
 * de al lado no se rearma y no se pierden cambios que aún no se guardaron.
 */
function useUpdateCachedImages(projectId: number) {
  const queryClient = useQueryClient();
  return (change: (images: ProjectImage[]) => ProjectImage[]) => {
    queryClient.setQueryData<AdminProject>(
      [...PROJECTS_KEY, projectId],
      (project) => project && { ...project, images: change(project.images) },
    );
  };
}

/** Sube una captura (multipart); la API la deja al final del proyecto. */
export function useUploadImage(projectId: number) {
  const updateImages = useUpdateCachedImages(projectId);
  return useMutation({
    mutationFn: ({ file, alt_es, alt_en }: ImageUpload) => {
      const body = new FormData();
      body.append("file", file);
      body.append("alt_es", alt_es);
      body.append("alt_en", alt_en);
      return request<ProjectImage>(`/api/admin/projects/${String(projectId)}/images`, {
        method: "POST",
        body,
      });
    },
    onSuccess: (image) => {
      updateImages((images) => [...images, image]);
    },
  });
}

export function useDeleteImage(projectId: number) {
  const updateImages = useUpdateCachedImages(projectId);
  return useMutation({
    mutationFn: (imageId: number) =>
      send(`/api/admin/projects/${String(projectId)}/images/${String(imageId)}`, {
        method: "DELETE",
      }),
    onSuccess: (_response, imageId) => {
      updateImages((images) => images.filter((image) => image.id !== imageId));
    },
  });
}
