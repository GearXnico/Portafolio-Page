import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ContactSection } from "../src/components/ContactSection";
import { renderWithQuery } from "./render";

describe("ContactSection", () => {
  it("shows only https links and opens them separately without giving access to the page", () => {
    renderWithQuery(
      <ContactSection
        links={{
          github: "https://github.com/ejemplo",
          malo: "javascript:alert(1)",
          inseguro: "http://ejemplo.cl",
          roto: "no es una url",
        }}
      />,
    );

    const links = screen.getAllByRole("link");
    expect(links).toHaveLength(1);
    expect(links[0]).toHaveAttribute("href", "https://github.com/ejemplo");
    expect(links[0]).toHaveAttribute("rel", "noopener noreferrer");
  });

  it("without valid links shows only the form", () => {
    renderWithQuery(<ContactSection links={{ x: "ftp://a" }} />);

    expect(screen.queryByRole("list")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Enviar" })).toBeInTheDocument();
  });
});
