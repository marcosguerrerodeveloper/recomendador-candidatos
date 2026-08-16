"""Paso 4 — Calculo de similitud y ranking de candidatos frente a una oferta.

Este es el nucleo explicable del proyecto: dada una oferta de trabajo, se embebe
igual que los CVs y se compara contra todos los candidatos guardados en MySQL.
La comparacion se hace en Python (numpy) y no en SQL a proposito: MySQL no tiene
tipo vector nativo, el embedding vive serializado como JSON, y calcularlo aqui
permite ver la formula con los ojos en vez de esconderla tras una funcion.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np
from dotenv import load_dotenv

from db_setup import conectar
from embed_and_store import embed, fragmentos_de, guardar_puesto
from requisitos import evaluar, extraer_de_cv, extraer_de_oferta

# Ruta explicita: load_dotenv() a secas parte del directorio del archivo que la
# llama y puede acabar cargando otro .env o ninguno.
load_dotenv(Path(__file__).resolve().parent / ".env")

RAIZ = Path(__file__).resolve().parent


def similitud_coseno(a: np.ndarray, b: np.ndarray) -> float:
    """Similitud coseno entre dos vectores, escrita a mano.

    Formula:  cos(a, b) = dot(a, b) / (norm(a) * norm(b))

    Por que el coseno y no, por ejemplo, la distancia euclidea: el coseno mide el
    ANGULO entre los dos vectores, es decir su direccion en el espacio semantico,
    e ignora por completo su MAGNITUD. Eso es justo lo que interesa aqui, porque
    comparamos textos de longitud muy distinta: un CV de tres paginas produce un
    vector con mas "energia" acumulada que una oferta de diez lineas, y con una
    metrica sensible a la magnitud los CVs largos ganarian por ser largos, no por
    ser afines. Al dividir por las dos normas se normaliza esa diferencia de
    tamano y solo queda la pregunta relevante: "hacia donde apunta cada texto".

    El resultado teorico va de -1 (opuestos) a 1 (identicos). Con embeddings de
    texto en la practica casi nunca baja de 0, asi que lo util es el orden
    relativo entre candidatos, no el valor absoluto.
    """
    a = np.asarray(a, dtype=np.float32)
    b = np.asarray(b, dtype=np.float32)

    producto_escalar = float(np.dot(a, b))
    norma_a = float(np.linalg.norm(a))
    norma_b = float(np.linalg.norm(b))

    # Un vector nulo no tiene direccion, asi que el angulo no esta definido.
    # Devolvemos 0.0 en vez de dejar que numpy propague un NaN que envenenaria
    # el ordenamiento del ranking entero.
    if norma_a == 0.0 or norma_b == 0.0:
        return 0.0

    return producto_escalar / (norma_a * norma_b)


def _leer_json(valor) -> object:
    """MySQL devuelve las columnas JSON como str o como bytes segun el driver."""
    if isinstance(valor, (bytes, bytearray)):
        valor = valor.decode("utf-8")
    return json.loads(valor)


def cargar_candidatos(conn) -> list[tuple[int, str, np.ndarray, np.ndarray]]:
    """Devuelve [(id, nombre, vector, fragmentos)] de los candidatos procesados.

    'vector' es el embedding del CV completo y 'fragmentos' una matriz (n, 384)
    con un vector unitario por trozo. Se filtran los de embedding NULL porque son
    CVs insertados pero aun no procesados por el paso 3; incluirlos solo
    ensuciaria el ranking con ceros.
    """
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, nombre, embedding, fragmentos
        FROM candidatos WHERE embedding IS NOT NULL
        """
    )
    filas = cursor.fetchall()
    cursor.close()

    candidatos = []
    for id_candidato, nombre, bruto_vector, bruto_frag in filas:
        vector = np.array(_leer_json(bruto_vector), dtype=np.float32)
        fragmentos = (np.array(_leer_json(bruto_frag), dtype=np.float32)
                      if bruto_frag else np.empty((0, vector.shape[0]), np.float32))
        candidatos.append((id_candidato, nombre, vector, fragmentos))

    return candidatos


