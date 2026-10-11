"""Configuración de la API, leída de variables de entorno."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Busca un .env en la carpeta actual o en la raíz del repo (si corres desde api/).
    # Las variables de entorno tienen prioridad sobre el archivo.
    model_config = SettingsConfigDict(env_file=(".env", "../.env"), extra="ignore")

    database_url: str


settings = Settings()
