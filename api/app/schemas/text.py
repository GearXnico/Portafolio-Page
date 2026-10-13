"""Text validators shared by the schemas that receive user data.

They reject control characters: Postgres doesn't accept the null byte (it would be a 500) and
the others have no place in a text shown on the page or sent in an email.
"""

import re

# Control characters (C0, DEL and C1) and the Unicode line separators.
_CONTROL = re.compile("[\x00-\x1f\x7f-\x9f  ]")
# Line breaks and tabs are allowed in long texts.
_CONTROL_MULTILINE = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f  ]")


def single_line(value: str) -> str:
    if _CONTROL.search(value):
        raise ValueError("can't contain line breaks or control characters")
    return value


def multiline(value: str) -> str:
    if _CONTROL_MULTILINE.search(value):
        raise ValueError("can't contain control characters")
    return value
