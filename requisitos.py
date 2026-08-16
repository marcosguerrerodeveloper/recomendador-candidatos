"""Extraccion de requisitos duros de una oferta y del perfil de un candidato.

Este modulo convierte texto libre en datos comparables: anios de experiencia,
nivel de titulacion y nivel de ingles. No sabe nada de MySQL, de embeddings ni
de la interfaz, y por eso se puede probar entero con cadenas de texto.

Existe porque la similitud coseno mide DE QUE VA un CV, no SI EL CANDIDATO
SIRVE: en el espacio semantico "un anio de experiencia" y "ocho anios" son
practicamente el mismo vector. La cantidad hay que leerla aparte.
"""

from __future__ import annotations

import datetime
import re
from dataclasses import dataclass, field
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


# ---------------------------------------------------------------------------
# Nivel de ingles
# ---------------------------------------------------------------------------

NIVELES_MCER: dict[str, int] = {
    "a1": 1, "a2": 2, "b1": 3, "b2": 4, "c1": 5, "c2": 6,
}

# Expresiones sueltas que la gente escribe en vez del codigo del MCER. El mapeo
# es conservador a proposito: "nivel alto" se traduce a C1 y no a C2 porque
# quien tiene un C2 acreditado casi siempre lo escribe como C2.
_EQUIVALENCIAS_MCER: dict[str, int] = {
    "nativo": 6, "nativa": 6, "native": 6, "bilingue": 6, "bilingual": 6,
    "nivel alto": 5, "fluido": 5, "fluida": 5, "fluent": 5, "avanzado": 5,
}

# El nivel debe ir pegado a la mencion del ingles, no suelto por la linea: un
# CV que diga "Ingles C1. Frances B1." tiene que dar C1 y no B1. Se busca la
# palabra 'ingles'/'english' y se mira solo en la ventana siguiente, cortando
# en cuanto aparece otro idioma.
_OTROS_IDIOMAS = r"frances|french|aleman|german|italiano|italian|portugues|portuguese|catalan|valenciano|espanol|spanish|chino|chinese"


def _nivel_ingles(texto: str) -> int | None:
    """Nivel de ingles mencionado en el texto, o None si no se menciona."""
    plano = _normalizar(texto)

    for encaje in re.finditer(r"\bingl[eé]s\b|\benglish\b", plano):
        # Ventana desde la mencion del ingles hasta el siguiente idioma o el
        # final de la frase, lo que llegue antes.
        resto = plano[encaje.end():encaje.end() + 80]
        corte = re.search(_OTROS_IDIOMAS, resto)
        if corte:
            resto = resto[:corte.start()]

        codigo = re.search(r"\b([abc][12])\b", resto)
        if codigo:
            return NIVELES_MCER[codigo.group(1)]

        for expresion, nivel in _EQUIVALENCIAS_MCER.items():
            if expresion in resto:
                return nivel

    return None


def ingles_de_cv(texto: str) -> int | None:
    """Nivel de ingles que el candidato acredita, leido de su seccion IDIOMAS.

    Se busca solo ahi y no en el CV entero para no confundir el nivel del
    candidato con la mencion de un requisito o de una certificacion citada en
    otro contexto.
    """
    return _nivel_ingles(secciones_cv(texto)["idiomas"])


def ingles_de_oferta(texto: str) -> int | None:
    """Nivel de ingles EXIGIDO por la oferta.

    Solo cuenta lo que este bajo la seccion de requisitos. Lo que aparece bajo
    'Se valorara' es un merito, no una condicion, y penalizar por ello seria
    castigar a candidatos perfectamente validos.
    """
    return _nivel_ingles(secciones_oferta(texto)["requisitos"])


# ---------------------------------------------------------------------------
# Nivel de titulacion
# ---------------------------------------------------------------------------

# Se compara SOLO el nivel academico, nunca la rama. Decidir si un "Grado en
# Matematicas" vale para una oferta que pide "Grado en Informatica" es un
# problema semantico, y para eso ya esta el coseno: duplicarlo aqui con una
# lista de sinonimos daria un resultado peor y ademas invisible.
#
# El orden importa. Se evalua de mayor a menor y "grado superior" va antes que
# "grado" porque lo contiene: al reves, un Grado Superior de FP se leeria como
# un Grado universitario y subiria un nivel que no tiene.
_TITULACIONES: list[tuple[int, str]] = [
    (3, r"\bm[aá]ster\b|\bmaster\b|\bmsc\b|\bmba\b|\bdoctorad|\bphd\b|\bdoctor\b"),
    (1, r"\bgrado superior\b|\bciclo formativo de grado superior\b|\bfp\b|\bformaci[oó]n profesional\b"),
    (2, r"\bgrado\b|\blicenciatur|\bingenier[ií]a t[eé]cnica\b|\bingenier[ií]a\b|\bbachelor\b|\bbsc\b|\bdegree\b"),
]


