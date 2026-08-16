"""Paso 1 del pipeline: extraccion de texto plano a partir de CVs en PDF.

Se usa pdfplumber y no PyPDF2 porque los CVs reales traen columnas y tablas,
y PyPDF2 devuelve el texto entrelazado o directamente vacio en esos casos.

La limpieza de este modulo es deliberadamente conservadora: solo arregla los
artefactos tipograficos del PDF (palabras cortadas por guion, espacios dobles,
lineas en blanco repetidas) y conserva los saltos de parrafo, porque esa
estructura (secciones tipo "Experiencia", "Formacion") es informacion util
para el modelo de embeddings del Paso 3.
"""

from __future__ import annotations

import os
import re
import unicodedata
from pathlib import Path

import pdfplumber
from dotenv import load_dotenv

# Carga explicita del .env: load_dotenv() sin argumentos parte del directorio
# del archivo que la invoca, asi que se fija la ruta para que funcione igual
# tanto ejecutando el script directo como importandolo desde otro modulo.
load_dotenv(Path(__file__).resolve().parent / ".env")

RAIZ_PROYECTO = Path(__file__).resolve().parent


def _ruta_desde_raiz(valor: str) -> Path:
    """Convierte una ruta del .env en absoluta, anclandola a la raiz del proyecto.

    En el .env las rutas se escriben en relativo (CVS_DIR=cvs) porque es lo
    legible. Pero una ruta relativa se resuelve contra el cwd, y el cwd depende
    de desde donde se lance el script: llamar a este modulo desde n8n o desde
    otra carpeta hacia que 'cvs' no existiera. Anclando a la carpeta del
    proyecto, la misma configuracion funciona se lance desde donde se lance.
    """
    ruta = Path(valor).expanduser()
    return ruta if ruta.is_absolute() else (RAIZ_PROYECTO / ruta).resolve()


# Carpeta por defecto de CVs, configurable desde el .env.
CVS_DIR = _ruta_desde_raiz(os.getenv("CVS_DIR", "cvs"))


def _recomponer_acentos(texto: str) -> str:
    """Reconstruye las vocales acentuadas que el PDF trae partidas en dos glifos.

    Los CVs generados con LaTeX (aqui, 'Evaristo CV.pdf') no incrustan el
    caracter 'o' sino la letra base y el acento como dos glifos independientes.
    Al extraer el texto salen cosas como 'Formacio´n', 'M´aster', 'Espan˜a' o
    'Tecnolog´ıa'. Para el modelo de embeddings eso no son palabras en espanol:
    el tokenizador las parte en fragmentos sin sentido y se pierde el
    significado de secciones enteras del CV.

    El acento aparece unas veces DETRAS de su letra y otras DELANTE, porque el
    orden depende de la coordenada X con la que el PDF dibujo cada glifo. Por
    eso se prueban las dos posiciones, siempre en ese orden: si la letra previa
    admite el acento, gana ella; si no, se mira la siguiente.
    """
    # LaTeX usa la 'i sin punto' como base para poner encima el acento.
    texto = texto.replace("\u0131", "i").replace("\u0130", "I")

    # Acento suelto DETRAS de su letra: 'Formacio´n' -> 'Formacion' + acento.
    texto = re.sub(r"([aeiouAEIOU])\u00b4", "\\1\u0301", texto)
    texto = re.sub(r"([nN])\u02dc", "\\1\u0303", texto)

    # Acento suelto DELANTE de su letra: 'M´aster' -> 'Master' + acento.
    texto = re.sub(r"\u00b4([aeiouAEIOU])", "\\1\u0301", texto)
    texto = re.sub(r"\u02dc([nN])", "\\1\u0303", texto)

    # NFC funde letra + marca combinante en un unico caracter ('o'+U+0301 -> 'ó').
    return unicodedata.normalize("NFC", texto)


