"""Paso 6 (capa de servicio): expone el pipeline por HTTP para que n8n lo llame.

Esta capa NO implementa logica de negocio. Es un traductor entre HTTP y las
funciones de los pasos 1-4, que ya estan probadas de forma aislada. Si se borra
este fichero, el pipeline sigue funcionando por linea de comandos exactamente
igual: esa es la prueba de que la separacion esta bien hecha.

Por que un servicio permanente y no un script que n8n lance por cada peticion:
cargar el modelo de embeddings tarda varios segundos. Como proceso que se queda
encendido se paga una sola vez, al arrancar; lanzando un Python nuevo por
peticion se pagaria siempre.

Arranque:
    .venv\\Scripts\\python.exe -m uvicorn api:app --host 127.0.0.1 --port 8000

Sin autenticacion a proposito: corre en local y no se expone a internet. En un
despliegue real llevaria un token por cabecera; queda anotado en el README como
decision consciente y no como olvido.
"""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from db_setup import conectar, crear_tablas
from embed_and_store import cargar_modelo, procesar_pdf
from extract_text import CVS_DIR
from match import rankear_detallado

app = FastAPI(
    title="Recomendador de candidatos",
    description="Capa HTTP sobre el pipeline de embeddings. Consumida por n8n.",
    version="1.0.0",
)


class PeticionMatch(BaseModel):
    """Cuerpo del POST /match."""

    texto: str = Field(..., description="Descripcion completa de la oferta.")
    titulo: str = Field("Oferta via API", description="Nombre para la tabla 'puestos'.")
    top: int | None = Field(None, description="Devolver solo los N mejores.")
    guardar: bool = Field(True, description="False para probar sin tocar la BD.")


@app.on_event("startup")
def preparar() -> None:
    """Crea el esquema y precarga el modelo ANTES de atender la primera peticion.

    Sin esto, quien hiciera la primera llamada se comeria los segundos de carga
    del modelo y podria interpretarlo como que el servicio va lento.
    """
    crear_tablas()
    cargar_modelo()
    print("[api] Modelo y esquema listos. Servicio disponible.")


@app.get("/salud")
def salud() -> dict:
    """Comprobacion rapida de que la API, MySQL y el modelo responden.

    Util como primer nodo de diagnostico en n8n: si esto falla, el problema esta
    aqui abajo y no en el flujo.
    """
    conn = conectar()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM candidatos WHERE embedding IS NOT NULL")
        total = cursor.fetchone()[0]
        cursor.close()
    finally:
        conn.close()

    return {
        "estado": "ok",
        "candidatos_indexados": total,
        "dimension_embedding": cargar_modelo().get_sentence_embedding_dimension(),
    }


@app.post("/candidatos")
async def alta_candidato(archivo: UploadFile = File(...)) -> dict:
    """Flujo A: recibe un PDF, lo indexa y lo deja disponible para el ranking.

    El PDF se guarda en la carpeta de CVs del proyecto para que quede el original
    junto a los demas, no solo su texto en la base de datos. El nombre de fichero
    es la clave unica de 'candidatos', asi que resubir el mismo CV actualiza al
    candidato en vez de duplicarlo.
    """
    if not archivo.filename or not archivo.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Se esperaba un archivo .pdf")

    CVS_DIR.mkdir(parents=True, exist_ok=True)
    destino = CVS_DIR / Path(archivo.filename).name

    # Se escribe primero en un temporal y solo despues se mueve al destino: si el
    # PDF llega corrupto o la subida se corta, no se queda un fichero a medias en
    # la carpeta de CVs haciendose pasar por un candidato valido.
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temporal:
        shutil.copyfileobj(archivo.file, temporal)
        ruta_temporal = Path(temporal.name)

    try:
        shutil.move(str(ruta_temporal), destino)
        datos = procesar_pdf(destino)
    except ValueError as error:
        # PDF sin texto extraible: es culpa del fichero enviado, no del servidor.
        destino.unlink(missing_ok=True)
        raise HTTPException(422, str(error)) from None
    finally:
        ruta_temporal.unlink(missing_ok=True)

    return {"ok": True, **datos}


