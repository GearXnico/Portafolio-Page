import { afterEach, describe, expect, it, vi } from "vitest";

import { fetchBootstrap } from "../src/api/bootstrap";

describe("fetchBootstrap", () => {
  afterEach(() => {
    window.history.replaceState(null, "", "/");
    vi.restoreAllMocks();
    localStorage.clear();
  });

  it("sends the UTM (Urchin Tracking Module) parameters from the URL, the referrer and the saved language", async () => {
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

  it("doesn't send lang if there is no valid saved one", async () => {
    localStorage.setItem("lang", "fr");
    const fetchMock = vi.fn().mockResolvedValue(new Response('{"lang":"es"}'));
    vi.stubGlobal("fetch", fetchMock);

    await expect(fetchBootstrap()).resolves.toMatchObject({ lang: "es" });
    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toBe("/api/bootstrap");
    expect(init.signal).toBeInstanceOf(AbortSignal);
  });

  it("fails if the API (application programming interface) responds with an error", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response("", { status: 503 })));

    await expect(fetchBootstrap()).rejects.toThrow("503");
  });

  it("aborts if the API doesn't respond in time", async () => {
    // A fetch that never responds and only ends if it is aborted.
    const hangingFetch = vi.fn(
      (_url: string, init: RequestInit) =>
        new Promise((_resolve, reject) => {
          init.signal?.addEventListener("abort", () => {
            reject(new Error("aborted"));
          });
        }),
    );
    vi.stubGlobal("fetch", hangingFetch);

    await expect(fetchBootstrap(undefined, 10)).rejects.toThrow("aborted");
  });
});
