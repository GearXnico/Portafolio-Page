import { describe, expect, it } from "vitest";

import { headlineName, httpsUrl, monthYear, ownRepoUrl } from "../src/content";
import { projectFixture } from "./fixtures";

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

  it("takes the name from the start of the headline", () => {
    expect(headlineName("Ana Pérez · Backend developer")).toBe("Ana Pérez");
    expect(headlineName("Backend developer")).toBe("Backend developer");
  });

  it("finds the repository of the project deployed on this same host", () => {
    const own = projectFixture({
      demo_url: "https://me.example/",
      repo_url: "https://github.com/me/site",
    });
    const other = projectFixture({
      demo_url: "https://other.example/",
      repo_url: "https://github.com/me/other",
    });

    expect(ownRepoUrl([other, own], "me.example")).toBe("https://github.com/me/site");
    expect(ownRepoUrl([other], "me.example")).toBeNull();
    expect(ownRepoUrl([{ ...own, repo_url: "javascript:alert(1)" }], "me.example")).toBeNull();
  });
});