@app.get("/candidatos")
def listar_candidatos() -> dict:
    """Devuelve los candidatos indexados, sin el texto completo.

    Se omite 'texto_cv' a proposito: son varios miles de caracteres por
    candidato y quien pinta una lista no los necesita. El texto se pide aparte,
    solo del candidato que se abra.
    """
    conn = conectar()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, nombre, archivo, CHAR_LENGTH(texto_cv), fecha_alta
            FROM candidatos
            ORDER BY nombre
            """
        )
        filas = cursor.fetchall()
        cursor.close()
    finally:
        conn.close()

    return {
        "total": len(filas),
        "candidatos": [
            {
                "id": id_candidato,
                "nombre": nombre,
                "archivo": archivo,
                "caracteres": caracteres or 0,
                "fecha_alta": fecha.isoformat() if fecha else None,
            }
            for id_candidato, nombre, archivo, caracteres, fecha in filas
        ],
    }


@app.get("/candidatos/{candidato_id}")
def detalle_candidato(candidato_id: int) -> dict:
    """Devuelve un candidato con el texto que se extrajo de su PDF.

    Este texto es exactamente lo que se convirtio en vector: es la forma de ver
    que 'lee' el sistema y de detectar a ojo un PDF mal extraido (columnas
    entrelazadas, acentos partidos) antes de culpar al ranking.
    """
    conn = conectar()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, nombre, archivo, texto_cv, fecha_alta,
                   embedding IS NOT NULL
            FROM candidatos WHERE id = %s
            """,
            (candidato_id,),
        )
        fila = cursor.fetchone()
        cursor.close()
    finally:
        conn.close()

    if fila is None:
        raise HTTPException(404, f"No existe el candidato {candidato_id}")

    id_candidato, nombre, archivo, texto, fecha, tiene_embedding = fila
    return {
        "id": id_candidato,
        "nombre": nombre,
        "archivo": archivo,
        "texto": texto or "",
        "caracteres": len(texto or ""),
        "fecha_alta": fecha.isoformat() if fecha else None,
        "indexado": bool(tiene_embedding),
        "pdf_disponible": (CVS_DIR / archivo).is_file(),
    }


@app.get("/candidatos/{candidato_id}/pdf")
def pdf_candidato(candidato_id: int) -> FileResponse:
    """Sirve el PDF original del candidato.

    El nombre de fichero sale de la base de datos, pero igualmente se comprueba
    que la ruta resuelta cae DENTRO de la carpeta de CVs: si algun dia entrase
    un nombre con '..' por otra via, esto impide que la API acabe sirviendo
    ficheros arbitrarios del disco.
    """
    conn = conectar()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT archivo FROM candidatos WHERE id = %s", (candidato_id,))
        fila = cursor.fetchone()
        cursor.close()
    finally:
        conn.close()

    if fila is None:
        raise HTTPException(404, f"No existe el candidato {candidato_id}")

    ruta = (CVS_DIR / fila[0]).resolve()
    if CVS_DIR.resolve() not in ruta.parents:
        raise HTTPException(400, "Ruta de archivo no permitida.")
    if not ruta.is_file():
        raise HTTPException(
            404,
            f"El candidato existe en la base de datos pero su PDF ya no esta en "
            f"{CVS_DIR}. El texto extraido sigue disponible.",
        )

    return FileResponse(ruta, media_type="application/pdf", filename=ruta.name)


@app.post("/match")
def calcular_match(peticion: PeticionMatch) -> dict:
    """Flujo B: recibe el texto de una oferta y devuelve el ranking de candidatos.

    Devuelve la posicion explicita ademas del orden de la lista porque n8n
    manipula los elementos de uno en uno y ahi el indice del array se pierde.
    """
    if not peticion.texto.strip():
        raise HTTPException(400, "El campo 'texto' esta vacio, no hay nada que comparar.")

    ranking = rankear_detallado(
        peticion.texto, titulo=peticion.titulo, guardar=peticion.guardar
    )
    if not ranking:
        raise HTTPException(
            409,
            "No hay candidatos con embedding en la base de datos. "
            "Da de alta alguno por POST /candidatos o ejecuta embed_and_store.py.",
        )

    if peticion.top is not None:
        ranking = ranking[: max(peticion.top, 1)]

    return {
        "titulo": peticion.titulo,
        "total_candidatos": len(ranking),
        "ranking": [
            {
                "posicion": posicion,
                "candidato": fila["nombre"],
                # Los dos scores viajan juntos a proposito. 'score' es el coseno
                # puro y 'score_ajustado' el que decide el orden: separarlos
                # permite ver que parte de la puntuacion es afinidad semantica y
                # que parte es correccion por requisitos no cumplidos. Con un
                # unico numero ya corregido esa distincion se perderia.
                "score": round(fila["score"], 4),
                "score_ajustado": round(fila["score_ajustado"], 4),
                "penalizacion": fila["penalizacion"],
                # Por que ha bajado, en lenguaje legible. Lista vacia si cumple
                # todo lo que la oferta exige, o si su CV no declara el dato.
                "avisos": fila["avisos"],
                # El trozo del CV mas afin a esta oferta. No interviene en la
                # puntuacion: sirve para poder comprobar de un vistazo si el
                # sistema tiene razon, en vez de tener que creerse el numero.
                "extracto": fila["extracto"],
            }
            for posicion, fila in enumerate(ranking, start=1)
        ],
    }
