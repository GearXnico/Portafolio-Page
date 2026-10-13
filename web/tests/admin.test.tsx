import { fireEvent, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { App } from "../src/App";
import { renderWithQuery } from "./render";

/**
 * Fakes the admin panel API (application programming interface): each route responds with the
 * status code given in `statuses`.
 */
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

describe("admin panel /admin", () => {
  it("without a session redirects to the login", async () => {
    stubAdminApi({ session: 401 });

    renderWithQuery(<App />, "/admin");

    expect(await screen.findByRole("heading", { name: "Iniciar sesión" })).toBeInTheDocument();
  });

  it("with a session shows the admin panel", async () => {
    stubAdminApi({ session: 200 });

    renderWithQuery(<App />, "/admin");

    expect(
      await screen.findByRole("heading", { name: "Panel de administración" }),
    ).toBeInTheDocument();
  });

  it("if the API doesn't respond, shows a notice instead of sending to the login", async () => {
    stubAdminApi({ session: 500 });

    renderWithQuery(<App />, "/admin");

    expect(await screen.findByRole("alert")).toHaveTextContent("No se pudo conectar");
    expect(screen.queryByRole("heading", { name: "Iniciar sesión" })).not.toBeInTheDocument();
  });

  it("a correct login sends the credentials and enters the admin panel", async () => {
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
  ])("if the login responds %i, shows the message and stays on the login", async (status, text) => {
    stubAdminApi({ login: status });
    renderWithQuery(<App />, "/admin/login");

    fillLogin();

    expect(await screen.findByRole("alert")).toHaveTextContent(text);
    expect(screen.getByRole("heading", { name: "Iniciar sesión" })).toBeInTheDocument();
  });

  it("logging out calls logout and goes back to the login", async () => {
    const fetchMock = stubAdminApi({ session: 200 });
    renderWithQuery(<App />, "/admin");

    fireEvent.click(await screen.findByRole("button", { name: "Cerrar sesión" }));

    expect(await screen.findByRole("heading", { name: "Iniciar sesión" })).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/admin/logout",
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("if logout fails, shows a notice and stays in the admin panel", async () => {
    stubAdminApi({ session: 200, logout: 500 });
    renderWithQuery(<App />, "/admin");

    fireEvent.click(await screen.findByRole("button", { name: "Cerrar sesión" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("No se pudo conectar");
    expect(screen.getByRole("heading", { name: "Panel de administración" })).toBeInTheDocument();
  });

  it("uses the language picked in the switcher", async () => {
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

  it("the switcher changes the admin panel language and remembers it", async () => {
    stubAdminApi({ session: 401 });
    renderWithQuery(<App />, "/admin/login");

    fireEvent.click(await screen.findByRole("button", { name: "English" }));

    expect(screen.getByRole("heading", { name: "Sign in" })).toBeInTheDocument();
    expect(localStorage.getItem("lang")).toBe("en");
  });

  it("the admin panel doesn't fetch bootstrap, so no visit is recorded", async () => {
    const fetchMock = stubAdminApi({ session: 401 });

    renderWithQuery(<App />, "/admin");

    await screen.findByRole("heading", { name: "Iniciar sesión" });
    expect(fetchMock).not.toHaveBeenCalledWith(
      expect.stringContaining("/api/bootstrap"),
      expect.anything(),
    );
  });
});
