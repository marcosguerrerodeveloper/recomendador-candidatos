"""Paso 3 del pipeline: convertir texto en vectores y persistirlos en MySQL.

Por que este paso vive separado de la extraccion y del matching: el modelo de
embeddings es el unico recurso caro del proyecto (tarda segundos en cargar y
ocupa memoria), asi que conviene aislarlo detras de una funcion que lo cachee.
El resto de scripts pueden importar `embed()` sin preocuparse de cuando se
carga el modelo ni de cuantas veces se llama.

Decision cerrada (ver CLAUDE.md): embeddings LOCALES con sentence-transformers,
modelo multilingue, sin ninguna API externa.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path

import numpy as np
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

from extract_text import extraer_carpeta, extraer_texto, nombre_candidato
from db_setup import conectar, crear_tablas

# load_dotenv() sin argumentos resuelve el .env desde el cwd, que cambia segun
# desde donde se lance el script. Ruta explicita para que siempre sea el mismo.
load_dotenv(Path(__file__).resolve().parent / ".env")

# Nombre del modelo configurable por .env, pero con el valor cerrado del
# proyecto como defecto para que el script funcione aunque falte la variable.
MODELO_POR_DEFECTO = "paraphrase-multilingual-MiniLM-L12-v2"

# Cache a nivel de modulo: el modelo se carga una unica vez por proceso.
_modelo: SentenceTransformer | None = None


def cargar_modelo() -> SentenceTransformer:
    """Devuelve el modelo de embeddings, cargandolo solo la primera vez.

    La carga perezosa evita pagar los segundos de arranque cuando otro modulo
    importa este fichero solo para reutilizar, por ejemplo, `guardar_puesto`.
    """
    global _modelo
    if _modelo is None:
        nombre = os.getenv("EMBEDDING_MODEL", MODELO_POR_DEFECTO)
        print(f"[modelo] Cargando '{nombre}' (solo la primera vez)...")
        _modelo = SentenceTransformer(nombre)
        dimension = _modelo.get_sentence_embedding_dimension()
        print(f"[modelo] Listo. Dimension del vector: {dimension}")
    return _modelo


def _trocear(texto: str, limite_tokens: int) -> list[str]:
    """Parte un texto en trozos que quepan enteros en la ventana del modelo.

    Se corta por frases y saltos de linea, no por numero de caracteres, para
    que ningun trozo empiece a mitad de una idea. Si una sola frase ya excede
    el limite (pasa con las secciones de 'Tecnologias', que son una enumeracion
    larguisima sin puntos), se parte por palabras como ultimo recurso.
    """
    tokenizer = cargar_modelo().tokenizer

    def contar(fragmento: str) -> int:
        return len(tokenizer.tokenize(fragmento))

    # Unidades minimas: frases (corte tras . ! ?) y lineas.
    unidades = [u.strip() for u in re.split(r"(?<=[.!?])\s+|\n+", texto) if u.strip()]

    # Una unidad demasiado larga se subdivide por palabras hasta que quepa.
    unidades_ajustadas: list[str] = []
    for unidad in unidades:
        if contar(unidad) <= limite_tokens:
            unidades_ajustadas.append(unidad)
            continue
        acumulado: list[str] = []
        for palabra in unidad.split():
            if acumulado and contar(" ".join(acumulado + [palabra])) > limite_tokens:
                unidades_ajustadas.append(" ".join(acumulado))
                acumulado = []
            acumulado.append(palabra)
        if acumulado:
            unidades_ajustadas.append(" ".join(acumulado))

    # Agrupacion voraz: se juntan unidades consecutivas mientras quepan.
    # Se mide el trozo YA UNIDO en cada paso, en vez de ir sumando los tokens de
    # cada unidad por separado. Sumar seria mas barato pero es solo una
    # estimacion: el tokenizador no tiene por que partir igual dos textos sueltos
    # que su concatenacion, y una desviacion al alza haria que el trozo superase
    # la ventana y el modelo volviese a truncar en silencio, que es exactamente
    # el bug que esta funcion existe para evitar.
    trozos: list[str] = []
    actual: list[str] = []
    for unidad in unidades_ajustadas:
        if actual and contar(" ".join(actual + [unidad])) > limite_tokens:
            trozos.append(" ".join(actual))
            actual = []
        actual.append(unidad)
    if actual:
        trozos.append(" ".join(actual))

    return trozos or [texto]


def embed(texto: str) -> np.ndarray:
    """Convierte un texto en su vector semantico de 384 dimensiones.

    Por que no se llama a encode(texto) y ya: el modelo tiene una ventana de
    solo 128 tokens (`max_seq_length`) y TRUNCA en silencio todo lo que sobra.
    Con eso, de cada CV solo se comparaban el nombre, el titular y el parrafo
    de perfil -- prosa profesional generica que se parece entre todos los
    candidatos -- mientras que la seccion de tecnologias, que es justo la que
    distingue a un backend de un frontend, quedaba fuera del vector. El sintoma
    medido era un control negativo (perfil de RRHH) puntuando por encima de
    perfiles tecnicos frente a una oferta de backend.

    La solucion es tratar el documento como la suma de sus partes: se trocea en
    fragmentos que caben enteros en la ventana, se embebe cada uno, se normaliza
    y se promedia. Normalizar ANTES de promediar es importante: sin ello, un
    fragmento con vector de mayor magnitud arrastraria la media hacia su tema
    solo por ser mas "energico", no por ser mas representativo del documento.

    Contrapartida honesta de promediar, visible en los rankings del paso 5:
    la media convierte el documento en su CENTROIDE tematico, asi que un CV
    largo que toca muchos temas queda a media distancia de cualquier oferta y
    puntua alto contra todas sin ser el mejor para ninguna. Alternativas
    conocidas y descartadas por complejidad para un portfolio: quedarse con el
    maximo por dimension (max-pooling), o rankear por el mejor fragmento en vez
    de por la media, que responderia "que parte de este CV encaja" en lugar de
    "cuanto encaja el CV entero".

    Se fuerza float32 porque es lo que devuelve el modelo y asi el vector que
    se guarda en MySQL y el que se recupera en match.py tienen exactamente el
    mismo tipo: cualquier diferencia de precision ensuciaria los scores.
    """
    _, vectores = embed_fragmentos(texto)
    return vectores.mean(axis=0).astype(np.float32)


def fragmentos_de(texto: str) -> list[str]:
    """Trozos en que se parte un texto para embeberlo.

    Se expone aparte porque el troceo es DETERMINISTA: dado el mismo texto
    devuelve siempre los mismos trozos en el mismo orden. Eso permite guardar en
    la base de datos solo los vectores y recuperar despues el texto del fragmento
    que mejor encajo por su indice, sin duplicar el CV entero en la tabla.
    """
    modelo = cargar_modelo()
    # Margen de 2 tokens para los especiales que el tokenizador anade (<s>, </s>).
    return _trocear(texto, max(modelo.max_seq_length - 2, 16))


def embed_fragmentos(texto: str) -> tuple[list[str], np.ndarray]:
    """Devuelve los fragmentos de un texto y sus vectores YA NORMALIZADOS.

    Los vectores salen normalizados a norma 1 por dos motivos. Uno, promediarlos
    para obtener el vector del documento exige normalizar antes (si no, un
    fragmento de mayor magnitud arrastra la media por energico y no por
    representativo). Y dos, con vectores unitarios el coseno se reduce al producto
    escalar, asi que comparar la oferta contra todos los fragmentos es una sola
    multiplicacion de matrices.
    """
    modelo = cargar_modelo()
    trozos = fragmentos_de(texto)

    vectores = np.asarray(modelo.encode(trozos), dtype=np.float32)
    if vectores.ndim == 1:  # un unico trozo: encode devuelve vector plano
        vectores = vectores[np.newaxis, :]

    normas = np.linalg.norm(vectores, axis=1, keepdims=True)
    normas[normas == 0.0] = 1.0  # un trozo vacio no debe generar NaN
    return trozos, (vectores / normas).astype(np.float32)


def _serializar(vector: np.ndarray) -> str:
    """Vector -> texto JSON, formato en el que MySQL guarda el embedding.

    MySQL no tiene tipo vector nativo (decision cerrada: nada de vector DBs),
    asi que la lista de floats en una columna JSON es el almacenamiento mas
    simple y legible posible. La similitud se calcula luego en Python.
    """
    return json.dumps(vector.tolist())


def guardar_candidato(conn, nombre: str, archivo: str, texto: str,
                      vector: np.ndarray,
                      fragmentos: np.ndarray | None = None) -> int:
    """Inserta o actualiza un candidato y devuelve su id.

    Es un UPSERT sobre la columna UNIQUE 'archivo' para que reprocesar la
    carpeta de CVs las veces que haga falta no duplique candidatos ni obligue
    a vaciar la tabla a mano.

    Se guardan las dos representaciones del candidato: el vector promedio, que
    responde a "cuanto encaja este CV entero", y la matriz de fragmentos, que
    permite responder a "cual es la parte de este CV que mejor encaja". La
    segunda es la que usa el ranking; la primera se conserva porque es barata y
    sirve de comparacion.
    """
    matriz = None if fragmentos is None else json.dumps(
        [f.tolist() for f in fragmentos])

    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO candidatos (nombre, archivo, texto_cv, embedding, fragmentos)
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            nombre = VALUES(nombre),
            texto_cv = VALUES(texto_cv),
            embedding = VALUES(embedding),
            fragmentos = VALUES(fragmentos)
        """,
        (nombre, archivo, texto, _serializar(vector), matriz),
    )
    # lastrowid es 0 cuando el UPDATE no cambio nada, asi que en ese caso se
    # consulta el id real por 'archivo' en vez de devolver un id invalido.
    candidato_id = cursor.lastrowid
    if not candidato_id:
        cursor.execute("SELECT id FROM candidatos WHERE archivo = %s", (archivo,))
        candidato_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    return int(candidato_id)


