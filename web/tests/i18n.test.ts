import { afterEach, describe, expect, it, vi } from "vitest";

import en from "../src/i18n/en.json";
import es from "../src/i18n/es.json";
import { isLang, localized, storedLang, storeLang, translate } from "../src/i18n";

describe("i18n", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("es.json y en.json tienen las mismas claves", () => {
    expect(Object.keys(en).sort()).toEqual(Object.keys(es).sort());
  });

  it("traduce según el idioma", () => {
    expect(translate("es", "app.title")).toBe("Producto");
    expect(translate("en", "app.title")).toBe("Product");
  });

  it("elige el campo _es o _en", () => {
    const project = { title_es: "Hola", title_en: "Hello" };
    expect(localized(project, "title", "es")).toBe("Hola");
    expect(localized(project, "title", "en")).toBe("Hello");
  });

  it("solo acepta es y en", () => {
    expect(isLang("es")).toBe(true);
    expect(isLang("en")).toBe(true);
    expect(isLang("fr")).toBe(false);
    expect(isLang(null)).toBe(false);
  });

  it("guarda y lee el idioma, e ignora valores inválidos", () => {
    expect(storedLang()).toBeNull();
    storeLang("en");
    expect(storedLang()).toBe("en");
    localStorage.setItem("lang", "<script>");
    expect(storedLang()).toBeNull();
  });

  it("sin localStorage disponible no falla", () => {
    vi.spyOn(Storage.prototype, "getItem").mockImplementation(() => {
      throw new Error("bloqueado");
    });
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
      throw new Error("bloqueado");
    });

    expect(() => {
      storeLang("en");
    }).not.toThrow();
    expect(storedLang()).toBeNull();
  });
});