def _limpiar(texto: str) -> str:
    """Normaliza el texto crudo del PDF sin destruir su estructura de parrafos.

    El orden importa: primero se unen las palabras partidas por guion (si se
    colapsaran antes los saltos de linea, el guion quedaria en medio de la
    frase y ya no se sabria que era un corte tipografico).
    """
    # Antes que nada, arreglar los acentos rotos: si no, un 'Formacio´n' llega
    # entero hasta el embedding y contamina el vector del candidato.
    texto = _recomponer_acentos(texto)

    # Vinetas decorativas: no aportan significado y el tokenizador las gasta
    # como tokens propios dentro de una ventana de contexto ya escasa.
    texto = re.sub(r"[\u2022\u25e6\u25cf\u25aa\u00b7]", " ", texto)

    # "desarro-\nllador" -> "desarrollador"
    texto = re.sub(r"-\s*\n\s*", "", texto)

    # Espacios y tabuladores multiples -> un solo espacio (sin tocar los \n).
    texto = re.sub(r"[ \t\r\f\v]+", " ", texto)

    # Espacios sobrantes al principio y final de cada linea.
    texto = "\n".join(linea.strip() for linea in texto.split("\n"))

    # Tres o mas saltos seguidos -> uno doble: se conserva el corte de parrafo
    # pero se eliminan los huecos enormes que dejan los PDFs maquetados.
    texto = re.sub(r"\n{3,}", "\n\n", texto)

    return texto.strip()


def extraer_texto(ruta_pdf: Path) -> str:
    """Devuelve el texto plano limpio de un PDF, concatenando todas sus paginas.

    Las paginas se separan con linea en blanco para que un CV de varias paginas
    (CV1.pdf tiene 3) no acabe pegando el final de una con el inicio de la otra.
    """
    paginas: list[str] = []
    with pdfplumber.open(str(ruta_pdf)) as pdf:
        for pagina in pdf.pages:
            texto_pagina = pagina.extract_text() or ""
            if texto_pagina.strip():
                paginas.append(texto_pagina)
    return _limpiar("\n\n".join(paginas))


def extraer_carpeta(carpeta: Path | None = None) -> dict[str, str]:
    """Extrae el texto de todos los PDFs de una carpeta.

    Devuelve {nombre_archivo_con_extension: texto}. Se conserva la extension
    en la clave porque 'archivo' es la columna UNIQUE de la tabla candidatos,
    y asi la clave del diccionario es ya el identificador natural del candidato.
    """
    carpeta = Path(carpeta) if carpeta is not None else CVS_DIR
    if not carpeta.is_dir():
        raise FileNotFoundError(f"No existe la carpeta de CVs: {carpeta}")

    resultados: dict[str, str] = {}
    for ruta in sorted(carpeta.glob("*.pdf")):
        try:
            resultados[ruta.name] = extraer_texto(ruta)
        except Exception as error:  # un PDF corrupto no debe tumbar el lote
            print(f"[AVISO] No se pudo leer {ruta.name}: {error}")
            resultados[ruta.name] = ""
    return resultados


# Nombres a mostrar en lugar del que trae el documento. Los dos CVs reales del
# proyecto contienen datos personales (nombre completo, email, telefono) y uno
# es de un tercero, asi que se muestran con seudonimo: las capturas del README
# y la demo del portfolio son publicas. Los PDF en si ya quedan fuera del
# repositorio por .gitignore; esto cubre lo que se ve en pantalla.
ALIAS: dict[str, str] = {
    "CV1.pdf": "CV1",
    "Evaristo CV.pdf": "Evaristo CV",
}

# Encabezados que ocupan la primera linea de algunos CVs en lugar del nombre.
_ENCABEZADOS = {
    "curriculum", "curriculum vitae", "cv", "resume", "resumen",
    "hoja de vida", "datos personales",
}

# Un nombre propio: solo letras (con tildes y ñ), guiones, apostrofes y puntos
# de inicial. Excluye digitos, arrobas y barras, que delatan una linea de
# contacto en vez de un nombre.
_PATRON_NOMBRE = re.compile(r"^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ][A-Za-zÁÉÍÓÚÜÑáéíóúüñ'’.\-]*$")


