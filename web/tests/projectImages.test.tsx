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

/** Fakes the admin panel API: `routes` gives the status and body by "METHOD url". */
function stubApi(routes: Record<string, [number, unknown]>) {
  const fetchMock = vi.fn((url: string, init?: RequestInit) => {
    const [status, body] = routes[`${init?.method ?? "GET"} ${url}`] ?? [200, {}];
    // A 204 can't have a body.
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

/** Picks a file and fills in the alt texts, which are required. */
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

describe("project screenshots in the admin panel", () => {
  it("shows the saved screenshots", async () => {
    stubApi({ "GET /api/admin/projects/7": [200, PROJECT] });
    const section = await openProject();

    expect(section.getByRole("img", { name: "Portada" })).toHaveAttribute("src", COVER.url);
  });

  it("doesn't upload without both alt texts", async () => {
    const fetchMock = stubApi({ "GET /api/admin/projects/7": [200, PROJECT] });
    const section = await openProject();

    chooseFile();
    fireEvent.change(section.getByLabelText("Texto alternativo en inglés"), {
      target: { value: "" },
    });
    fireEvent.click(section.getByRole("button", { name: "Subir captura" }));

    expect(calls(fetchMock, "POST")).toHaveLength(0);
  });

  it("says so when there are no screenshots, and doesn't allow uploading without picking a file", async () => {
    stubApi({ "GET /api/admin/projects/7": [200, { ...PROJECT, images: [] }] });
    const section = await openProject();

    expect(section.getByText("Este proyecto todavía no tiene capturas.")).toBeInTheDocument();
    expect(section.getByRole("button", { name: "Subir captura" })).toBeDisabled();
  });

  it("a new project asks to be saved before uploading screenshots", async () => {
    stubApi({});
    renderWithQuery(<App />, "/admin/projects/new");

    expect(
      await screen.findByText("Guarda el proyecto para poder subirle capturas."),
    ).toBeInTheDocument();
    expect(screen.queryByRole("region", { name: "Capturas" })).not.toBeInTheDocument();
  });

  it("uploading sends the file with its texts and shows it without losing what was typed in the form", async () => {
    const fetchMock = stubApi({
      "GET /api/admin/projects/7": [200, PROJECT],
      "POST /api/admin/projects/7/images": [201, NEW_IMAGE],
    });
    const section = await openProject();
    // An unsaved change in the form next to it.
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
    // It doesn't fetch the project again: the form keeps the change and the fields are cleared.
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
  ])("if the upload responds %i, shows a notice", async (status, text) => {
    stubApi({
      "GET /api/admin/projects/7": [200, PROJECT],
      "POST /api/admin/projects/7/images": [status, {}],
    });
    const section = await openProject();

    chooseFile();
    fireEvent.click(section.getByRole("button", { name: "Subir captura" }));

    expect(await section.findByRole("alert")).toHaveTextContent(text);
  });

  it("deleting asks for confirmation and removes the screenshot", async () => {
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

  it("a successful delete clears the error from a failed upload", async () => {
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

  it("if not confirmed, deletes nothing", async () => {
    const fetchMock = stubApi({ "GET /api/admin/projects/7": [200, PROJECT] });
    vi.spyOn(window, "confirm").mockReturnValue(false);
    const section = await openProject();

    fireEvent.click(section.getByRole("button", { name: "Borrar" }));

    expect(calls(fetchMock, "DELETE")).toHaveLength(0);
    expect(section.getByRole("img", { name: "Portada" })).toBeInTheDocument();
  });
});