def _nivel_titulacion(texto: str) -> int | None:
    """Titulacion mas alta mencionada en el texto, o None si no hay ninguna."""
    plano = _normalizar(texto)

    # 'Grado Superior' se neutraliza antes de buscar los niveles universitarios
    # para que su palabra 'grado' no se cuente dos veces.
    encontrados = []
    if re.search(_TITULACIONES[1][1], plano):
        encontrados.append(1)
        plano = re.sub(r"\bgrado superior\b", " ", plano)
    if re.search(_TITULACIONES[0][1], plano):
        encontrados.append(3)
    if re.search(_TITULACIONES[2][1], plano):
        encontrados.append(2)

    return max(encontrados) if encontrados else None


def titulacion_de_cv(texto: str) -> int | None:
    """Titulacion mas alta que el candidato acredita, de su seccion FORMACION.

    Se toma el maximo y no la primera: lo relevante es el techo academico, y en
    un CV el Master y el Grado que lo precede aparecen juntos.
    """
    return _nivel_titulacion(secciones_cv(texto)["formacion"])


def titulacion_de_oferta(texto: str) -> int | None:
    """Titulacion EXIGIDA por la oferta, de su seccion de requisitos."""
    return _nivel_titulacion(secciones_oferta(texto)["requisitos"])


# ---------------------------------------------------------------------------
# Anios de experiencia
# ---------------------------------------------------------------------------

_NUMEROS_EN_LETRA: dict[str, int] = {
    "un": 1, "uno": 1, "una": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5,
    "seis": 6, "siete": 7, "ocho": 8, "nueve": 9, "diez": 10,
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
    "seven": 7, "eight": 8, "nine": 9, "ten": 10,
}

_HASTA_HOY = r"actualidad|actual|presente|hoy|present|now|current"

# Rango de anios: '2019-2024', '2021 - actualidad', '(2018-2019)'.
_RANGO = re.compile(
    r"\b(19[89]\d|20[0-4]\d)\s*[-–—/]\s*(19[89]\d|20[0-4]\d|" + _HASTA_HOY + r")\b"
)


def _unir_intervalos(intervalos: list[tuple[int, int]]) -> int:
    """Anios cubiertos por la union de los intervalos, sin contar solapes.

    Sumar cada intervalo por separado inflaria el total: en un CV el anio de
    salida de un empleo suele ser el mismo que el de entrada del siguiente, y
    ese anio se contaria dos veces.
    """
    if not intervalos:
        return 0

    ordenados = sorted(intervalos)
    fusionados = [ordenados[0]]
    for inicio, fin in ordenados[1:]:
        ultimo_inicio, ultimo_fin = fusionados[-1]
        if inicio <= ultimo_fin:
            fusionados[-1] = (ultimo_inicio, max(ultimo_fin, fin))
        else:
            fusionados.append((inicio, fin))

    return sum(fin - inicio for inicio, fin in fusionados)


def _anios_por_rangos(texto: str) -> int | None:
    """Anios cubiertos por los rangos de fechas del texto, o None si no hay."""
    anio_actual = datetime.date.today().year

    intervalos = []
    for encaje in _RANGO.finditer(_normalizar(texto)):
        inicio = int(encaje.group(1))
        fin_bruto = encaje.group(2)
        fin = anio_actual if not fin_bruto.isdigit() else int(fin_bruto)
        if fin >= inicio:
            intervalos.append((inicio, fin))

    if not intervalos:
        return None
    return _unir_intervalos(intervalos)


# Frase explicita: el numero debe ir seguido de 'de experiencia' o de un
# gerundio. Sin esa exigencia, 'un monolito de siete anos' daria siete anios de
# experiencia a quien tiene ocho, y por un motivo que no habla del candidato
# sino del sistema que migro. Es un caso real del CV de Ana Ruiz.
_FRASE_ANIOS = re.compile(
    r"\b(\d{1,2}|" + "|".join(_NUMEROS_EN_LETRA) + r")\s*\+?\s*a[nñ]os?\s+"
    r"(?:de\s+experiencia|\w+ando|\w+iendo|of\s+experience)"
    r"|\b(\d{1,2}|" + "|".join(_NUMEROS_EN_LETRA) + r")\s*\+?\s*years?\s+of\s+experience"
)


def _anios_por_frase(texto: str) -> int | None:
    """Anios declarados en una frase explicita, o None si no la hay."""
    encaje = _FRASE_ANIOS.search(_normalizar(texto))
    if not encaje:
        return None

    bruto = next(g for g in encaje.groups() if g)
    return int(bruto) if bruto.isdigit() else _NUMEROS_EN_LETRA[bruto]


def anios_de_cv(texto: str) -> int | None:
    """Anios de experiencia del candidato.

    Orden estricto y deliberado:

    1. Rangos de fechas de la seccion de EXPERIENCIA. Es la via principal
       porque es la unica objetiva: son datos, no una afirmacion del candidato.
    2. Solo si no hay ningun rango, una frase explicita, buscada en el CV
       entero porque suele estar en el titular o en el perfil.

    Invertir el orden seria un error medible: el CV de Ana Ruiz menciona 'un
    monolito de siete anos' dentro de su experiencia, y una busqueda de frases
    que fuese primero le asignaria siete anios en vez de los ocho que suman sus
    rangos.
    """
    secciones = secciones_cv(texto)

    por_rangos = _anios_por_rangos(secciones["experiencia"])
    if por_rangos:
        return por_rangos

    return _anios_por_frase(texto)


