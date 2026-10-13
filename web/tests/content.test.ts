import { describe, expect, it } from "vitest";

import { httpsUrl, monthYear } from "../src/content";

describe("content", () => {
  it("accepts only https URLs", () => {
    expect(httpsUrl("https://a.cl/x")).toBe("https://a.cl/x");
    expect(httpsUrl("HTTPS://a.cl")).toBe("HTTPS://a.cl");
    expect(httpsUrl("http://a.cl")).toBeNull();
    expect(httpsUrl("javascript:alert(1)")).toBeNull();
    expect(httpsUrl("//a.cl")).toBeNull();
    expect(httpsUrl(null)).toBeNull();
  });

  it("formats month and year without shifting with the time zone", () => {
    expect(monthYear("2024-01-01", "en")).toBe("Jan 2024");
  });
});