def mejor_fragmento(vector_oferta: np.ndarray, fragmentos: np.ndarray) -> int:
    """Indice del trozo del CV mas afin a la oferta.

    OJO: esto NO puntua al candidato, solo explica su puntuacion senalando que
    parte de su CV responde a la oferta. Se probo usarlo tambien para ordenar
    (quedarse con el maximo por fragmento en vez de con el promedio) y salio
    medible peor: ver la nota en rankear_detallado.

    Los fragmentos se guardan ya normalizados, asi que basta con normalizar la
    oferta para que el producto escalar SEA el coseno. Es la misma formula de
    similitud_coseno, resuelta de una vez para todos los fragmentos.
    """
    norma = float(np.linalg.norm(vector_oferta))
    if norma == 0.0 or fragmentos.size == 0:
        return 0
    return int(np.argmax(fragmentos @ (vector_oferta / norma)))


def _guardar_matches(conn, puesto_id: int, resultados: list[tuple[int, float]]) -> None:
    """Persiste los scores en 'matches' con UPSERT.

    La clave unica (candidato_id, puesto_id) hace que volver a rankear la misma
    oferta actualice el score en vez de duplicar filas.
    """
    cursor = conn.cursor()
    cursor.executemany(
        """
        INSERT INTO matches (candidato_id, puesto_id, score)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE score = VALUES(score), fecha = CURRENT_TIMESTAMP
        """,
        [(candidato_id, puesto_id, score) for candidato_id, score in resultados],
    )
    conn.commit()
    cursor.close()


def rankear_detallado(
    texto_oferta: str,
    titulo: str = "Oferta sin titulo",
    guardar: bool = True,
) -> list[dict]:
    """Ranking completo, con el fragmento que justifica cada puntuacion.

    Devuelve por candidato: id, nombre, score y el texto del trozo de su CV que
    mejor encajo. Ese extracto es lo que convierte el ranking en algo revisable:
    sin el, un numero pide fe; con el, se puede comprobar en dos segundos si el
    sistema tiene razon.

    Por que la puntuacion sigue siendo el coseno contra el vector PROMEDIO del CV
    y no el maximo por fragmento: se midio. Con las cuatro ofertas de ejemplo y
    dieciocho candidatos, las dos aciertan al ganador, pero la posicion media de
    los dos controles negativos (RRHH y contable, que deberian hundirse en una
    oferta tecnica) empeora segun se da peso al maximo, de forma monotona:

        promedio            16,62 de 18       <- el mejor
        70% promedio + 30% max   16,12
        50% + 50%                15,75
        30% + 70%                15,25
        solo el maximo      13,88 de 18       <- el peor

    El motivo es que el maximo se queda con UN fragmento, y todo CV tiene alguno
    generico (el perfil de apertura, los datos de disponibilidad) que puntua
    tibio contra cualquier oferta. Al promediar, en cambio, se premia que el
    documento entero vaya del tema. La intuicion de "basta con que una parte
    encaje" resulto ser falsa aqui, y por eso el maximo se queda solo para
    explicar, no para ordenar.

    'guardar=False' permite probar una oferta sin ensuciar la base de datos, que
    es lo comodo mientras se afina el pipeline o se llama desde una demo.
    """
    vector_oferta = embed(texto_oferta)

    conn = conectar()
    try:
        candidatos = cargar_candidatos(conn)
        if not candidatos:
            return []

        puntuaciones = []
        for id_candidato, nombre, vector, fragmentos in candidatos:
            puntuaciones.append({
                "id": id_candidato,
                "nombre": nombre,
                "score": similitud_coseno(vector_oferta, vector),
                "fragmento": mejor_fragmento(vector_oferta, fragmentos),
            })
        # Los textos completos se leen una sola vez y sirven para las dos cosas:
        # evaluar los requisitos y reconstruir el fragmento que se cita.
        textos_cv = _textos_crudos(conn, [p["id"] for p in puntuaciones])

        # El filtro se aplica ANTES de ordenar: el orden lo decide el score ya
        # ajustado, no el coseno a secas.
        aplicar_requisitos(puntuaciones, texto_oferta, textos_cv)
        puntuaciones.sort(key=lambda fila: fila["score_ajustado"], reverse=True)

        # El texto del fragmento se reconstruye troceando de nuevo el CV, en vez
        # de guardarlo duplicado en la base de datos. El troceo es determinista,
        # asi que el indice i devuelve siempre el mismo trozo.
        for fila in puntuaciones:
            trozos = fragmentos_de(textos_cv.get(fila["id"], ""))
            fila["extracto"] = (
                trozos[fila["fragmento"]] if fila["fragmento"] < len(trozos) else ""
            )

        if guardar:
            puesto_id = guardar_puesto(conn, titulo, texto_oferta, vector_oferta)
            _guardar_matches(
                conn, puesto_id, [(p["id"], p["score"]) for p in puntuaciones]
            )
    finally:
        conn.close()

    return puntuaciones


