import { fireEvent, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

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
  it("envía los campos, el idioma y el campo trampa vacío, y avisa que llegó", async () => {
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
    ["datos inválidos (422)", new Response("{}", { status: 422 }), /Revisa los datos/],
    ["límite de envíos (429)", new Response("{}", { status: 429 }), /varios mensajes seguidos/],
    ["error del servidor (500)", new Response("{}", { status: 500 }), /No se pudo enviar/],
    ["sin conexión", new TypeError("Failed to fetch"), /No se pudo enviar/],
  ])("con %s muestra el error y conserva lo escrito", async (_caso, response, text) => {
    stubContact(response);
    renderForm();

    fillAndSubmit();

    expect(await screen.findByRole("alert")).toHaveTextContent(text);
    expect(screen.getByLabelText("Mensaje")).toHaveValue("Hola");
  });

  it("el campo trampa queda fuera del foco y de los lectores de pantalla", () => {
    renderForm();

    const trap = document.querySelector<HTMLInputElement>('input[name="hp_field"]');
    expect(trap).toHaveAttribute("tabindex", "-1");
    expect(trap?.closest('[aria-hidden="true"]')).not.toBeNull();
  });

  it("si el campo trampa viene lleno, lo envía como website para que la API lo descarte", async () => {
    const fetchMock = stubContact(new Response("{}", { status: 201 }));
    renderForm();

    const trap = document.querySelector<HTMLInputElement>('input[name="hp_field"]');
    if (!trap) throw new Error("falta el campo trampa");
    fireEvent.change(trap, { target: { value: "https://spam.example.com" } });
    fillAndSubmit();

    await screen.findByText(/Tu mensaje llegó/);
    expect(fetchMock.mock.calls[0]?.[1].body).toContain('"website":"https://spam.example.com"');
  });

  it("usa los textos en inglés y envía lang en", async () => {
    const fetchMock = stubContact(new Response("{}", { status: 201 }));
    renderForm("en");

    fireEvent.change(screen.getByLabelText("Name"), { target: { value: "Ann" } });
    fireEvent.change(screen.getByLabelText("Email"), { target: { value: "ann@example.com" } });
    fireEvent.change(screen.getByLabelText("Message"), { target: { value: "Hi" } });
    fireEvent.click(screen.getByRole("button", { name: "Send" }));

    expect(await screen.findByText(/Your message arrived/)).toBeInTheDocument();
    expect(fetchMock.mock.calls[0]?.[1]?.body).toContain('"lang":"en"');
  });
});
