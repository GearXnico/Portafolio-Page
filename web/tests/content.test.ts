import { describe, expect, it } from "vitest";

import { httpsUrl, monthYear } from "../src/content";

describe("content", () => {
  it("acepta solo URL https", () => {
    expect(httpsUrl("https://a.cl/x")).toBe("https://a.cl/x");
    expect(httpsUrl("HTTPS://a.cl")).toBe("HTTPS://a.cl");
    expect(httpsUrl("http://a.cl")).toBeNull();
    expect(httpsUrl("javascript:alert(1)")).toBeNull();
    expect(httpsUrl("//a.cl")).toBeNull();
    expect(httpsUrl(null)).toBeNull();
  });

  it("formatea mes y año sin correrse por la zona horaria", () => {
    expect(monthYear("2024-01-01", "en")).toBe("Jan 2024");
  });
});