def _textos_crudos(conn, ids: list[int]) -> dict[int, str]:
    """Texto completo del CV de cada candidato, sin trocear."""
    if not ids:
        return {}

    marcadores = ", ".join(["%s"] * len(ids))
    cursor = conn.cursor()
    cursor.execute(
        f"SELECT id, texto_cv FROM candidatos WHERE id IN ({marcadores})", ids
    )
    filas = cursor.fetchall()
    cursor.close()

    return {id_c: (texto or "") for id_c, texto in filas}


def aplicar_requisitos(
    puntuaciones: list[dict], texto_oferta: str, textos_cv: dict[int, str]
) -> list[dict]:
    """Anade a cada fila la penalizacion por requisitos no cumplidos.

    Se separa de rankear_detallado para poder probarla sin MySQL y sin cargar
    el modelo de embeddings, que es lo que la hacia intocable estando dentro.

    El score original NO se modifica: se anade 'score_ajustado'. Los dos viajan
    juntos hasta la interfaz porque un unico numero ya corregido no permitiria
    distinguir que parte es afinidad semantica y que parte es correccion por
    requisitos, y esa distincion es justamente lo que hace el ranking revisable.

    Los requisitos de la oferta se extraen UNA vez, fuera del bucle: son los
    mismos para todos los candidatos.
    """
    requisitos = extraer_de_oferta(texto_oferta)

    for fila in puntuaciones:
        veredicto = evaluar(requisitos, extraer_de_cv(textos_cv.get(fila["id"], "")))
        fila["penalizacion"] = veredicto.penalizacion
        fila["avisos"] = veredicto.avisos
        fila["score_ajustado"] = fila["score"] - veredicto.penalizacion

    return puntuaciones


def rankear(
    texto_oferta: str,
    titulo: str = "Oferta sin titulo",
    guardar: bool = True,
) -> list[tuple[str, float]]:
    """Ranking como lista de (candidato, score), ordenado de mayor a menor.

    Se mantiene con esta firma porque es la del contrato del paso 4. Para tener
    ademas el fragmento que justifica cada puntuacion, usar rankear_detallado.
    """
    return [
        (fila["nombre"], fila["score"])
        for fila in rankear_detallado(texto_oferta, titulo, guardar)
    ]


