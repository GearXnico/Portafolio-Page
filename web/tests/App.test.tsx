import { fireEvent, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { App } from "../src/App";
import { renderWithQuery } from "./render";

function bootstrapBody(lang: string) {
  return JSON.stringify({ lang, profile: null, skills: [], experience: [], projects: [] });
}

/** Fakes the API: /api/bootstrap responds with `lang` and /api/health with ok. */
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
  it("without content shows the template title", async () => {
    stubApi("es");

    renderWithQuery(<App />);

    expect(await screen.findByRole("heading", { name: "Producto" })).toBeInTheDocument();
  });

  it("uses the language the API decides", async () => {
    stubApi("en");

    renderWithQuery(<App />);

    expect(await screen.findByRole("heading", { name: "Product" })).toBeInTheDocument();
    expect(document.documentElement.lang).toBe("en");
    expect(screen.getByRole("button", { name: "English" })).toHaveAttribute("aria-pressed", "true");
  });

  it("the saved choice overrides the API and is sent in bootstrap", async () => {
    localStorage.setItem("lang", "en");
    const fetchMock = stubApi("es");

    renderWithQuery(<App />);

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith("/api/bootstrap?lang=en", expect.anything());
    });
    expect(screen.getByRole("heading", { name: "Product" })).toBeInTheDocument();
  });

  it("the switcher changes the language and remembers it", async () => {
    stubApi("en");
    renderWithQuery(<App />);
    await screen.findByRole("heading", { name: "Product" });

    fireEvent.click(screen.getByRole("button", { name: "Español" }));

    expect(screen.getByRole("heading", { name: "Producto" })).toBeInTheDocument();
    expect(localStorage.getItem("lang")).toBe("es");
    expect(document.documentElement.lang).toBe("es");
  });

  it("if bootstrap fails, the page stays in Spanish", async () => {
    const fetchMock = stubApi(null);

    renderWithQuery(<App />);

    expect(await screen.findByRole("heading", { name: "Producto" })).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith("/api/bootstrap", expect.anything());
  });

  it("shows no text while waiting for bootstrap", () => {
    vi.stubGlobal("fetch", vi.fn().mockReturnValue(new Promise(() => undefined)));

    renderWithQuery(<App />);

    expect(screen.queryByRole("heading")).not.toBeInTheDocument();
  });
});
