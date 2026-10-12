"""Login del panel de administración."""

from pydantic import BaseModel, ConfigDict, Field


class LoginIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(min_length=3, max_length=254)
    # Tope para que nadie haga trabajar a Argon2 con una contraseña gigante.
    password: str = Field(min_length=1, max_length=256)


class SessionOut(BaseModel):
    status: str = "ok"
