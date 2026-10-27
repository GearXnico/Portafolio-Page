import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import type { PublicProfile } from "../src/api/bootstrap";
import { ProfileSection } from "../src/components/ProfileSection";
import { LangContext } from "../src/i18n";

// three.js needs WebGL, which jsdom doesn't have; the figure is replaced by a marker.
vi.mock("../src/components/Entity", () => ({
  default: () => <div data-testid="entity" />,
}));

const profile: PublicProfile = {
  headline_es: "Ana Pérez · Ingeniera backend",
  headline_en: "Ana Pérez · Backend engineer",
  about_es: "Construyo APIs.",
  about_en: "I build APIs.",
  links: { github: "https://github.com/ana", bad: "javascript:alert(1)" },
};

function renderHero(device: { reducedMotion?: boolean; wide?: boolean; webgl?: boolean } = {}) {
  const { reducedMotion = false, wide = true, webgl = true } = device;
  vi.stubGlobal(
    "matchMedia",
    (query: string) =>
      ({ matches: query.includes("reduce") ? reducedMotion : wide }) as MediaQueryList,
  );
  vi.spyOn(HTMLCanvasElement.prototype, "getContext").mockReturnValue(
    webgl ? ({} as RenderingContext) : null,
  );
  return render(
    <LangContext value={{ lang: "es", setLang: () => undefined }}>
      <ProfileSection profile={profile} />
    </LangContext>,
  );
}

describe("ProfileSection", () => {
  it("splits the headline into name and role and links only https profiles", () => {
    renderHero();

    expect(screen.getByRole("heading", { level: 1, name: "Ana Pérez" })).toBeInTheDocument();
    expect(screen.getByText("Ingeniera backend")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Abrir expedientes" })).toHaveAttribute(
      "href",
      "#projects",
    );
    expect(screen.getByRole("link", { name: "github" })).toHaveAttribute(
      "href",
      "https://github.com/ana",
    );
    expect(screen.queryByRole("link", { name: "bad" })).not.toBeInTheDocument();
  });

  it("opens with the case file lines and the surname in outline", () => {
    const { container } = renderHero();

    expect(container.querySelector(".boot")).toHaveTextContent(
      "> abriendo expediente: sujeto 01> ocupación: Ingeniera backend> estado: disponible para el próximo caso",
    );
    expect(container.querySelector("h1 .outline")).toHaveTextContent("Pérez");
  });

  it("loads the 3D figure on a wide screen with WebGL", async () => {
    renderHero();

    expect(await screen.findByTestId("entity")).toBeInTheDocument();
  });

  it.each([
    ["the device asks for reduced motion", { reducedMotion: true }],
    ["the screen is narrow", { wide: false }],
    ["there is no WebGL", { webgl: false }],
  ])("skips the 3D figure when %s", (_, device) => {
    renderHero(device);

    expect(screen.queryByTestId("entity")).not.toBeInTheDocument();
  });
});
