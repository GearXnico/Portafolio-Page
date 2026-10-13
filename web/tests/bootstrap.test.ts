import { afterEach, describe, expect, it, vi } from "vitest";

import { fetchBootstrap } from "../src/api/bootstrap";

describe("fetchBootstrap", () => {
  afterEach(() => {
    window.history.replaceState(null, "", "/");
    vi.restoreAllMocks();
    localStorage.clear();
  });

  it("envía las UTM de la URL, el referrer y el idioma guardado", async () => {
    window.history.replaceState(null, "", "/?utm_source=linkedin&utm_campaign=postulacion&x=1");
    vi.spyOn(document, "referrer", "get").mockReturnValue("https://www.linkedin.com/feed/");
    localStorage.setItem("lang", "en");
    const fetchMock = vi.fn().mockResolvedValue(new Response('{"lang":"en"}'));
    vi.stubGlobal("fetch", fetchMock);

    await fetchBootstrap();
    const [url] = fetchMock.mock.calls[0] as [string];
    const params = new URL(url, "http://localhost").searchParams;
    expect(Object.fromEntries(params)).toEqual({
      utm_source: "linkedin",
      utm_campaign: "postulacion",
      referrer: "https://www.linkedin.com/feed/",
      lang: "en",
    });
  });

  it("no envía lang si no hay uno guardado válido", async () => {
    localStorage.setItem("lang", "fr");
    const fetchMock = vi.fn().mockResolvedValue(new Response('{"lang":"es"}'));
    vi.stubGlobal("fetch", fetchMock);

    await expect(fetchBootstrap()).resolves.toMatchObject({ lang: "es" });
    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toBe("/api/bootstrap");
    expect(init.signal).toBeInstanceOf(AbortSignal);
  });

  it("falla si la API responde con error", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response("", { status: 503 })));

    await expect(fetchBootstrap()).rejects.toThrow("503");
  });

  it("se corta si la API no responde a tiempo", async () => {
    // Un fetch que nunca responde y solo termina si se aborta.
    const hangingFetch = vi.fn(
      (_url: string, init: RequestInit) =>
        new Promise((_resolve, reject) => {
          init.signal?.addEventListener("abort", () => {
            reject(new Error("abortado"));
          });
        }),
    );
    vi.stubGlobal("fetch", hangingFetch);

    await expect(fetchBootstrap(undefined, 10)).rejects.toThrow("abortado");
  });
});
