"""Punto de entrada de la API. El esqueleto completo llega en la tarea 1.2 del plan."""

from fastapi import FastAPI

app = FastAPI(title="API")


@app.get("/api/health")
def health() -> dict[str, str]:
    """Indica que la API está arriba. En la tarea 1.2 también consulta la base."""
    return {"status": "ok"}
