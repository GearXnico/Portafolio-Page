import { fireEvent, screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { App } from "../src/App";
import type { AdminProject } from "../src/api/projects";
import { renderWithQuery } from "./render";

const PROJECT = {
  id: 7,
  slug: "sitio",
  title_es: "Este sitio",
  title_en: "This site",
  summary_es: "Portafolio con CI",
  summary_en: "Portfolio with CI",
  body_es: "",
  body_en: "",
  stack: ["React", "FastAPI"],
  demo_url: null,
  repo_url: "https://github.com/ejemplo/sitio",
  status: "done",
  visible: false,
  position: 2,
  // Fields the API sends but that aren't edited: they must not come back in the PUT.
  images: [],
  created_at: "2026-10-01T00:00:00Z",
  updated_at: "2026-10-01T00:00:00Z",
} as AdminProject;

/** Fakes the admin panel API with a session: `routes` gives the status and body by "METHOD url". */
function stubApi(routes: Record<string, [number, unknown]>) {
  const fetchMock = vi.fn((url: string, init?: RequestInit) => {
    const [status, body] = routes[`${init?.method ?? "GET"} ${url}`] ?? [200, {}];
    return Promise.resolve(new Response(JSON.stringify(body), { status }));
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

function sentBody(fetchMock: ReturnType<typeof stubApi>, method: string): unknown {
  const call = fetchMock.mock.calls.find(([, init]) => init?.method === method);
  return JSON.parse(call?.[1]?.body as string);
}

function fillNewProject() {
  for (const [lang, title, summary] of [
    ["Español", "Juego", "Un juego"],
    ["English", "Game", "A game"],
  ]) {
    const group = within(screen.getByRole("group", { name: lang }));
    fireEvent.change(group.getByLabelText("Título"), { target: { value: title } });
    fireEvent.change(group.getByLabelText("Resumen"), { target: { value: summary } });
  }
  fireEvent.change(screen.getByLabelText(/^Slug/), { target: { value: "juego" } });
  fireEvent.change(screen.getByLabelText(/^Stack/), { target: { value: " Godot, , C# " } });
  fireEvent.click(screen.getByLabelText("Visible en la página"));
}

describe("projects in the admin panel", () => {
  it("the admin panel home links to the projects", async () => {
    stubApi({});
    renderWithQuery(<App />, "/admin");

    fireEvent.click(await screen.findByRole("link", { name: "Proyectos" }));

    expect(await screen.findByRole("heading", { name: "Proyectos" })).toBeInTheDocument();
  });

  it("the list shows the order and marks hidden ones", async () => {
    stubApi({ "GET /api/admin/projects": [200, [PROJECT]] });
    renderWithQuery(<App />, "/admin/projects");

    const item = await screen.findByRole("listitem");
    expect(within(item).getByRole("link", { name: "Este sitio" })).toHaveAttribute(
      "href",
      "/admin/projects/7",
    );
    expect(item).toHaveTextContent("Orden 2 · oculto");
  });

  it("says so when there are no projects", async () => {
    stubApi({ "GET /api/admin/projects": [200, []] });
    renderWithQuery(<App />, "/admin/projects");

    expect(await screen.findByText("Todavía no hay proyectos.")).toBeInTheDocument();
  });

  it("if the list doesn't load, shows a notice", async () => {
    stubApi({ "GET /api/admin/projects": [500, {}] });
    renderWithQuery(<App />, "/admin/projects");

    expect(await screen.findByRole("alert")).toHaveTextContent("No se pudo conectar");
  });

  it("creating sends both languages, the stack, the status and the visibility, and goes back to the list", async () => {
    const fetchMock = stubApi({
      "POST /api/admin/projects": [201, PROJECT],
      "GET /api/admin/projects": [200, []],
    });
    renderWithQuery(<App />, "/admin/projects/new");
    await screen.findByRole("heading", { name: "Nuevo proyecto" });

    fillNewProject();
    fireEvent.change(screen.getByLabelText("Estado (sello en la página)"), {
      target: { value: "in_progress" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Guardar" }));

    expect(await screen.findByRole("heading", { name: "Proyectos" })).toBeInTheDocument();
    expect(sentBody(fetchMock, "POST")).toEqual({
      slug: "juego",
      title_es: "Juego",
      title_en: "Game",
      summary_es: "Un juego",
      summary_en: "A game",
      body_es: "",
      body_en: "",
      stack: ["Godot", "C#"],
      demo_url: null,
      repo_url: null,
      status: "in_progress",
      visible: true,
      position: 0,
    });
  });

  it.each([
    [409, "Ya existe un proyecto con ese slug."],
    [422, "Revisa los datos"],
    [500, "No se pudo conectar"],
  ])("if saving responds %i, shows a notice and stays on the form", async (status, text) => {
    stubApi({ "POST /api/admin/projects": [status, {}] });
    renderWithQuery(<App />, "/admin/projects/new");
    await screen.findByRole("heading", { name: "Nuevo proyecto" });

    fillNewProject();
    fireEvent.click(screen.getByRole("button", { name: "Guardar" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(text);
    expect(screen.getByRole("heading", { name: "Nuevo proyecto" })).toBeInTheDocument();
  });

  it("editing loads the project and the PUT sends only the editable fields", async () => {
    const fetchMock = stubApi({
      "GET /api/admin/projects/7": [200, PROJECT],
      "PUT /api/admin/projects/7": [200, PROJECT],
      "GET /api/admin/projects": [200, [PROJECT]],
    });
    renderWithQuery(<App />, "/admin/projects/7");

    const english = within(await screen.findByRole("group", { name: "English" }));
    expect(english.getByLabelText("Título")).toHaveValue("This site");
    fireEvent.change(screen.getByLabelText("Orden"), { target: { value: "5" } });
    fireEvent.click(screen.getByRole("button", { name: "Guardar" }));

    expect(await screen.findByRole("heading", { name: "Proyectos" })).toBeInTheDocument();
    expect(sentBody(fetchMock, "PUT")).toEqual({
      slug: "sitio",
      title_es: "Este sitio",
      title_en: "This site",
      summary_es: "Portafolio con CI",
      summary_en: "Portfolio with CI",
      body_es: "",
      body_en: "",
      stack: ["React", "FastAPI"],
      demo_url: null,
      repo_url: "https://github.com/ejemplo/sitio",
      status: "done",
      visible: false,
      position: 5,
    });
  });

  it("if the project doesn't exist, shows a notice", async () => {
    stubApi({ "GET /api/admin/projects/99": [404, {}] });
    renderWithQuery(<App />, "/admin/projects/99");

    expect(await screen.findByRole("alert")).toHaveTextContent("No se pudo cargar el proyecto.");
  });
});
