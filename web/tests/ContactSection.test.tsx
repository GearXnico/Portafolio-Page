import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ContactSection } from "../src/components/ContactSection";

describe("ContactSection", () => {
  it("muestra solo los enlaces https y los abre aparte sin dar acceso a la página", () => {
    render(
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

  it("no aparece si no hay enlaces válidos", () => {
    const { container } = render(<ContactSection links={{ x: "ftp://a" }} />);

    expect(container).toBeEmptyDOMElement();
  });
});
