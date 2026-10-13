// Mensajes de contacto y visitas por UTM para el panel (tarea 4.5). Las rutas exigen la cookie
// de sesión, que el navegador manda solo.
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { ApiError } from "./admin";

export interface ContactMessage {
  id: number;
  created_at: string;
  name: string;
  email: string;
  message: string;
  lang: string;
  utm_source: string | null;
  utm_campaign: string | null;
  read: boolean;
}

export interface VisitCount {
  utm_source: string | null;
  utm_campaign: string | null;
  visits: number;
  unique_visitors: number;
}

const MESSAGES_KEY = ["admin", "messages"] as const;

async function getJson<T>(url: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(url, { signal });
  if (!response.ok) throw new ApiError(response.status);
  return (await response.json()) as T;
}

export function useMessages() {
  return useQuery({
    queryKey: MESSAGES_KEY,
    queryFn: ({ signal }) => getJson<ContactMessage[]>("/api/admin/messages", signal),
  });
}

export function useVisits() {
  return useQuery({
    queryKey: ["admin", "visits"],
    queryFn: ({ signal }) => getJson<VisitCount[]>("/api/admin/visits", signal),
  });
}

/** Marca un mensaje como leído o no leído y vuelve a pedir la lista. */
export function useMarkMessage() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, read }: { id: number; read: boolean }) => {
      const response = await fetch(`/api/admin/messages/${String(id)}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ read }),
      });
      if (!response.ok) throw new ApiError(response.status);
    },
    onSettled: () => queryClient.invalidateQueries({ queryKey: MESSAGES_KEY }),
  });
}
