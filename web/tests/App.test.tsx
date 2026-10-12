import { fireEvent, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { App } from "../src/App";
import { renderWithQuery } from "./render";

function bootstrapBody(lang: string) {
  return JSON.stringify({ lang, profile: null, skills: [], experience: [], projects: [] });
}

/** Simula la API: /api/bootstrap responde con `lang` y /api/health con ok. */
function stubApi(lang: string | null) {
  const fetchMock = vi.fn((input: string) => {
    if (input.startsWith("/api/bootstrap")) {
      return Promise.resolve(
        lang === null ? new Response("", { status: 500 }) : new Response(bootstrapBody(lang)),
      );
    }
    return Promise.resolve(new Response("{}", { status: 200 }));
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

describe("App", () => {
  it("muestra el título y el estado de la API", async () => {
    stubApi("es");

    renderWithQuery(<App />);

    expect(await screen.findByRole("heading", { name: "Producto" })).toBeInTheDocument();
    expect(await screen.findByText("ok")).toBeInTheDocument();
  });

  it("usa el idioma que decide la API", async () => {
    stubApi("en");

    renderWithQuery(<App />);

    expect(await screen.findByRole("heading", { name: "Product" })).toBeInTheDocument();
    expect(document.documentElement.lang).toBe("en");
    expect(screen.getByRole("button", { name: "English" })).toHaveAttribute("aria-pressed", "true");
  });

  it("la elección guardada manda sobre la API y se envía en bootstrap", async () => {
    localStorage.setItem("lang", "en");
    const fetchMock = stubApi("es");

    renderWithQuery(<App />);

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith("/api/bootstrap?lang=en", expect.anything());
    });
    expect(screen.getByRole("heading", { name: "Product" })).toBeInTheDocument();
  });

  it("el selector cambia el idioma y lo recuerda", async () => {
    stubApi("en");
    renderWithQuery(<App />);
    await screen.findByRole("heading", { name: "Product" });

    fireEvent.click(screen.getByRole("button", { name: "Español" }));

    expect(screen.getByRole("heading", { name: "Producto" })).toBeInTheDocument();
    expect(screen.getByText("Estado de la API", { exact: false })).toBeInTheDocument();
    expect(localStorage.getItem("lang")).toBe("es");
    expect(document.documentElement.lang).toBe("es");
  });

  it("si bootstrap falla, la página queda en español", async () => {
    const fetchMock = stubApi(null);

    renderWithQuery(<App />);

    expect(await screen.findByRole("heading", { name: "Producto" })).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith("/api/bootstrap", expect.anything());
  });

  it("no muestra textos mientras espera a bootstrap", () => {
    vi.stubGlobal("fetch", vi.fn().mockReturnValue(new Promise(() => undefined)));

    renderWithQuery(<App />);

    expect(screen.queryByRole("heading")).not.toBeInTheDocument();
  });
});
