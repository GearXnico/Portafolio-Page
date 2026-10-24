import { describe, expect, it } from "vitest";

import { readUtm } from "../src/utm";

describe("readUtm", () => {
  it("reads the four UTM parameters and leaves out the others", () => {
    const search =
      "?utm_source=linkedin&utm_medium=social&utm_campaign=postulacion&utm_content=perfil&otro=x";

    expect(readUtm(search)).toEqual({
      utm_source: "linkedin",
      utm_medium: "social",
      utm_campaign: "postulacion",
      utm_content: "perfil",
    });
  });

  it("without UTM parameters, or with empty ones, returns an empty object", () => {
    expect(readUtm("")).toEqual({});
    expect(readUtm("?utm_source=%20%20&utm_campaign=")).toEqual({});
  });

  it("removes line breaks and control characters, and trims to 200 characters", () => {
    const long = "😀".repeat(250);
    const utm = readUtm(`?utm_source=%20linked%0Ain%00%E2%80%A8&utm_campaign=${long}`);

    expect(utm.utm_source).toBe("linkedin");
    // Characters are counted, not UTF-16 code units: no emoji gets split.
    expect(Array.from(utm.utm_campaign ?? "")).toHaveLength(200);
    expect(utm.utm_campaign).toBe("😀".repeat(200));
  });
});
