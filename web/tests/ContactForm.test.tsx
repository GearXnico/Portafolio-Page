import { fireEvent, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ContactForm } from "../src/components/ContactForm";
import { LangContext, type Lang } from "../src/i18n";
import { renderWithQuery } from "./render";

function renderForm(lang: Lang = "es") {
  return renderWithQuery(
    <LangContext value={{ lang, setLang: () => undefined }}>
      <ContactForm />
    </LangContext>,
  );
}

function stubContact(response: Response | Error) {
  const fetchMock = vi.fn<(url: string, init: RequestInit) => Promise<Response>>(() =>
    response instanceof Error ? Promise.reject(response) : Promise.resolve(response),
  );
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

function fillAndSubmit() {
  fireEvent.change(screen.getByLabelText("Nombre"), { target: { value: "Ana" } });
  fireEvent.change(screen.getByLabelText("Correo"), { target: { value: "ana@example.com" } });
  fireEvent.change(screen.getByLabelText("Mensaje"), { target: { value: "Hola" } });
  fireEvent.click(screen.getByRole("button", { name: "Enviar" }));
}

describe("ContactForm", () => {
  afterEach(() => {
    window.history.replaceState(null, "", "/");
  });

  it("sends the fields, the language and the empty honeypot field, and confirms it arrived", async () => {
    const fetchMock = stubContact(new Response('{"status":"ok"}', { status: 201 }));
    renderForm();

    fillAndSubmit();

    expect(await screen.findByText(/Tu mensaje llegó/)).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith("/api/contact", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: "Ana",
        email: "ana@example.com",
        message: "Hola",
        website: "",
        lang: "es",
      }),
    });
    expect(screen.getByLabelText("Mensaje")).toHaveValue("");
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it.each([
    ["invalid data (422)", new Response("{}", { status: 422 }), /Revisa los datos/],
    ["submission limit (429)", new Response("{}", { status: 429 }), /varios mensajes seguidos/],
    ["server error (500)", new Response("{}", { status: 500 }), /No se pudo enviar/],
    ["no connection", new TypeError("Failed to fetch"), /No se pudo enviar/],
  ])("with %s shows the error and keeps what was typed", async (_caso, response, text) => {
    stubContact(response);
    renderForm();

    fillAndSubmit();

    expect(await screen.findByRole("alert")).toHaveTextContent(text);
    expect(screen.getByLabelText("Mensaje")).toHaveValue("Hola");
  });

  it("the honeypot field is out of focus order and hidden from screen readers", () => {
    renderForm();

    const trap = document.querySelector<HTMLInputElement>('input[name="hp_field"]');
    expect(trap).toHaveAttribute("tabindex", "-1");
    expect(trap?.closest('[aria-hidden="true"]')).not.toBeNull();
  });

  it("if the honeypot field is filled, sends it as website so the API (application programming interface) discards it", async () => {
    const fetchMock = stubContact(new Response("{}", { status: 201 }));
    renderForm();

    const trap = document.querySelector<HTMLInputElement>('input[name="hp_field"]');
    if (!trap) throw new Error("honeypot field missing");
    fireEvent.change(trap, { target: { value: "https://spam.example.com" } });
    fillAndSubmit();

    await screen.findByText(/Tu mensaje llegó/);
    expect(fetchMock.mock.calls[0]?.[1].body).toContain('"website":"https://spam.example.com"');
  });

  it("uses the English texts and sends lang en", async () => {
    const fetchMock = stubContact(new Response("{}", { status: 201 }));
    renderForm("en");

    fireEvent.change(screen.getByLabelText("Name"), { target: { value: "Ann" } });
    fireEvent.change(screen.getByLabelText("Email"), { target: { value: "ann@example.com" } });
    fireEvent.change(screen.getByLabelText("Message"), { target: { value: "Hi" } });
    fireEvent.click(screen.getByRole("button", { name: "Send" }));

    expect(await screen.findByText(/Your message arrived/)).toBeInTheDocument();
    expect(fetchMock.mock.calls[0]?.[1]?.body).toContain('"lang":"en"');
  });

  it("sends utm_source and utm_campaign from the URL, and not the UTM (Urchin Tracking Module) parameters the API doesn't store", async () => {
    window.history.replaceState(
      null,
      "",
      "/?utm_source=linkedin&utm_medium=social&utm_campaign=postulacion",
    );
    const fetchMock = stubContact(new Response("{}", { status: 201 }));
    renderForm();

    fillAndSubmit();

    await screen.findByText(/Tu mensaje llegó/);
    const body = JSON.parse(fetchMock.mock.calls[0]?.[1].body as string) as Record<string, string>;
    expect(body).toMatchObject({ utm_source: "linkedin", utm_campaign: "postulacion" });
    expect(body).not.toHaveProperty("utm_medium");
  });
});
