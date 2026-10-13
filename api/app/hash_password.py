"""Generate the Argon2 hash of the administrator's password.

Usage: `python -m app.hash_password`. Asks for the password without echoing it and prints the
line for `.env`, in single quotes so Docker Compose doesn't interpret the `$` in the hash.
"""

import getpass
import sys

from app.services.auth import hash_password

MIN_LENGTH = 12
MAX_LENGTH = 256  # The same cap the login accepts.


def main() -> int:
    password = getpass.getpass("Administrator password: ")
    if not MIN_LENGTH <= len(password) <= MAX_LENGTH:
        print(f"Use between {MIN_LENGTH} and {MAX_LENGTH} characters.", file=sys.stderr)
        return 1
    if getpass.getpass("Repeat it: ") != password:
        print("The passwords don't match.", file=sys.stderr)
        return 1
    print(f"ADMIN_PASSWORD_HASH='{hash_password(password)}'")
    return 0


if __name__ == "__main__":
    sys.exit(main())