def anios_de_oferta(texto: str) -> int | None:
    """Anios de experiencia EXIGIDOS, de la seccion de requisitos de la oferta.

    Solo la via de la frase explicita: una oferta no lleva rangos de fechas, y
    lo que se busca es un minimo declarado ('minimo 5 anos', 'al menos tres
    anos', '3+ anos', 'at least 3 years').
    """
    return _anios_por_frase(secciones_oferta(texto)["requisitos"])


# ---------------------------------------------------------------------------
# Ensamblaje
# ---------------------------------------------------------------------------

# Cuanto baja el score por cada unidad que falta, y hasta donde puede llegar.
#
# CALIBRADAS CONTRA LA ESCALA REAL DE SCORES DE ESTE CORPUS: la distancia entre
# el primero y el segundo va de 0,015 a 0,16, y en la zona media del ranking
# baja de 0,02. Los anios se ponen A PROPOSITO por encima de esa escala para
# que un requisito de experiencia mande sobre la afinidad tematica: faltando un
# solo anio, 0,05 ya supera cualquier diferencia de la zona media.
#
# El efecto asumido es que la experiencia domina sobre los otros dos criterios.
# Es una decision de producto, no una propiedad emergente de los numeros.
#
# SI SE CAMBIA EL MODELO DE EMBEDDINGS HAY QUE REMEDIRLAS: otra escala de
# scores convierte estas constantes en ruido o en una apisonadora.
PENALIZACIONES: dict[str, tuple[float, float]] = {
    # criterio:      (por unidad, tope)
    "anios":         (0.05, 0.20),
    "titulacion":    (0.04, 0.08),
    "ingles":        (0.03, 0.09),
}

_NOMBRE_MCER = {nivel: codigo.upper() for codigo, nivel in NIVELES_MCER.items()}
_NOMBRE_TITULACION = {1: "FP o Grado Superior", 2: "Grado", 3: "Máster"}


@dataclass(frozen=True)
class Requisitos:
    """Lo que la oferta EXIGE. None = no lo pide, asi que no se filtra por el."""

    anios: int | None = None
    titulacion: int | None = None
    ingles: int | None = None


@dataclass(frozen=True)
class Perfil:
    """Lo que el candidato ACREDITA. None = no se pudo extraer, NO es cero."""

    anios: int | None = None
    titulacion: int | None = None
    ingles: int | None = None


@dataclass(frozen=True)
class Veredicto:
    """Cuanto baja el candidato y por que, en lenguaje legible."""

    penalizacion: float = 0.0
    avisos: list[str] = field(default_factory=list)


def extraer_de_oferta(texto: str) -> Requisitos:
    """Requisitos duros que la oferta declara de forma explicita."""
    return Requisitos(
        anios=anios_de_oferta(texto),
        titulacion=titulacion_de_oferta(texto),
        ingles=ingles_de_oferta(texto),
    )


def extraer_de_cv(texto: str) -> Perfil:
    """Lo que el CV acredita en los tres criterios del filtro."""
    return Perfil(
        anios=anios_de_cv(texto),
        titulacion=titulacion_de_cv(texto),
        ingles=ingles_de_cv(texto),
    )


def evaluar(requisitos: Requisitos, perfil: Perfil) -> Veredicto:
    """Penalizacion y avisos de un candidato frente a una oferta.

    Un criterio solo penaliza cuando se dan las dos condiciones a la vez: la
    oferta lo exige Y el CV acredita menos. Si la oferta no lo pide, o si el
    dato del candidato no se pudo extraer, no pasa nada. Esa asimetria es
    deliberada: el sistema calla en lugar de inventar, porque un descarte por
    fallo del parser seria un error que nadie ve.

    La penalizacion es proporcional a la distancia y no binaria. Un umbral de
    si o no trataria igual a quien tiene cuatro anios y a quien tiene uno
    frente a una oferta que pide cinco, y eso es falso.
    """
    penalizacion = 0.0
    avisos: list[str] = []

    comparaciones = [
        ("anios", requisitos.anios, perfil.anios,
         lambda pide, tiene: f"pide {pide} años de experiencia, se le calculan {tiene}"),
        ("titulacion", requisitos.titulacion, perfil.titulacion,
         lambda pide, tiene: f"pide {_NOMBRE_TITULACION[pide]}, acredita {_NOMBRE_TITULACION.get(tiene, 'ninguna titulación')}"),
        ("ingles", requisitos.ingles, perfil.ingles,
         lambda pide, tiene: f"pide inglés {_NOMBRE_MCER[pide]}, acredita {_NOMBRE_MCER[tiene]}"),
    ]

    for criterio, exigido, acreditado, redactar in comparaciones:
        if exigido is None or acreditado is None or acreditado >= exigido:
            continue

        por_unidad, tope = PENALIZACIONES[criterio]
        penalizacion += min((exigido - acreditado) * por_unidad, tope)
        avisos.append(redactar(exigido, acreditado))

    return Veredicto(penalizacion=round(penalizacion, 4), avisos=avisos)
