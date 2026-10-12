"""Validadores de texto compartidos por los esquemas que reciben datos del usuario.

Rechazan caracteres de control: Postgres no acepta el byte nulo (sería un 500) y los demás
no tienen nada que hacer en un texto que se muestra en la página o va en un correo.
"""

import re

# Caracteres de control (C0, DEL y C1) y los separadores de línea de Unicode.
_CONTROL = re.compile("[\x00-\x1f\x7f-\x9f  ]")
# En los textos largos se permiten saltos de línea y tabulaciones.
_CONTROL_MULTILINE = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f  ]")


def single_line(value: str) -> str:
    if _CONTROL.search(value):
        raise ValueError("no puede tener saltos de línea ni caracteres de control")
    return value


def multiline(value: str) -> str:
    if _CONTROL_MULTILINE.search(value):
        raise ValueError("no puede tener caracteres de control")
    return value