def _huella(descripcion: str) -> str:
    """SHA-256 del texto de la oferta: es lo que da identidad a un puesto.

    El titulo no sirve como identidad porque se deriva del nombre del fichero y
    por stdin es siempre la misma cadena. El texto si: la misma oferta relanzada
    produce la misma huella y actualiza su fila, y una oferta distinta produce
    otra y crea una nueva.
    """
    return hashlib.sha256(descripcion.strip().encode("utf-8")).hexdigest()


def guardar_puesto(conn, titulo: str, descripcion: str, vector: np.ndarray) -> int:
    """Inserta o actualiza una oferta y devuelve su id.

    UPSERT sobre la columna UNIQUE 'huella'. Sin el, cada ejecucion de match.py
    insertaba una fila nueva aunque la oferta fuese identica, y la tabla crecia
    sin limite; con n8n disparando el webhook (paso 6) eso se dispara.
    """
    cursor = conn.cursor()
    huella = _huella(descripcion)
    cursor.execute(
        """
        INSERT INTO puestos (titulo, descripcion, huella, embedding)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            titulo = VALUES(titulo),
            embedding = VALUES(embedding)
        """,
        (titulo, descripcion, huella, _serializar(vector)),
    )
    # Mismo motivo que en guardar_candidato: lastrowid vale 0 si el UPDATE no
    # cambio nada, asi que se recupera el id real por la clave unica.
    puesto_id = cursor.lastrowid
    if not puesto_id:
        cursor.execute("SELECT id FROM puestos WHERE huella = %s", (huella,))
        puesto_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    return int(puesto_id)


