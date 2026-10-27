import { describe, expect, it } from "vitest";

import { CITY_HEIGHT, skyline } from "../src/city";

describe("city", () => {
  it("draws the same skyline on every visit", () => {
    expect(skyline()).toEqual(skyline());
    expect(skyline(1)).not.toEqual(skyline(2));
  });

  it("keeps windows and signs inside the drawing", () => {
    const { far, near, windows, signs } = skyline();

    expect(far).toMatch(/^M/);
    expect(near).toMatch(/^M/);
    expect(windows.length).toBeGreaterThan(0);
    for (const { y } of windows) expect(y).toBeLessThan(CITY_HEIGHT);
    for (const { y, height } of signs) expect(y + height).toBeLessThanOrEqual(CITY_HEIGHT);
  });
});
