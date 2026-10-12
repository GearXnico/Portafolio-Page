"""Configuración de la API, leída de variables de entorno."""

from pydantic import SecretStr
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

    # IP (dirección de red) de los proxies de confianza, separadas por coma; acepta redes
    # (172.18.0.0/16). Solo de ellos se lee X-Forwarded-For para saber la IP real del
    # visitante. Vacío: se usa la IP de la conexión, y nadie puede falsearla con ese header.
    trusted_proxies: str = ""

    # Aviso por correo de cada mensaje de contacto (ADR 0005). Si falta alguno, el mensaje
    # igual se guarda y solo se anota en el log que el correo está desactivado.
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: SecretStr | None = None
    contact_notify_to: str | None = None


settings = Settings()
