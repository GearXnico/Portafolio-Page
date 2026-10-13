import { fireEvent, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "../src/App";
import type { AdminProject, ProjectImage } from "../src/api/projects";
import { renderWithQuery } from "./render";

const COVER: ProjectImage = {
  id: 1,
  url: "/media/projects/portada.webp",
  alt_es: "Portada",
  alt_en: "Cover",
  position: 0,
};

const PROJECT = {
  id: 7,
  slug: "sitio",
  title_es: "Este sitio",
  title_en: "This site",
  summary_es: "Portafolio con CI",
  summary_en: "Portfolio with CI",
  body_es: "",
  body_en: "",
  stack: [],
  demo_url: null,
  repo_url: null,
  visible: true,
  position: 0,
  images: [COVER],
} as AdminProject;

const NEW_IMAGE: ProjectImage = {
  id: 2,
  url: "/media/projects/nueva.webp",
  alt_es: "Pantalla de inicio",
  alt_en: "Home screen",
  position: 1,
};

/** Simula la API del panel: `routes` da el código y el cuerpo por "MÉTODO url". */
function stubApi(routes: Record<string, [number, unknown]>) {
  const fetchMock = vi.fn((url: string, init?: RequestInit) => {
    const [status, body] = routes[`${init?.method ?? "GET"} ${url}`] ?? [200, {}];
    // Un 204 no puede llevar cuerpo.
    return Promise.resolve(new Response(status === 204 ? null : JSON.stringify(body), { status }));
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

function calls(fetchMock: ReturnType<typeof stubApi>, method: string) {
  return fetchMock.mock.calls.filter(([, init]) => (init?.method ?? "GET") === method);
}

async function openProject() {
  renderWithQuery(<App />, "/admin/projects/7");
  return within(await screen.findByRole("region", { name: "Capturas" }));
}

/** Elige un archivo y llena los textos alternativos, que son obligatorios. */
function chooseFile(name = "inicio.png") {
  const file = new File(["png"], name, { type: "image/png" });
  fireEvent.change(screen.getByLabelText(/^Imagen/), { target: { files: [file] } });
  fireEvent.change(screen.getByLabelText("Texto alternativo en español"), {
    target: { value: "Pantalla de inicio" },
  });
  fireEvent.change(screen.getByLabelText("Texto alternativo en inglés"), {
    target: { value: "Home screen" },
  });
  return file;
}

afterEach(() => {
  vi.restoreAllMocks();
});

describe("capturas de un proyecto en el panel", () => {
  it("muestra las capturas guardadas", async () => {
    stubApi({ "GET /api/admin/projects/7": [200, PROJECT] });
    const section = await openProject();

    expect(section.getByRole("img", { name: "Portada" })).toHaveAttribute("src", COVER.url);
  });

  it("no sube sin los dos textos alternativos", async () => {
    const fetchMock = stubApi({ "GET /api/admin/projects/7": [200, PROJECT] });
    const section = await openProject();

    chooseFile();
    fireEvent.change(section.getByLabelText("Texto alternativo en inglés"), {
      target: { value: "" },
    });
    fireEvent.click(section.getByRole("button", { name: "Subir captura" }));

    expect(calls(fetchMock, "POST")).toHaveLength(0);
  });

  it("sin capturas lo dice, y no deja subir sin elegir un archivo", async () => {
    stubApi({ "GET /api/admin/projects/7": [200, { ...PROJECT, images: [] }] });
    const section = await openProject();

    expect(section.getByText("Este proyecto todavía no tiene capturas.")).toBeInTheDocument();
    expect(section.getByRole("button", { name: "Subir captura" })).toBeDisabled();
  });

  it("un proyecto nuevo pide guardarlo antes de subir capturas", async () => {
    stubApi({});
    renderWithQuery(<App />, "/admin/projects/new");

    expect(
      await screen.findByText("Guarda el proyecto para poder subirle capturas."),
    ).toBeInTheDocument();
    expect(screen.queryByRole("region", { name: "Capturas" })).not.toBeInTheDocument();
  });

  it("subir envía el archivo con sus textos y la muestra sin perder lo escrito en el formulario", async () => {
    const fetchMock = stubApi({
      "GET /api/admin/projects/7": [200, PROJECT],
      "POST /api/admin/projects/7/images": [201, NEW_IMAGE],
    });
    const section = await openProject();
    // Un cambio sin guardar en el formulario de al lado.
    fireEvent.change(screen.getByLabelText("Orden"), { target: { value: "4" } });

    const file = chooseFile();
    fireEvent.click(section.getByRole("button", { name: "Subir captura" }));

    expect(await section.findByRole("img", { name: "Pantalla de inicio" })).toBeInTheDocument();
    const [url, init] = calls(fetchMock, "POST")[0] ?? [];
    expect(url).toBe("/api/admin/projects/7/images");
    const sent = init?.body as FormData;
    expect(sent.get("file")).toBe(file);
    expect(sent.get("alt_es")).toBe("Pantalla de inicio");
    expect(sent.get("alt_en")).toBe("Home screen");
    // No vuelve a pedir el proyecto: el formulario conserva el cambio y los campos se limpian.
    expect(calls(fetchMock, "GET").filter(([url]) => url === "/api/admin/projects/7")).toHaveLength(
      1,
    );
    expect(screen.getByLabelText("Orden")).toHaveValue(4);
    expect(section.getByLabelText("Texto alternativo en español")).toHaveValue("");
  });

  it.each([
    [413, "La imagen pesa más de 5 MB."],
    [415, "El archivo no es una imagen JPEG, PNG o WebP."],
    [422, "La imagen está dañada"],
    [500, "No se pudo conectar"],
  ])("si la subida responde %i, lo avisa", async (status, text) => {
    stubApi({
      "GET /api/admin/projects/7": [200, PROJECT],
      "POST /api/admin/projects/7/images": [status, {}],
    });
    const section = await openProject();

    chooseFile();
    fireEvent.click(section.getByRole("button", { name: "Subir captura" }));

    expect(await section.findByRole("alert")).toHaveTextContent(text);
  });

  it("borrar pide confirmación y quita la captura", async () => {
    const fetchMock = stubApi({
      "GET /api/admin/projects/7": [200, PROJECT],
      "DELETE /api/admin/projects/7/images/1": [204, null],
    });
    const confirm = vi.spyOn(window, "confirm").mockReturnValue(true);
    const section = await openProject();

    fireEvent.click(section.getByRole("button", { name: "Borrar" }));

    expect(
      await section.findByText("Este proyecto todavía no tiene capturas."),
    ).toBeInTheDocument();
    expect(confirm).toHaveBeenCalled();
    expect(calls(fetchMock, "DELETE")[0]?.[0]).toBe("/api/admin/projects/7/images/1");
  });

  it("un borrado correcto quita el error de una subida fallida", async () => {
    stubApi({
      "GET /api/admin/projects/7": [200, PROJECT],
      "POST /api/admin/projects/7/images": [413, {}],
      "DELETE /api/admin/projects/7/images/1": [204, null],
    });
    vi.spyOn(window, "confirm").mockReturnValue(true);
    const section = await openProject();
    chooseFile();
    fireEvent.click(section.getByRole("button", { name: "Subir captura" }));
    await section.findByRole("alert");

    fireEvent.click(section.getByRole("button", { name: "Borrar" }));

    expect(
      await section.findByText("Este proyecto todavía no tiene capturas."),
    ).toBeInTheDocument();
    expect(section.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("si no se confirma, no borra nada", async () => {
    const fetchMock = stubApi({ "GET /api/admin/projects/7": [200, PROJECT] });
    vi.spyOn(window, "confirm").mockReturnValue(false);
    const section = await openProject();

    fireEvent.click(section.getByRole("button", { name: "Borrar" }));

    expect(calls(fetchMock, "DELETE")).toHaveLength(0);
    expect(section.getByRole("img", { name: "Portada" })).toBeInTheDocument();
  });
});
