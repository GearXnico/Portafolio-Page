// Admin panel projects: CRUD on /api/admin/projects. The panel also sees hidden projects; the
// public page only sees the visible ones, on the next `bootstrap` load. Screenshots have their own
// routes.
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { ApiError } from "./admin";

/** What the API accepts on create or edit (ProjectIn); it rejects extra fields. */
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

/** A saved screenshot (ImageOut): the API stored it as WebP under /media. */
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

/** Without an `id` (new project) it fetches nothing. */
export function useProject(id: number | undefined) {
  return useQuery({
    queryKey: [...PROJECTS_KEY, id],
    queryFn: ({ signal }) => request<AdminProject>(`/api/admin/projects/${String(id)}`, { signal }),
    enabled: id !== undefined,
  });
}

/** Creates (without `id`) or replaces the whole project (with `id`). */
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
 * Screenshots update the project in the cache instead of fetching it again: that way the form next
 * to them isn't rebuilt and unsaved changes aren't lost.
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

/** Uploads a screenshot (multipart); the API adds it at the end of the project. */
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
