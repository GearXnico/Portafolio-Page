"""Punto de entrada de la API."""

from fastapi import FastAPI

from app.routers import bootstrap, health

app = FastAPI(title="API")
app.include_router(health.router)
app.include_router(bootstrap.router)
