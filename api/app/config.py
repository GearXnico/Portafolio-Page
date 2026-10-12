"""Configuración de la API, leída de variables de entorno."""

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Busca un .env en la carpeta actual o en la raíz del repo (si corres desde api/).
    # Las variables de entorno tienen prioridad sobre el archivo.
    # Una variable vacía (ADMIN_EMAIL=) cuenta como no definida y toma el valor por defecto.
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"), extra="ignore", env_ignore_empty=True
    )

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

    # Administrador único (ADR 0004). Si falta alguno, el login responde 503 y el panel no
    # se puede usar. El hash se genera con `python -m app.hash_password`.
    admin_email: str | None = None
    admin_password_hash: SecretStr | None = None
    # Firma la cookie de sesión (JWT). Al menos 32 caracteres al azar; cambiarla cierra todas
    # las sesiones abiertas.
    jwt_secret: SecretStr | None = Field(default=None, min_length=32)


settings = Settings()
