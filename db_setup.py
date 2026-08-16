"""Paso 2 del pipeline: esquema y conexion a MySQL.

Este modulo es la unica puerta de entrada a la base de datos. El resto de
scripts (embed_and_store.py, match.py) importan `conectar()` en vez de leer
el .env por su cuenta, para que las credenciales vivan en un solo sitio y
un cambio de puerto o password no obligue a tocar cuatro ficheros.

Decision cerrada del proyecto: el embedding se guarda en una columna JSON
(MySQL 8 no tiene tipo vector nativo) y la similitud se calcula en Python.
Por eso aqui no hay ni un solo indice pensado para busqueda vectorial.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import mysql.connector
from dotenv import load_dotenv

# load_dotenv() sin argumentos parte del directorio del archivo que la llama y
# puede acabar cargando otro .env (o ninguno). Ruta explicita siempre.
load_dotenv(Path(__file__).resolve().parent / ".env")


# Sentencias CREATE TABLE separadas para poder ejecutarlas de una en una y
# saber cual falla si algo va mal. El orden importa: 'matches' tiene claves
# foraneas hacia las otras dos, asi que va la ultima.
SENTENCIAS_CREATE: dict[str, str] = {
    "candidatos": """
        CREATE TABLE IF NOT EXISTS candidatos (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nombre VARCHAR(255) NOT NULL,
            archivo VARCHAR(255) NOT NULL UNIQUE,
            texto_cv MEDIUMTEXT,
            embedding JSON,
            fragmentos JSON,
            fecha_alta DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """,
    # 'huella' es el SHA-256 de la descripcion y es lo que identifica una oferta,
    # no el titulo. Se eligio asi porque el titulo no es fiable como identidad:
    # sale del nombre del fichero, y por stdin es siempre la misma cadena, de modo
    # que dos ofertas distintas acabarian pisandose. Con la huella, relanzar el
    # mismo texto actualiza su fila y un texto distinto crea una nueva. Sin esta
    # clave la tabla crecia una fila por ejecucion, que en el paso 6 (n8n
    # disparando el webhook repetidamente) significa crecimiento sin control.
    "puestos": """
        CREATE TABLE IF NOT EXISTS puestos (
            id INT AUTO_INCREMENT PRIMARY KEY,
            titulo VARCHAR(255) NOT NULL,
            descripcion MEDIUMTEXT,
            huella CHAR(64) NOT NULL UNIQUE,
            embedding JSON,
            fecha_alta DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """,
    "matches": """
        CREATE TABLE IF NOT EXISTS matches (
            id INT AUTO_INCREMENT PRIMARY KEY,
            candidato_id INT NOT NULL,
            puesto_id INT NOT NULL,
            score FLOAT NOT NULL,
            fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (candidato_id) REFERENCES candidatos(id) ON DELETE CASCADE,
            FOREIGN KEY (puesto_id) REFERENCES puestos(id) ON DELETE CASCADE,
            UNIQUE KEY uq_match (candidato_id, puesto_id)
        )
    """,
}


def conectar() -> mysql.connector.connection.MySQLConnection:
    """Abre una conexion a MySQL con las credenciales del .env.

    Traduce el error de conexion a un mensaje accionable: el fallo mas
    frecuente en este proyecto no es un bug del codigo, es que el contenedor
    Docker de MySQL esta parado. Un stacktrace crudo no ayuda a verlo.
    """
    parametros = {
        "host": os.getenv("MYSQL_HOST", "127.0.0.1"),
        "port": int(os.getenv("MYSQL_PORT", "3306")),
        "database": os.getenv("MYSQL_DATABASE", "candidatos"),
        "user": os.getenv("MYSQL_USER", "app"),
        "password": os.getenv("MYSQL_PASSWORD", ""),
    }

    try:
        return mysql.connector.connect(**parametros)
    except mysql.connector.Error as error:
        destino = f"{parametros['host']}:{parametros['port']}"
        mensaje = (
            f"No se pudo conectar a MySQL en {destino} "
            f"(base '{parametros['database']}', usuario '{parametros['user']}').\n"
            f"  Detalle de MySQL: {error.msg or error}\n"
            "  Comprobaciones habituales:\n"
            "    1. El contenedor esta levantado?  ->  docker compose up -d\n"
            "    2. Ver estado y logs             ->  docker ps | docker logs candidatos_mysql\n"
            "    3. Coinciden usuario/password/puerto con los del .env?"
        )
        # 'from None' para que la consola muestre el mensaje util y no el
        # stacktrace de mysql-connector, que aqui solo hace ruido.
        raise RuntimeError(mensaje) from None


# Columnas anadidas despues de la primera version del esquema. CREATE TABLE IF
# NOT EXISTS no toca una tabla que ya existe, asi que sin esto una base de datos
# creada con el esquema antiguo se queda sin la columna y falla al insertar.
COLUMNAS_NUEVAS: list[tuple[str, str, str]] = [
    ("candidatos", "fragmentos", "ADD COLUMN fragmentos JSON AFTER embedding"),
]


def _migrar(cursor) -> None:
    """Anade las columnas que falten. Idempotente: consulta antes de tocar nada."""
    for tabla, columna, sentencia in COLUMNAS_NUEVAS:
        cursor.execute(
            """
            SELECT COUNT(*) FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = %s AND COLUMN_NAME = %s
            """,
            (tabla, columna),
        )
        if cursor.fetchone()[0] == 0:
            cursor.execute(f"ALTER TABLE {tabla} {sentencia}")
            print(f"  [migracion] '{tabla}.{columna}' anadida")


def crear_tablas() -> None:
    """Crea las tres tablas si no existen. Idempotente: se puede repetir."""
    conexion = conectar()
    try:
        cursor = conexion.cursor()
        for nombre, sentencia in SENTENCIAS_CREATE.items():
            cursor.execute(sentencia)
            print(f"  [ok] tabla '{nombre}' lista")
        _migrar(cursor)
        conexion.commit()
        cursor.close()
    finally:
        conexion.close()


def describir_tablas() -> None:
    """Imprime el DESCRIBE de cada tabla para verificar el esquema a ojo."""
    conexion = conectar()
    try:
        cursor = conexion.cursor()
        for nombre in SENTENCIAS_CREATE:
            cursor.execute(f"DESCRIBE {nombre}")
            filas = cursor.fetchall()
            cabeceras = [c[0] for c in cursor.description]

            print(f"\nDESCRIBE {nombre}")
            print("-" * 78)
            print(formatear_fila(cabeceras))
            for fila in filas:
                print(formatear_fila(fila))
        cursor.close()
    finally:
        conexion.close()


def formatear_fila(valores) -> str:
    """Alinea en columnas fijas para que el DESCRIBE se lea sin esfuerzo."""
    anchos = (18, 14, 6, 6, 10, 16)
    partes = []
    for valor, ancho in zip(valores, anchos):
        texto = "NULL" if valor is None else str(valor)
        partes.append(texto.ljust(ancho))
    return " ".join(partes).rstrip()


if __name__ == "__main__":
    print("Paso 2 - Esquema y conexion MySQL")
    print("=" * 78)
    try:
        crear_tablas()
        describir_tablas()
    except RuntimeError as error:
        print(f"\nERROR: {error}", file=sys.stderr)
        sys.exit(1)

    print("\nEsquema creado/verificado correctamente.")
