import { fireEvent, screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import type { ContactMessage, VisitCount } from "../src/api/activity";
import { App } from "../src/App";
import { renderWithQuery } from "./render";

const MESSAGE: ContactMessage = {
  id: 7,
  created_at: "2026-10-12T15:30:00Z",
  name: "Ana Prueba",
  email: "ana@example.com",
  message: "Hola, <b>me interesa</b> tu perfil.",
  lang: "es",
  utm_source: "portal",
  utm_campaign: "empresa-x",
  read: false,
};

/** Simula la API del panel con sesión: cada ruta responde lo que indica `routes`. */
function stubApi(routes: { messages?: unknown; visits?: unknown; status?: number }) {
  let messages = routes.messages;
  const fetchMock = vi.fn((input: string, init?: RequestInit) => {
    const json = (body: unknown, status = 200) =>
      Promise.resolve(new Response(JSON.stringify(body), { status }));
    if (input === "/api/admin/session") return json({ status: "ok" });
    if (routes.status) return json({}, routes.status);
    if (input === "/api/admin/visits") return json(routes.visits);
    if (input === "/api/admin/messages") return json(messages);
    if (init?.method === "PATCH") {
      const { read } = JSON.parse(init.body as string) as { read: boolean };
      messages = [{ ...MESSAGE, read }];
      return json(messages);
    }
    return json({}, 404);
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

describe("panel: mensajes", () => {
  it("el inicio del panel enlaza a mensajes y visitas", async () => {
    stubApi({});
    renderWithQuery(<App />, "/admin");

    expect(await screen.findByRole("link", { name: "Mensajes" })).toHaveAttribute(
      "href",
      "/admin/messages",
    );
    expect(screen.getByRole("link", { name: "Visitas por enlace" })).toHaveAttribute(
      "href",
      "/admin/visits",
    );
  });

  it("muestra el mensaje con su remitente y origen, y el HTML como texto", async () => {
    stubApi({ messages: [MESSAGE] });
    renderWithQuery(<App />, "/admin/messages");

    const item = (await screen.findByRole("heading", { name: /Ana Prueba/ })).closest("article");
    expect(item).not.toBeNull();
    const article = within(item as HTMLElement);
    expect(article.getByText(/ana@example.com/)).toBeInTheDocument();
    expect(article.getByText(/portal \/ empresa-x · Nuevo/)).toBeInTheDocument();
    expect(article.getByText("Hola, <b>me interesa</b> tu perfil.")).toBeInTheDocument();
  });

  it("marcar como leído llama a la API y actualiza el estado", async () => {
    const fetchMock = stubApi({ messages: [MESSAGE] });
    renderWithQuery(<App />, "/admin/messages");

    fireEvent.click(await screen.findByRole("button", { name: "Marcar como leído" }));

    expect(await screen.findByRole("button", { name: "Marcar como no leído" })).toBeInTheDocument();
    expect(screen.getByText(/· Leído/)).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/admin/messages/7",
      expect.objectContaining({ method: "PATCH", body: JSON.stringify({ read: true }) }),
    );
  });

  it("un mensaje sin UTM aparece como directo", async () => {
    stubApi({ messages: [{ ...MESSAGE, utm_source: null, utm_campaign: null, read: true }] });
    renderWithQuery(<App />, "/admin/messages");

    expect(await screen.findByText(/Directo · Leído/)).toBeInTheDocument();
  });

  it("sin mensajes lo dice", async () => {
    stubApi({ messages: [] });
    renderWithQuery(<App />, "/admin/messages");

    expect(await screen.findByText("Todavía no hay mensajes.")).toBeInTheDocument();
  });

  it("si la API falla, avisa", async () => {
    stubApi({ status: 500 });
    renderWithQuery(<App />, "/admin/messages");

    expect(await screen.findByRole("alert")).toHaveTextContent("No se pudo conectar");
  });
});

describe("panel: visitas", () => {
  const VISITS: VisitCount[] = [
    { utm_source: "portal", utm_campaign: "empresa-x", visits: 3, unique_visitors: 2 },
    { utm_source: null, utm_campaign: null, visits: 1, unique_visitors: 1 },
  ];

  it("muestra los conteos por utm_source y utm_campaign", async () => {
    stubApi({ visits: VISITS });
    renderWithQuery(<App />, "/admin/visits");

    const rows = await screen.findAllByRole("row");
    expect(rows.map((row) => row.textContent)).toEqual([
      "Fuente (utm_source)Campaña (utm_campaign)VisitasVisitantes únicos por día",
      "portalempresa-x32",
      "Directo—11",
    ]);
  });

  it("sin visitas lo dice", async () => {
    stubApi({ visits: [] });
    renderWithQuery(<App />, "/admin/visits");

    expect(await screen.findByText("Todavía no hay visitas.")).toBeInTheDocument();
  });

  it("si la API falla, avisa", async () => {
    stubApi({ status: 500 });
    renderWithQuery(<App />, "/admin/visits");

    expect(await screen.findByRole("alert")).toHaveTextContent("No se pudo conectar");
  });
});