def imprimir_ranking(ranking: list[tuple[str, float]], titulo: str) -> None:
    """Salida de consola pensada para la demo del portfolio y el README."""
    ancho_nombre = max([len(nombre) for nombre, _ in ranking] + [len("CANDIDATO")])
    separador = "=" * (10 + ancho_nombre + 12)

    print()
    print(separador)
    print(f"RANKING DE CANDIDATOS  |  {titulo}")
    print(separador)
    print(f"{'#':<4}{'CANDIDATO':<{ancho_nombre + 4}}{'AFINIDAD':>10}")
    print("-" * (10 + ancho_nombre + 12))

    for posicion, (nombre, score) in enumerate(ranking, start=1):
        # Barra visual de 20 caracteres: ayuda a ver de un vistazo la distancia
        # entre el primero y el ultimo, que es lo que cuenta la historia.
        bloques = int(round(max(score, 0.0) * 20))
        barra = "#" * bloques + "." * (20 - bloques)
        print(f"{posicion:<4}{nombre:<{ancho_nombre + 4}}{score:>10.4f}  {barra}")

    print(separador)
    print(f"{len(ranking)} candidatos evaluados. Metrica: similitud coseno.")
    print()


def _resolver_oferta(argumento: str) -> Path:
    """Convierte el argumento del CLI en una ruta a un fichero de oferta.

    Se prueba primero tal cual (ruta absoluta o relativa al cwd) y, si ahi no
    hay nada, se busca dentro de la carpeta OFERTAS_DIR del .env, anclada a la
    raiz del proyecto y no al cwd. Asi vale tanto la ruta completa como el
    nombre suelto:  python match.py backend_python_senior.txt
    Tambien se prueba anadiendo la extension .txt, que es la unica que se usa.
    """
    carpeta = RAIZ / os.getenv("OFERTAS_DIR", "ofertas")

    candidatas = [
        Path(argumento),
        carpeta / argumento,
        carpeta / f"{argumento}.txt",
    ]
    for candidata in candidatas:
        if candidata.is_file():
            return candidata.resolve()

    print(f"ERROR: no se encontro la oferta '{argumento}'. Se busco en:")
    for candidata in candidatas:
        print(f"  - {candidata}")
    if carpeta.is_dir():
        disponibles = sorted(p.name for p in carpeta.glob("*.txt"))
        if disponibles:
            print(f"Ofertas disponibles en {carpeta}:")
            for nombre in disponibles:
                print(f"  - {nombre}")
    sys.exit(1)


def _leer_oferta() -> tuple[str, str]:
    """Lee la oferta de un .txt pasado como argumento o, si no, de stdin.

    Las dos vias fuerzan UTF-8 de forma explicita. En la via de fichero es obvio;
    en la de stdin no lo es tanto: en Windows `sys.stdin` se abre con la
    codificacion del sistema (aqui cp1252), asi que un texto UTF-8 llegado por
    tuberia se decodifica mal y produce mojibake SIN lanzar ninguna excepcion.
    El tokenizador acabaria viendo secuencias basura donde hay palabras en
    espanol y el score saldria distinto segun por donde entrase el mismo texto.
    Importa especialmente de cara al paso 6: n8n inyecta la oferta por tuberia.
    """
    if len(sys.argv) > 1:
        ruta = _resolver_oferta(sys.argv[1])
        return ruta.read_text(encoding="utf-8"), ruta.stem.replace("_", " ").title()

    print("Pega la descripcion de la oferta y termina con Ctrl+Z + Enter (Windows):")
    # Se leen los bytes crudos y se decodifican a mano en vez de usar
    # sys.stdin.reconfigure(): funciona igual venga la entrada de un TTY o de
    # una tuberia, y 'errors=replace' garantiza que un byte suelto invalido no
    # tumbe el proceso entero a mitad de un flujo de n8n.
    return sys.stdin.buffer.read().decode("utf-8", errors="replace"), "Oferta desde stdin"


if __name__ == "__main__":
    texto, titulo_oferta = _leer_oferta()

    if not texto.strip():
        print("ERROR: la oferta esta vacia, no hay nada que comparar.")
        sys.exit(1)

    resultado = rankear(texto, titulo=titulo_oferta)

    if not resultado:
        print("No hay candidatos con embedding en la base de datos.")
        print("Ejecuta antes embed_and_store.py para procesar la carpeta de CVs.")
        sys.exit(1)

    imprimir_ranking(resultado, titulo_oferta)
