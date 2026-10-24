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

/** Fakes the admin panel API with a session: each route responds with what `routes` says. */
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

describe("admin panel: messages", () => {
  it("the admin panel home links to messages and visits", async () => {
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

  it("shows the message with its sender and source, and the HTML as text", async () => {
    stubApi({ messages: [MESSAGE] });
    renderWithQuery(<App />, "/admin/messages");

    const item = (await screen.findByRole("heading", { name: /Ana Prueba/ })).closest("article");
    expect(item).not.toBeNull();
    const article = within(item as HTMLElement);
    expect(article.getByText(/ana@example.com/)).toBeInTheDocument();
    expect(article.getByText(/portal \/ empresa-x · Nuevo/)).toBeInTheDocument();
    expect(article.getByText("Hola, <b>me interesa</b> tu perfil.")).toBeInTheDocument();
  });

  it("marking as read calls the API and updates the status", async () => {
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

  it("a message without UTM parameters shows as direct", async () => {
    stubApi({ messages: [{ ...MESSAGE, utm_source: null, utm_campaign: null, read: true }] });
    renderWithQuery(<App />, "/admin/messages");

    expect(await screen.findByText(/Directo · Leído/)).toBeInTheDocument();
  });

  it("says so when there are no messages", async () => {
    stubApi({ messages: [] });
    renderWithQuery(<App />, "/admin/messages");

    expect(await screen.findByText("Todavía no hay mensajes.")).toBeInTheDocument();
  });

  it("if the API fails, shows a notice", async () => {
    stubApi({ status: 500 });
    renderWithQuery(<App />, "/admin/messages");

    expect(await screen.findByRole("alert")).toHaveTextContent("No se pudo conectar");
  });
});

describe("admin panel: visits", () => {
  const VISITS: VisitCount[] = [
    { utm_source: "portal", utm_campaign: "empresa-x", visits: 3, unique_visitors: 2 },
    { utm_source: null, utm_campaign: null, visits: 1, unique_visitors: 1 },
  ];

  it("shows the counts by utm_source and utm_campaign", async () => {
    stubApi({ visits: VISITS });
    renderWithQuery(<App />, "/admin/visits");

    const rows = await screen.findAllByRole("row");
    expect(rows.map((row) => row.textContent)).toEqual([
      "Fuente (utm_source)Campaña (utm_campaign)VisitasVisitantes únicos por día",
      "portalempresa-x32",
      "Directo—11",
    ]);
  });

  it("says so when there are no visits", async () => {
    stubApi({ visits: [] });
    renderWithQuery(<App />, "/admin/visits");

    expect(await screen.findByText("Todavía no hay visitas.")).toBeInTheDocument();
  });

  it("if the API fails, shows a notice", async () => {
    stubApi({ status: 500 });
    renderWithQuery(<App />, "/admin/visits");

    expect(await screen.findByRole("alert")).toHaveTextContent("No se pudo conectar");
  });
});
