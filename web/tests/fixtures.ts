import { vi } from "vitest";

import type { Bootstrap, PublicProject } from "../src/api/bootstrap";

/** A `bootstrap` response with a bit of everything, in both languages. */
export function bootstrapFixture(overrides: Partial<Bootstrap> = {}): Bootstrap {
  return {
    lang: "es",
    profile: {
      headline_es: "Desarrollador full stack",
      headline_en: "Full stack developer",
      about_es: "Construyo productos web.",
      about_en: "I build web products.",
      links: { github: "https://github.com/ejemplo" },
      palette: null,
    },
    skills: [
      { name: "Python", category: "language" },
      { name: "React", category: "framework" },
      { name: "TypeScript", category: "language" },
    ],
    experience: [
      {
        company: "Acme",
        role_es: "Desarrollador",
        role_en: "Developer",
        description_es: "Hice cosas.",
        description_en: "I did things.",
        start_date: "2023-03-01",
        end_date: null,
      },
    ],
    projects: [
      {
        slug: "sitio",
        title_es: "Este sitio",
        title_en: "This site",
        summary_es: "Portafolio con CI",
        summary_en: "Portfolio with CI",
        body_es: "",
        body_en: "",
        stack: ["React"],
        demo_url: null,
        repo_url: null,
        status: null,
        images: [],
      },
    ],
    ...overrides,
  };
}

export function projectFixture(overrides: Partial<PublicProject> = {}): PublicProject {
  const [base] = bootstrapFixture().projects;
  if (!base) throw new Error("the fixture has no projects");
  return { ...base, ...overrides };
}

export function stubBootstrap(body: Bootstrap) {
  const fetchMock = vi.fn().mockResolvedValue(Response.json(body));
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}
