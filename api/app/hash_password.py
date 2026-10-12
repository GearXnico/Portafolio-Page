"""Genera el hash Argon2 de la contraseña del administrador.

Uso: `python -m app.hash_password`. Pide la contraseña sin mostrarla y escribe la línea para
el `.env`, entre comillas simples para que Docker Compose no interprete los `$` del hash.
"""

import getpass
import sys

from app.services.auth import hash_password

MIN_LENGTH = 12
MAX_LENGTH = 256  # El mismo tope que acepta el login.


def main() -> int:
    password = getpass.getpass("Contraseña del administrador: ")
    if not MIN_LENGTH <= len(password) <= MAX_LENGTH:
        print(f"Usa entre {MIN_LENGTH} y {MAX_LENGTH} caracteres.", file=sys.stderr)
        return 1
    if getpass.getpass("Repítela: ") != password:
        print("Las contraseñas no coinciden.", file=sys.stderr)
        return 1
    print(f"ADMIN_PASSWORD_HASH='{hash_password(password)}'")
    return 0


if __name__ == "__main__":
    sys.exit(main())
