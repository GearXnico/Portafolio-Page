"""Configuración de la API, leída de variables de entorno."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Busca un .env en la carpeta actual o en la raíz del repo (si corres desde api/).
    # Las variables de entorno tienen prioridad sobre el archivo.
    model_config = SettingsConfigDict(env_file=(".env", "../.env"), extra="ignore")

    # Usuario de la API, con permisos mínimos: solo lee y escribe filas.
    database_url: str
    # Dueño de las tablas: solo lo usa Alembic para las migraciones.
    migration_database_url: str


settings = Settings()
