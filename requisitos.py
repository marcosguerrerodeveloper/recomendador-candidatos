"""Extraccion de requisitos duros de una oferta y del perfil de un candidato.

Este modulo convierte texto libre en datos comparables: anios de experiencia,
nivel de titulacion y nivel de ingles. No sabe nada de MySQL, de embeddings ni
de la interfaz, y por eso se puede probar entero con cadenas de texto.

Existe porque la similitud coseno mide DE QUE VA un CV, no SI EL CANDIDATO
SIRVE: en el espacio semantico "un anio de experiencia" y "ocho anios" son
practicamente el mismo vector. La cantidad hay que leerla aparte.
"""

from __future__ import annotations

import re
import unicodedata

# ---------------------------------------------------------------------------
# Segmentacion
# ---------------------------------------------------------------------------

# Cabeceras de CV, normalizadas sin tildes y en minusculas. El valor es la
# clave canonica: varias cabeceras distintas caen en la misma seccion.
_CABECERAS_CV: dict[str, str] = {
    "perfil": "perfil",
    "profile": "perfil",
    "resumen": "perfil",
    "experiencia": "experiencia",
    "experiencia laboral": "experiencia",
    "experiencia profesional": "experiencia",
    "experience": "experiencia",
    "work experience": "experiencia",
    "formacion": "formacion",
    "formacion academica": "formacion",
    "education": "formacion",
    "idiomas": "idiomas",
    "languages": "idiomas",
}

# Cabeceras de oferta. Aqui la distincion critica es requisito EXIGIDO frente a
# merito VALORADO: la oferta data_engineer pone "Ingles B2 o superior" bajo
# "Se valorara", y tratarlo como obligatorio penalizaria a candidatos validos.
_CABECERAS_OFERTA: dict[str, str] = {
    "requisitos": "requisitos",
    "requisitos minimos": "requisitos",
    "que buscamos": "requisitos",
    "lo que buscamos": "requisitos",
    "requirements": "requisitos",
    "what we are looking for": "requisitos",
    "se valorara": "valorado",
    "se valoraran": "valorado",
    "valorable": "valorado",
    "nice to have": "valorado",
    "bonus": "valorado",
}


def _normalizar(texto: str) -> str:
    """Minusculas y sin tildes, para comparar cabeceras sin depender del acento."""
    sin_tildes = unicodedata.normalize("NFKD", texto)
    sin_tildes = "".join(c for c in sin_tildes if not unicodedata.combining(c))
    return sin_tildes.lower().strip()


def _es_cabecera_cv(linea: str) -> bool:
    """Una cabecera de CV es una linea corta, en mayusculas y sin puntuacion.

    Las tres condiciones extra (no acabar en punto, no llevar digitos, no llevar
    parentesis) descartan falsas cabeceras que existen de verdad en los CVs del
    repositorio: 'ITC (2018-2019).' y 'MVC.' van en mayusculas porque son siglas
    dentro de una frase, y tomarlas por cabecera parte la seccion de experiencia
    por la mitad y se pierden rangos de fechas.
    """
    limpia = linea.strip()
    if not limpia or len(limpia) > 40:
        return False
    if limpia.endswith(".") or any(c.isdigit() for c in limpia) or "(" in limpia:
        return False
    if limpia != limpia.upper():
        return False
    return bool(re.search(r"[A-ZÁÉÍÓÚÑ]{3}", limpia))


def _segmentar(texto: str, cabeceras: dict[str, str], es_cabecera) -> dict[str, str]:
    """Reparte las lineas del texto entre secciones canonicas.

    Todo lo que no cae bajo una cabecera reconocida va a 'otros', que siempre
    existe. Las secciones que no aparecen quedan como cadena vacia y no como
    None: quien consume esto hace 'in' sobre el resultado, y una cadena vacia
    responde correctamente a esa pregunta sin obligar a comprobar el tipo.
    """
    canonicas = set(cabeceras.values()) | {"otros"}
    partes: dict[str, list[str]] = {clave: [] for clave in canonicas}

    actual = "otros"
    for linea in texto.split("\n"):
        if es_cabecera(linea):
            clave = cabeceras.get(_normalizar(linea).rstrip(":"))
            if clave is not None:
                actual = clave
                continue
            # Cabecera con forma valida pero titulo no reconocido ("LOGROS",
            # "Que ofrecemos"): cierra la seccion anterior y manda a 'otros'.
            actual = "otros"
            continue
        partes[actual].append(linea)

    return {clave: "\n".join(lineas).strip() for clave, lineas in partes.items()}


def secciones_cv(texto: str) -> dict[str, str]:
    """Parte un CV en perfil / experiencia / formacion / idiomas / otros."""
    return _segmentar(texto, _CABECERAS_CV, _es_cabecera_cv)


def _es_cabecera_oferta(linea: str) -> bool:
    """En una oferta las cabeceras no van en mayusculas, asi que se reconocen
    por el titulo: linea corta, sin vinetas, cuyo texto esta en la lista.

    Es mas estricto a proposito que en el CV. Una oferta es prosa, y cualquier
    heuristica de forma (linea corta, acaba en dos puntos) se traga frases
    sueltas del cuerpo.
    """
    limpia = linea.strip()
    if not limpia or len(limpia) > 60 or limpia.startswith(("-", "*", "•")):
        return False
    return _normalizar(limpia).rstrip(":") in _CABECERAS_OFERTA


def secciones_oferta(texto: str) -> dict[str, str]:
    """Parte una oferta en requisitos / valorado / otros."""
    return _segmentar(texto, _CABECERAS_OFERTA, _es_cabecera_oferta)
