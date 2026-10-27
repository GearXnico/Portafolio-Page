import { fireEvent, screen, waitFor, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { App } from "../src/App";
import { renderWithQuery } from "./render";

type Reply = { status: number; body?: unknown };

/**
 * Fakes the API with a session: `routes` answers by "METHOD /path"; anything else gets 200 with {}.
 */
function stubApi(routes: Record<string, Reply>) {
  const fetchMock = vi.fn((url: string, init?: RequestInit) => {
    const reply = routes[`${init?.method ?? "GET"} ${url}`] ?? { status: 200, body: {} };
    const body = reply.status === 204 ? null : JSON.stringify(reply.body ?? {});
    return Promise.resolve(new Response(body, { status: reply.status }));
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

/** The JSON body sent to "METHOD /path". */
function sentBody(fetchMock: ReturnType<typeof stubApi>, method: string, url: string): unknown {
  const call = fetchMock.mock.calls.find(([u, init]) => u === url && init?.method === method);
  return call ? JSON.parse(call[1]?.body as string) : undefined;
}

const PROFILE = {
  headline_es: "Desarrollador",
  headline_en: "Developer",
  about_es: "Hola",
  about_en: "Hi",
  contact_email: "yo@example.com",
  links: { github: "https://github.com/example" },
  palette: null,
  updated_at: "2026-10-01T00:00:00Z",
};

const SKILL = { id: 7, name: "Python", category: "language", position: 0 };

const JOB = {
  id: 3,
  company: "Acme",
  role_es: "Dev",
  role_en: "Dev",
  description_es: "",
  description_en: "",
  start_date: "2024-01-01",
  end_date: null,
  position: 0,
};

function type(label: string, value: string, scope: Pick<typeof screen, "getByLabelText"> = screen) {
  fireEvent.change(scope.getByLabelText(label), { target: { value } });
}

describe("admin panel: profile, skills and experience", () => {
  it("the admin panel home links to profile, skills and experience", async () => {
    stubApi({});
    renderWithQuery(<App />, "/admin");

    const profile = await screen.findByRole("link", { name: "Perfil" });
    expect(profile).toHaveAttribute("href", "/admin/profile");
    expect(screen.getByRole("link", { name: "Experiencia" })).toHaveAttribute(
      "href",
      "/admin/experience",
    );
    fireEvent.click(screen.getByRole("link", { name: "Habilidades" }));

    expect(await screen.findByRole("heading", { name: "Habilidades" })).toBeInTheDocument();
  });

  it("saves the profile with both languages and only the fields the API accepts", async () => {
    const fetchMock = stubApi({
      "GET /api/admin/profile": { status: 200, body: PROFILE },
      "PUT /api/admin/profile": { status: 200, body: PROFILE },
    });
    renderWithQuery(<App />, "/admin/profile");

    expect(await screen.findByLabelText("Titular · Español")).toHaveValue("Desarrollador");
    type("Titular · English", "Engineer");
    type(
      "Enlaces, uno por línea: nombre y URL (github https://github.com/…)",
      "github https://github.com/example\n\n linkedin  https://linkedin.com/in/example",
    );
    expect(screen.getByRole("radio", { name: "Menta helada" })).toBeChecked();
    fireEvent.click(screen.getByRole("radio", { name: "Ámbar" }));
    fireEvent.click(screen.getByRole("button", { name: "Guardar" }));

    expect(await screen.findByRole("status")).toHaveTextContent("Guardado");
    const expected: Partial<typeof PROFILE> = { ...PROFILE };
    delete expected.updated_at;
    expect(sentBody(fetchMock, "PUT", "/api/admin/profile")).toEqual({
      ...expected,
      headline_en: "Engineer",
      palette: "amber",
      links: {
        github: "https://github.com/example",
        linkedin: "https://linkedin.com/in/example",
      },
    });
  });

  it("doesn't send links with a repeated name or an incomplete line", async () => {
    const fetchMock = stubApi({ "GET /api/admin/profile": { status: 200, body: PROFILE } });
    renderWithQuery(<App />, "/admin/profile");
    const label = "Enlaces, uno por línea: nombre y URL (github https://github.com/…)";
    await screen.findByLabelText(label);

    for (const text of ["github https://a.example\ngithub https://b.example", "github"]) {
      type(label, text);
      fireEvent.click(screen.getByRole("button", { name: "Guardar" }));
      expect(await screen.findByRole("alert")).toHaveTextContent("Revisa los campos");
    }
    expect(sentBody(fetchMock, "PUT", "/api/admin/profile")).toBeUndefined();
  });

  it("with no profile yet (404) shows the empty form", async () => {
    stubApi({ "GET /api/admin/profile": { status: 404 } });
    renderWithQuery(<App />, "/admin/profile");

    expect(await screen.findByLabelText("Titular · Español")).toHaveValue("");
  });

  it("if the API rejects the profile (422), asks to check the fields", async () => {
    stubApi({
      "GET /api/admin/profile": { status: 200, body: PROFILE },
      "PUT /api/admin/profile": { status: 422 },
    });
    renderWithQuery(<App />, "/admin/profile");

    fireEvent.click(await screen.findByRole("button", { name: "Guardar" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Revisa los campos");
  });

  it("if the profile doesn't load, shows a notice", async () => {
    stubApi({ "GET /api/admin/profile": { status: 500 } });
    renderWithQuery(<App />, "/admin/profile");

    expect(await screen.findByRole("alert")).toHaveTextContent("No se pudo conectar");
  });

  it("adds a new skill and leaves the form blank", async () => {
    const fetchMock = stubApi({
      "GET /api/admin/skills": { status: 200, body: [] },
      "POST /api/admin/skills": { status: 201, body: SKILL },
    });
    renderWithQuery(<App />, "/admin/skills");

    await screen.findByLabelText("Nombre");
    type("Nombre", "Python");
    fireEvent.change(screen.getByLabelText("Categoría"), { target: { value: "tool" } });
    type("Orden (el menor va primero)", "2");
    fireEvent.click(screen.getByRole("button", { name: "Agregar" }));

    await waitFor(() => {
      expect(screen.getByLabelText("Nombre")).toHaveValue("");
    });
    expect(sentBody(fetchMock, "POST", "/api/admin/skills")).toEqual({
      name: "Python",
      category: "tool",
      position: 2,
    });
  });

  it("edits and deletes an existing skill", async () => {
    const fetchMock = stubApi({
      "GET /api/admin/skills": { status: 200, body: [SKILL] },
      "PUT /api/admin/skills/7": { status: 200, body: SKILL },
      "DELETE /api/admin/skills/7": { status: 204 },
    });
    vi.stubGlobal("confirm", () => true);
    renderWithQuery(<App />, "/admin/skills");

    const row = (await screen.findByDisplayValue("Python")).closest("form") as HTMLElement;
    type("Nombre", "Python 3", within(row));
    fireEvent.click(within(row).getByRole("button", { name: "Guardar" }));
    expect(await within(row).findByRole("status")).toHaveTextContent("Guardado");
    fireEvent.click(within(row).getByRole("button", { name: "Borrar" }));

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        "/api/admin/skills/7",
        expect.objectContaining({ method: "DELETE" }),
      );
    });
    expect(sentBody(fetchMock, "PUT", "/api/admin/skills/7")).toEqual({
      name: "Python 3",
      category: "language",
      position: 0,
    });
  });

  it("doesn't delete if the confirmation is cancelled", async () => {
    const fetchMock = stubApi({ "GET /api/admin/skills": { status: 200, body: [SKILL] } });
    vi.stubGlobal("confirm", () => false);
    renderWithQuery(<App />, "/admin/skills");

    fireEvent.click(await screen.findByRole("button", { name: "Borrar" }));

    expect(fetchMock).not.toHaveBeenCalledWith(
      "/api/admin/skills/7",
      expect.objectContaining({ method: "DELETE" }),
    );
  });

  it("adds a current job (no end date) with the role in both languages", async () => {
    const fetchMock = stubApi({
      "GET /api/admin/experience": { status: 200, body: [] },
      "POST /api/admin/experience": { status: 201, body: JOB },
    });
    renderWithQuery(<App />, "/admin/experience");

    await screen.findByLabelText("Empresa");
    type("Empresa", "Acme");
    type("Cargo · Español", "Desarrollador");
    type("Cargo · English", "Developer");
    type("Descripción · Español", "Hice cosas");
    type("Inicio", "2024-01-01");
    fireEvent.click(screen.getByRole("button", { name: "Agregar" }));

    await waitFor(() => {
      expect(screen.getByLabelText("Empresa")).toHaveValue("");
    });
    expect(sentBody(fetchMock, "POST", "/api/admin/experience")).toEqual({
      company: "Acme",
      role_es: "Desarrollador",
      role_en: "Developer",
      description_es: "Hice cosas",
      description_en: "",
      start_date: "2024-01-01",
      end_date: null,
      position: 0,
    });
  });

  it("edits a job's end date and shows a notice if the API rejects it", async () => {
    const fetchMock = stubApi({
      "GET /api/admin/experience": { status: 200, body: [JOB] },
      "PUT /api/admin/experience/3": { status: 422 },
    });
    renderWithQuery(<App />, "/admin/experience");

    const card = (await screen.findByDisplayValue("Acme")).closest("form") as HTMLElement;
    type("Fin (vacío si es el trabajo actual)", "2023-01-01", within(card));
    fireEvent.click(within(card).getByRole("button", { name: "Guardar" }));

    expect(await within(card).findByRole("alert")).toHaveTextContent("Revisa los campos");
    expect(sentBody(fetchMock, "PUT", "/api/admin/experience/3")).toMatchObject({
      end_date: "2023-01-01",
    });
  });

  it("deletes a job after confirming", async () => {
    const fetchMock = stubApi({
      "GET /api/admin/experience": { status: 200, body: [JOB] },
      "DELETE /api/admin/experience/3": { status: 204 },
    });
    vi.stubGlobal("confirm", () => true);
    renderWithQuery(<App />, "/admin/experience");

    fireEvent.click(await screen.findByRole("button", { name: "Borrar" }));

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        "/api/admin/experience/3",
        expect.objectContaining({ method: "DELETE" }),
      );
    });
  });

  it.each(["/admin/skills", "/admin/experience"])(
    "if the %s list doesn't load, shows a notice",
    async (path) => {
      stubApi({ [`GET /api${path}`]: { status: 500 } });
      renderWithQuery(<App />, path);

      expect(await screen.findByRole("alert")).toHaveTextContent("No se pudo conectar");
    },
  );
});
