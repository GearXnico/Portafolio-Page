import { afterEach, describe, expect, it, vi } from "vitest";

import en from "../src/i18n/en.json";
import es from "../src/i18n/es.json";
import { isLang, localized, storedLang, storeLang, translate } from "../src/i18n";

describe("i18n", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("es.json and en.json have the same keys", () => {
    expect(Object.keys(en).sort()).toEqual(Object.keys(es).sort());
  });

  it("translates by language", () => {
    expect(translate("es", "app.title")).toBe("Producto");
    expect(translate("en", "app.title")).toBe("Product");
  });

  it("picks the _es or _en field", () => {
    const project = { title_es: "Hola", title_en: "Hello" };
    expect(localized(project, "title", "es")).toBe("Hola");
    expect(localized(project, "title", "en")).toBe("Hello");
  });

  it("only accepts es and en", () => {
    expect(isLang("es")).toBe(true);
    expect(isLang("en")).toBe(true);
    expect(isLang("fr")).toBe(false);
    expect(isLang(null)).toBe(false);
  });

  it("saves and reads the language, and ignores invalid values", () => {
    expect(storedLang()).toBeNull();
    storeLang("en");
    expect(storedLang()).toBe("en");
    localStorage.setItem("lang", "<script>");
    expect(storedLang()).toBeNull();
  });

  it("doesn't fail without localStorage available", () => {
    vi.spyOn(Storage.prototype, "getItem").mockImplementation(() => {
      throw new Error("blocked");
    });
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
      throw new Error("blocked");
    });

    expect(() => {
      storeLang("en");
    }).not.toThrow();
    expect(storedLang()).toBeNull();
  });
});
