"""Punto de entrada de la API."""

from fastapi import FastAPI

from app.routers import health

app = FastAPI(title="API")
app.include_router(health.router)
