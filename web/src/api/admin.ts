// Admin panel session: the API sets an httpOnly cookie on login, so the web app never sees the
// token; it only asks GET /api/admin/session whether the session is still valid.
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

export const SESSION_KEY = ["admin", "session"] as const;

/** Error with the HTTP status code, so the form shows the matching message. */
export class ApiError extends Error {
  constructor(readonly status: number) {
    super(`the API responded ${String(status)}`);
  }
}

/** true with a session, false without one (401). Any other response is an error. */
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
