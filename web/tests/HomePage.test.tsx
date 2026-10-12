import { screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { App } from "../src/App";
import { bootstrapFixture, stubBootstrap } from "./fixtures";
import { renderWithQuery } from "./render";

function renderPage() {
  return renderWithQuery(<App />);
}

describe("HomePage", () => {
  it("muestra perfil, proyectos, experiencia, habilidades y contacto en español", async () => {
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

  it("usa los textos en inglés cuando bootstrap decide inglés", async () => {
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

  it("agrupa las habilidades por categoría", async () => {
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

  it("sin contenido cargado muestra solo el título y el contacto, sin secciones vacías", async () => {
    stubBootstrap(bootstrapFixture({ profile: null, skills: [], experience: [], projects: [] }));

    renderPage();

    expect(await screen.findByRole("heading", { level: 1, name: "Producto" })).toBeInTheDocument();
    // El formulario de contacto no depende del contenido, así que es la única sección.
    const regions = screen.getAllByRole("region");
    expect(regions).toHaveLength(1);
    expect(regions[0]).toHaveAccessibleName("Contacto");
  });

  it("muestra el texto de un proyecto como texto, sin interpretar HTML", async () => {
    const projects = bootstrapFixture().projects.map((p) => ({
      ...p,
      title_es: '<img src=x onerror="alert(1)">',
    }));
    stubBootstrap(bootstrapFixture({ projects }));

    const { container } = renderPage();

    expect(await screen.findByText('<img src=x onerror="alert(1)">')).toBeInTheDocument();
    expect(container.querySelector("img")).toBeNull();
  });

  it("muestra un aviso si la API falla", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response("", { status: 500 })));

    renderPage();

    expect(await screen.findByRole("alert")).toHaveTextContent("No se pudo cargar el contenido");
  });
});
