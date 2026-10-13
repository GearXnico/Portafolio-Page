import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { PublicProject } from "../src/api/bootstrap";
import { ProjectsSection } from "../src/components/ProjectsSection";
import { LangContext, type Lang } from "../src/i18n";
import { bootstrapFixture } from "./fixtures";

function project(overrides: Partial<PublicProject> = {}): PublicProject {
  const [base] = bootstrapFixture().projects;
  if (!base) throw new Error("the fixture has no projects");
  return { ...base, ...overrides };
}

function renderIn(lang: Lang, projects: PublicProject[]) {
  return render(
    <LangContext value={{ lang, setLang: () => undefined }}>
      <ProjectsSection projects={projects} />
    </LangContext>,
  );
}

const images = [
  { url: "/media/projects/a.webp", alt_es: "Portada", alt_en: "Cover" },
  { url: "/media/projects/b.webp", alt_es: "Otra", alt_en: "Other" },
];

describe("ProjectsSection", () => {
  it("shows the first screenshot as the cover, with the alt text for the language", () => {
    renderIn("en", [project({ images })]);

    const img = screen.getByRole("img");
    expect(img).toHaveAttribute("src", "/media/projects/a.webp");
    expect(img).toHaveAttribute("alt", "Cover");
  });

  it("in Spanish uses the Spanish alt text", () => {
    renderIn("es", [project({ images })]);

    expect(screen.getByRole("img")).toHaveAttribute("alt", "Portada");
  });

  it("shows the stack and the demo and repository links in a separate tab", () => {
    renderIn("es", [
      project({
        stack: ["React", "FastAPI"],
        demo_url: "https://demo.example.com",
        repo_url: "https://github.com/ejemplo/sitio",
      }),
    ]);

    const stack = screen.getByRole("list", { name: "Stack" });
    expect(
      within(stack)
        .getAllByRole("listitem")
        .map((li) => li.textContent),
    ).toEqual(["React", "FastAPI"]);
    const demo = screen.getByRole("link", { name: "Ver demo" });
    expect(demo).toHaveAttribute("href", "https://demo.example.com");
    expect(demo).toHaveAttribute("rel", "noopener noreferrer");
    expect(screen.getByRole("link", { name: "Código" })).toHaveAttribute(
      "href",
      "https://github.com/ejemplo/sitio",
    );
  });

  it("doesn't link URLs that aren't https", () => {
    renderIn("es", [project({ demo_url: "javascript:alert(1)", repo_url: "http://ejemplo.cl" })]);

    expect(screen.queryAllByRole("link")).toEqual([]);
  });

  it("without screenshots, stack or links shows only the title and summary", () => {
    renderIn("es", [project({ stack: [], images: [] })]);

    expect(screen.getByRole("heading", { name: "Este sitio" })).toBeInTheDocument();
    expect(screen.queryByRole("img")).toBeNull();
    expect(screen.queryByRole("list", { name: "Stack" })).toBeNull();
  });

  it("doesn't appear if there are no published projects", () => {
    const { container } = renderIn("es", []);

    expect(container).toBeEmptyDOMElement();
  });
});
