"""Configuración de la API, leída de variables de entorno."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Busca un .env en la carpeta actual o en la raíz del repo (si corres desde api/).
    # Las variables de entorno tienen prioridad sobre el archivo.
    model_config = SettingsConfigDict(env_file=(".env", "../.env"), extra="ignore")

    # Usuario de la API, con permisos mínimos: solo lee y escribe filas.
    database_url: str
    # Dueño de las tablas: solo lo usa Alembic. Es opcional para que en producción
    # el proceso de la API pueda arrancar sin conocer la clave del dueño.
    migration_database_url: str | None = None


settings = Settings()