def procesar_pdf(ruta_pdf: Path) -> dict:
    """Extrae, embebe y guarda UN solo CV. Devuelve sus datos ya persistidos.

    Existe aparte de procesar_cvs() porque el flujo A del paso 6 (n8n) da de alta
    candidatos de uno en uno segun van llegando por el webhook, y reprocesar la
    carpeta entera por cada PDF nuevo seria absurdo. La logica es la misma; lo
    unico que cambia es la unidad de trabajo.
    """
    crear_tablas()
    ruta_pdf = Path(ruta_pdf)
    texto = extraer_texto(ruta_pdf)
    if not texto.strip():
        raise ValueError(
            f"'{ruta_pdf.name}' no tiene texto extraible. Suele significar que el "
            "PDF es un escaneo (una imagen), que necesitaria OCR."
        )

    nombre = nombre_candidato(ruta_pdf.name, texto)
    _, fragmentos = embed_fragmentos(texto)
    vector = fragmentos.mean(axis=0).astype(np.float32)

    conn = conectar()
    try:
        candidato_id = guardar_candidato(
            conn, nombre, ruta_pdf.name, texto, vector, fragmentos)
    finally:
        conn.close()

    return {
        "id": candidato_id,
        "nombre": nombre,
        "archivo": ruta_pdf.name,
        "caracteres": len(texto),
        "dimension": int(vector.shape[0]),
    }


def procesar_cvs(carpeta: Path | None = None) -> int:
    """Extrae, embebe y guarda todos los CVs de una carpeta. Devuelve cuantos.

    Orquesta los pasos 1 -> 3 sin reimplementar nada: la extraccion vive en
    extract_text.py y la conexion en db_setup.py.
    """
    crear_tablas()
    textos = extraer_carpeta(carpeta)
    if not textos:
        print("No se encontro ningun PDF que procesar.")
        return 0

    conn = conectar()
    guardados = 0
    try:
        for archivo, texto in sorted(textos.items()):
            if not texto.strip():
                print(f"  [aviso] {archivo}: sin texto extraible, se omite.")
                continue
            nombre = nombre_candidato(archivo, texto)
            trozos, fragmentos = embed_fragmentos(texto)
            vector = fragmentos.mean(axis=0).astype(np.float32)
            guardar_candidato(conn, nombre, archivo, texto, vector, fragmentos)
            guardados += 1
            print(f"  {nombre:<50} {len(texto):>6} caracteres  "
                  f"{len(trozos):>2} fragmentos de {vector.shape[0]} dims")
    finally:
        conn.close()

    return guardados


if __name__ == "__main__":
    print("=== Paso 3: generacion y almacenamiento de embeddings ===")
    total = procesar_cvs()
    print(f"\nTotal de candidatos guardados en MySQL: {total}")
