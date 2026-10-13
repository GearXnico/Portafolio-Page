import { fireEvent, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { App } from "../src/App";
import { renderWithQuery } from "./render";

/** Simula la API del panel: cada ruta responde con el código que indica `statuses`. */
function stubAdminApi(statuses: { session?: number; login?: number; logout?: number }) {
  const fetchMock = vi.fn((input: string) => {
    const status =
      input === "/api/admin/session"
        ? (statuses.session ?? 401)
        : input === "/api/admin/login"
          ? (statuses.login ?? 200)
          : (statuses.logout ?? 204);
    return Promise.resolve(new Response(status === 204 ? null : "{}", { status }));
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

function fillLogin() {
  fireEvent.change(screen.getByLabelText("Correo"), { target: { value: "admin@example.com" } });
  fireEvent.change(screen.getByLabelText("Contraseña"), { target: { value: "una-clave-larga" } });
  fireEvent.click(screen.getByRole("button", { name: "Entrar" }));
}

describe("panel /admin", () => {
  it("sin sesión redirige al login", async () => {
    stubAdminApi({ session: 401 });

    renderWithQuery(<App />, "/admin");

    expect(await screen.findByRole("heading", { name: "Iniciar sesión" })).toBeInTheDocument();
  });

  it("con sesión muestra el panel", async () => {
    stubAdminApi({ session: 200 });

    renderWithQuery(<App />, "/admin");

    expect(
      await screen.findByRole("heading", { name: "Panel de administración" }),
    ).toBeInTheDocument();
  });

  it("si la API no responde, avisa en vez de mandar al login", async () => {
    stubAdminApi({ session: 500 });

    renderWithQuery(<App />, "/admin");

    expect(await screen.findByRole("alert")).toHaveTextContent("No se pudo conectar");
    expect(screen.queryByRole("heading", { name: "Iniciar sesión" })).not.toBeInTheDocument();
  });

  it("el login correcto envía las credenciales y entra al panel", async () => {
    const fetchMock = stubAdminApi({ session: 401, login: 200 });
    renderWithQuery(<App />, "/admin/login");

    fillLogin();

    expect(
      await screen.findByRole("heading", { name: "Panel de administración" }),
    ).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/admin/login",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ email: "admin@example.com", password: "una-clave-larga" }),
      }),
    );
  });

  it.each([
    [401, "Correo o contraseña incorrectos."],
    [429, "Demasiados intentos. Intenta de nuevo en 15 minutos."],
    [503, "No se pudo conectar con el servidor. Intenta de nuevo en unos minutos."],
  ])("si el login responde %i, muestra el mensaje y sigue en el login", async (status, text) => {
    stubAdminApi({ login: status });
    renderWithQuery(<App />, "/admin/login");

    fillLogin();

    expect(await screen.findByRole("alert")).toHaveTextContent(text);
    expect(screen.getByRole("heading", { name: "Iniciar sesión" })).toBeInTheDocument();
  });

  it("cerrar sesión llama al logout y vuelve al login", async () => {
    const fetchMock = stubAdminApi({ session: 200 });
    renderWithQuery(<App />, "/admin");

    fireEvent.click(await screen.findByRole("button", { name: "Cerrar sesión" }));

    expect(await screen.findByRole("heading", { name: "Iniciar sesión" })).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/admin/logout",
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("si el logout falla, lo avisa y sigue en el panel", async () => {
    stubAdminApi({ session: 200, logout: 500 });
    renderWithQuery(<App />, "/admin");

    fireEvent.click(await screen.findByRole("button", { name: "Cerrar sesión" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("No se pudo conectar");
    expect(screen.getByRole("heading", { name: "Panel de administración" })).toBeInTheDocument();
  });

  it("usa el idioma elegido en el selector", async () => {
    localStorage.setItem("lang", "en");
    stubAdminApi({ session: 401 });

    renderWithQuery(<App />, "/admin");

    expect(await screen.findByRole("heading", { name: "Sign in" })).toBeInTheDocument();
    await waitFor(() => {
      expect(document.documentElement.lang).toBe("en");
    });
    expect(document.title).toBe("Admin panel");
    expect(document.querySelector('meta[name="robots"]')).toHaveAttribute("content", "noindex");
  });

  it("el selector cambia el idioma del panel y lo recuerda", async () => {
    stubAdminApi({ session: 401 });
    renderWithQuery(<App />, "/admin/login");

    fireEvent.click(await screen.findByRole("button", { name: "English" }));

    expect(screen.getByRole("heading", { name: "Sign in" })).toBeInTheDocument();
    expect(localStorage.getItem("lang")).toBe("en");
  });

  it("el panel no pide bootstrap, para no registrar una visita", async () => {
    const fetchMock = stubAdminApi({ session: 401 });

    renderWithQuery(<App />, "/admin");

    await screen.findByRole("heading", { name: "Iniciar sesión" });
    expect(fetchMock).not.toHaveBeenCalledWith(
      expect.stringContaining("/api/bootstrap"),
      expect.anything(),
    );
  });
});
