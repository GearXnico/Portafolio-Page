// Sesión del panel (tarea 2.3): la API deja una cookie httpOnly en el login, así que la web no
// ve el token; solo pregunta a GET /api/admin/session si la sesión sigue válida.
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

export const SESSION_KEY = ["admin", "session"] as const;

/** Error con el código HTTP, para que el formulario muestre el mensaje que corresponde. */
export class ApiError extends Error {
  constructor(readonly status: number) {
    super(`la API respondió ${String(status)}`);
  }
}

/** true con sesión, false sin ella (401). Cualquier otra respuesta es un error. */
export async function fetchSession(signal?: AbortSignal): Promise<boolean> {
  const response = await fetch("/api/admin/session", { signal });
  if (response.status === 401) return false;
  if (!response.ok) throw new ApiError(response.status);
  return true;
}

export function useAdminSession() {
  return useQuery({
    queryKey: SESSION_KEY,
    queryFn: ({ signal }) => fetchSession(signal),
    retry: false,
  });
}

export interface Credentials {
  email: string;
  password: string;
}

async function post(url: string, body?: unknown): Promise<void> {
  const response = await fetch(url, {
    method: "POST",
    headers: body === undefined ? undefined : { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!response.ok) throw new ApiError(response.status);
}

export function useLogin() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (credentials: Credentials) => post("/api/admin/login", credentials),
    onSuccess: () => {
      queryClient.setQueryData(SESSION_KEY, true);
    },
  });
}

export function useLogout() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => post("/api/admin/logout"),
    onSuccess: () => {
      queryClient.setQueryData(SESSION_KEY, false);
    },
  });
}
