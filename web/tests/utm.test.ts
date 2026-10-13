import { describe, expect, it } from "vitest";

import { readUtm } from "../src/utm";

describe("readUtm", () => {
  it("lee las cuatro UTM y deja fuera los demás parámetros", () => {
    const search =
      "?utm_source=linkedin&utm_medium=social&utm_campaign=postulacion&utm_content=perfil&otro=x";

    expect(readUtm(search)).toEqual({
      utm_source: "linkedin",
      utm_medium: "social",
      utm_campaign: "postulacion",
      utm_content: "perfil",
    });
  });

  it("sin UTM, o con UTM vacías, devuelve un objeto vacío", () => {
    expect(readUtm("")).toEqual({});
    expect(readUtm("?utm_source=%20%20&utm_campaign=")).toEqual({});
  });

  it("quita saltos de línea y caracteres de control, y recorta a 200 caracteres", () => {
    const long = "😀".repeat(250);
    const utm = readUtm(`?utm_source=%20linked%0Ain%00%E2%80%A8&utm_campaign=${long}`);

    expect(utm.utm_source).toBe("linkedin");
    // Se cuentan caracteres, no unidades UTF-16: ningún emoji queda partido.
    expect(Array.from(utm.utm_campaign ?? "")).toHaveLength(200);
    expect(utm.utm_campaign).toBe("😀".repeat(200));
  });
});
