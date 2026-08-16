"""Herramienta de diagnostico: que extrae el filtro de cada CV indexado.

No forma parte del pipeline. Existe para poder responder con un numero a la
pregunta "cuanto acierta el extractor", en vez de con una impresion. La
verificacion es manual: se imprime lo extraido junto al CV y se comprueba a
ojo, que con dieciocho candidatos es perfectamente viable.
"""

from __future__ import annotations

import sys
from pathlib import Path

from extract_text import extraer_carpeta, nombre_candidato
from requisitos import extraer_de_cv

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

TITULACION = {None: "-", 1: "FP", 2: "Grado", 3: "Master"}
MCER = {None: "-", 1: "A1", 2: "A2", 3: "B1", 4: "B2", 5: "C1", 6: "C2"}


def main() -> None:
    textos = extraer_carpeta()

    print(f"{'CANDIDATO':<26} {'ANIOS':>6} {'TITUL.':>8} {'INGLES':>7}")
    print("-" * 50)

    sin_anios = sin_titulacion = sin_ingles = 0
    for archivo, texto in sorted(textos.items()):
        perfil = extraer_de_cv(texto)
        nombre = nombre_candidato(archivo, texto)

        sin_anios += perfil.anios is None
        sin_titulacion += perfil.titulacion is None
        sin_ingles += perfil.ingles is None

        anios = "-" if perfil.anios is None else str(perfil.anios)
        print(f"{nombre[:26]:<26} {anios:>6} "
              f"{TITULACION[perfil.titulacion]:>8} {MCER[perfil.ingles]:>7}")

    total = len(textos)
    print("-" * 50)
    print(f"{total} CVs. Sin dato: anios {sin_anios}, "
          f"titulacion {sin_titulacion}, ingles {sin_ingles}.")
    print("\nUn '-' no es un fallo por si mismo: significa que el CV no declara")
    print("ese dato, y esos candidatos no se penalizan. Lo que hay que revisar")
    print("a ojo son las cifras que SI aparecen y son incorrectas.")


if __name__ == "__main__":
    main()