def nombre_desde_texto(texto: str) -> str | None:
    """Extrae el nombre del candidato de la primera linea util de su CV.

    El nombre correcto vive DENTRO del documento, no en como se llame el
    fichero: un archivo llamado 'beatriz_nogales_rrhh.pdf' solo puede producir
    'Beatriz Nogales Rrhh', mientras que su primera linea dice 'Beatriz Nogales
    Cuesta'. Y un fichero nunca puede devolver las tildes, porque casi nadie las
    pone al nombrar archivos.

    Devuelve None si la primera linea no parece un nombre de persona, para que
    quien llame pueda caer al nombre del fichero en lugar de mostrar basura.
    """
    for linea in texto.splitlines():
        linea = linea.strip()
        if not linea:
            continue

        if linea.lower().strip(".:") in _ENCABEZADOS:
            continue  # 'CURRICULUM VITAE' y similares: sigue buscando

        palabras = linea.split()
        if not 2 <= len(palabras) <= 5 or not 5 <= len(linea) <= 60:
            return None
        if not all(_PATRON_NOMBRE.match(p) for p in palabras):
            return None

        # 'MARCOS GUERRERO' -> 'Marcos Guerrero'. Si ya viene en mayusculas y
        # minusculas se respeta tal cual, porque puede traer particulas ('de la
        # Cruz') que capitalizar estropearia.
        if linea.isupper():
            return linea.title()
        return linea

    return None


def puesto_desde_texto(texto: str) -> str | None:
    """Extrae el puesto del candidato de la linea siguiente a su nombre.

    En un CV, debajo del nombre va el titular profesional ('Desarrolladora
    Backend Python | 6 anos de experiencia'). Nos quedamos con lo anterior a la
    barra, que es el cargo, y descartamos el resto, que es relleno.

    Devuelve None si esa linea no parece un cargo: lleva digitos (telefono),
    arroba (email), coma (una direccion) o es un encabezado de seccion. Muchos
    CVs ponen los datos de contacto justo ahi, y 'Bargas, Toledo 611408310' no
    es un puesto de trabajo.
    """
    lineas = [l.strip() for l in texto.splitlines() if l.strip()]
    if len(lineas) < 2:
        return None

    candidata = lineas[1].split("|")[0].split("·")[0].strip(" .,-–—")
    if not candidata or not 3 <= len(candidata) <= 60:
        return None
    if any(c.isdigit() for c in candidata) or "@" in candidata or "," in candidata:
        return None
    if candidata.lower() in _ENCABEZADOS or candidata.isupper():
        return None  # 'PERFIL', 'EXPERIENCIA': es un titulo de seccion

    return candidata


def nombre_candidato(nombre_archivo: str, texto: str | None = None) -> str:
    """Nombre legible del candidato: del propio CV si se puede, si no del fichero.

    'texto' es opcional para no romper a quien llame solo con el nombre del
    fichero, pero pasarlo da siempre mejor resultado.

    Sin texto:  'ana_ruiz_backend.pdf' -> 'Ana Ruiz Backend'
    Con texto:  'ana_ruiz_backend.pdf' -> 'Ana Ruiz Melgar'
    En ALIAS:   'CV1.pdf'              -> 'CV1'
    """
    # El seudonimo manda sobre todo lo demas: si un CV esta en ALIAS es porque
    # su nombre real no debe aparecer en pantalla.
    if nombre_archivo in ALIAS:
        return ALIAS[nombre_archivo]

    if texto:
        del_documento = nombre_desde_texto(texto)
        if del_documento:
            # 'Ana Ruiz Melgar - Desarrolladora Backend Python'. El cargo va en
            # el nombre mostrado porque un ranking de candidatos sin saber a que
            # se dedica cada uno obliga a abrir el CV para juzgar si el orden
            # tiene sentido.
            puesto = puesto_desde_texto(texto)
            return f"{del_documento} - {puesto}" if puesto else del_documento

    base = Path(nombre_archivo).stem
    palabras = base.replace("_", " ").replace("-", " ").split()
    return " ".join(p if p.isupper() else p.capitalize() for p in palabras)


if __name__ == "__main__":
    textos = extraer_carpeta()

    print(f"\nCarpeta de CVs: {CVS_DIR}")
    print(f"PDFs encontrados: {len(textos)}\n")

    cabecera = f"{'ARCHIVO':<32} {'CANDIDATO':<26} {'CHARS':>7}  INICIO DEL TEXTO"
    print(cabecera)
    print("-" * len(cabecera))

    for archivo, texto in textos.items():
        inicio = " ".join(texto.split()[:8])
        print(
            f"{archivo:<32} {nombre_candidato(archivo, texto):<26} "
            f"{len(texto):>7}  {inicio[:60]}"
        )

    vacios = [a for a, t in textos.items() if not t.strip()]
    print()
    if vacios:
        print(f"[ERROR] PDFs sin texto extraido: {', '.join(vacios)}")
    else:
        print(f"[OK] Los {len(textos)} PDFs han dado texto no vacio.")
