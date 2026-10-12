import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { App } from "../src/App";

describe("App", () => {
  it("muestra el título y el estado de la API", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response("{}", { status: 200 })));

    render(<App />);

    expect(screen.getByRole("heading", { name: "Producto" })).toBeInTheDocument();
    expect(await screen.findByText("ok")).toBeInTheDocument();
  });
});
