"""Compara el ranking con filtro de requisitos y sin el, sobre las seis ofertas.

No forma parte del pipeline. Produce la tabla que sustenta las cifras del
README, para que esas cifras se puedan reproducir en vez de tener que creerlas.

El criterio de calidad es el mismo de la sesion anterior: donde caen los dos
controles negativos (la tecnica de RRHH y el contable senior), que deberian
hundirse frente a cualquier oferta tecnica. Un sistema que los sube esta peor,
por muy bien que acierte al ganador.
"""

from __future__ import annotations

import sys
from pathlib import Path

from match import rankear_detallado
from requisitos import extraer_de_oferta

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CONTROLES = ("Beatriz", "Javier")


def posicion_de_controles(ranking: list[dict], clave: str) -> list[int]:
    ordenado = sorted(ranking, key=lambda f: f[clave], reverse=True)
    return [
        posicion
        for posicion, fila in enumerate(ordenado, start=1)
        if fila["nombre"].split()[0] in CONTROLES
    ]


def main() -> None:
    ofertas = sorted(Path("ofertas").glob("*.txt"))

    print(f"{'OFERTA':<30} {'REQUISITOS':<18} {'GANADOR':<22} {'CONTROLES sin/con':>18}")
    print("-" * 92)

    total_sin = total_con = 0
    for ruta in ofertas:
        texto = ruta.read_text(encoding="utf-8")
        ranking = rankear_detallado(texto, titulo=ruta.stem, guardar=False)
        if not ranking:
            print("No hay candidatos indexados. Ejecuta antes embed_and_store.py.")
            return

        req = extraer_de_oferta(texto)
        pide = []
        if req.anios is not None:
            pide.append(f"{req.anios}a")
        if req.titulacion is not None:
            pide.append({1: "FP", 2: "Grado", 3: "Master"}[req.titulacion])
        if req.ingles is not None:
            pide.append({1: "A1", 2: "A2", 3: "B1", 4: "B2", 5: "C1", 6: "C2"}[req.ingles])

        sin = posicion_de_controles(ranking, "score")
        con = posicion_de_controles(ranking, "score_ajustado")
        total_sin += sum(sin)
        total_con += sum(con)

        ganador = max(ranking, key=lambda f: f["score_ajustado"])["nombre"]
        antes = max(ranking, key=lambda f: f["score"])["nombre"]
        marca = "" if ganador == antes else f"  (antes: {antes.split(' - ')[0]})"

        print(f"{ruta.stem:<30} {(','.join(pide) or '-'):<18} "
              f"{ganador.split(' - ')[0][:22]:<22} {str(sin):>8}/{str(con):<8}{marca}")

    print("-" * 92)
    n = len(ofertas) * 2
    print(f"Posicion media de los controles:  sin filtro {total_sin / n:.2f}   "
          f"con filtro {total_con / n:.2f}   (de 18)")
    print("Cuanto MAS ALTA esa cifra, mejor: significa que estan mas al fondo.")


if __name__ == "__main__":
    main()
