import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ApiStatus } from "../src/components/ApiStatus";

describe("ApiStatus", () => {
  it("muestra 'consultando…' mientras espera", () => {
    vi.stubGlobal("fetch", vi.fn().mockReturnValue(new Promise(() => undefined)));

    render(<ApiStatus />);

    expect(screen.getByTestId("api-status")).toHaveTextContent("consultando…");
  });

  it("muestra 'ok' si /api/health responde 200", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response("{}", { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);

    render(<ApiStatus />);

    expect(await screen.findByText("ok")).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith("/api/health", expect.anything());
  });

  it("muestra 'sin respuesta' si la API responde 503", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response("{}", { status: 503 })));

    render(<ApiStatus />);

    expect(await screen.findByText("sin respuesta")).toBeInTheDocument();
  });

  it("muestra 'sin respuesta' si la API no contesta", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("Failed to fetch")));

    render(<ApiStatus />);

    expect(await screen.findByText("sin respuesta")).toBeInTheDocument();
  });
});
