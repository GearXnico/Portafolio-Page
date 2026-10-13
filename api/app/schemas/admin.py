"""Admin panel login."""

from pydantic import BaseModel, ConfigDict, Field


class LoginIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(min_length=3, max_length=254)
    # Cap so nobody can make Argon2 work on a giant password.
    password: str = Field(min_length=1, max_length=256)


class SessionOut(BaseModel):
    status: str = "ok"
