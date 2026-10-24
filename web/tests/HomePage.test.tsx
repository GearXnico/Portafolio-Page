import { fireEvent, screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { App } from "../src/App";
import { bootstrapFixture, stubBootstrap } from "./fixtures";
import { renderWithQuery } from "./render";

function renderPage() {
  return renderWithQuery(<App />);
}

describe("HomePage", () => {
  it("shows profile, projects, experience, skills and contact in Spanish", async () => {
    stubBootstrap(bootstrapFixture());

    renderPage();

    expect(
      await screen.findByRole("heading", { level: 1, name: "Desarrollador full stack" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Construyo productos web.")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Este sitio" })).toBeInTheDocument();
    expect(screen.getByText("Portafolio con CI")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Desarrollador · Acme" })).toBeInTheDocument();
    expect(screen.getByText(/actualidad/)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "github" })).toHaveAttribute(
      "href",
      "https://github.com/ejemplo",
    );
    expect(document.documentElement.lang).toBe("es");
  });

  it("uses the English texts when bootstrap picks English", async () => {
    stubBootstrap(bootstrapFixture({ lang: "en" }));

    renderPage();

    expect(
      await screen.findByRole("heading", { level: 1, name: "Full stack developer" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Projects" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "This site" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Developer · Acme" })).toBeInTheDocument();
    expect(screen.getByText(/present/)).toBeInTheDocument();
    expect(screen.queryByText("Este sitio")).not.toBeInTheDocument();
    expect(document.documentElement.lang).toBe("en");
  });

  it("groups skills by category", async () => {
    stubBootstrap(bootstrapFixture());

    renderPage();

    const skills = await screen.findByRole("region", { name: "Habilidades" });
    const backend = within(skills).getByText("Lenguajes").parentElement as HTMLElement;
    expect(
      within(backend)
        .getAllByRole("listitem")
        .map((li) => li.textContent),
    ).toEqual(["Python", "TypeScript"]);
  });

  it("with no content loaded shows only the title and contact, without empty sections", async () => {
    stubBootstrap(bootstrapFixture({ profile: null, skills: [], experience: [], projects: [] }));

    renderPage();

    expect(await screen.findByRole("heading", { level: 1, name: "Producto" })).toBeInTheDocument();
    // The contact form doesn't depend on the content, so it is the only section.
    const regions = screen.getAllByRole("region");
    expect(regions).toHaveLength(1);
    expect(regions[0]).toHaveAccessibleName("Contacto");
  });

  it("shows a project's text as text, without interpreting HTML", async () => {
    const projects = bootstrapFixture().projects.map((p) => ({
      ...p,
      title_es: '<img src=x onerror="alert(1)">',
    }));
    stubBootstrap(bootstrapFixture({ projects }));

    const { container } = renderPage();

    expect(await screen.findByText('<img src=x onerror="alert(1)">')).toBeInTheDocument();
    expect(container.querySelector("img")).toBeNull();
  });

  it("shows a notice if the API fails", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response("", { status: 500 })));

    renderPage();

    expect(await screen.findByRole("alert")).toHaveTextContent("No se pudo cargar el contenido");
  });

  it("sets the document title and description by language", async () => {
    stubBootstrap(bootstrapFixture());

    renderPage();
    await screen.findByRole("heading", { level: 1, name: "Desarrollador full stack" });

    const description = () =>
      document.querySelector('meta[name="description"]')?.getAttribute("content");
    expect(document.title).toBe("Desarrollador full stack · Portafolio");
    expect(description()).toMatch(/^Portafolio:/);

    fireEvent.click(screen.getByRole("button", { name: "English" }));

    expect(document.title).toBe("Full stack developer · Portfolio");
    expect(description()).toMatch(/^Portfolio:/);
  });
});
