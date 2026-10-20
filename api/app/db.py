"""Conexión a SQLite e inicialización de la base de datos.

Uso por consola:
    python -m app.db           # crea la BD si no existe
    python -m app.db --reset   # la borra y la vuelve a crear desde datos_prueba.sql
"""

import argparse
import sqlite3
from collections.abc import Iterator
from pathlib import Path

from app import config
from app.texto import normalizar


def conectar(ruta: Path | None = None) -> sqlite3.Connection:
    conn = sqlite3.connect(ruta or config.DATABASE_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    # lower() de SQLite solo entiende ASCII: "TÓNER" no coincidiría con "tóner".
    # Se registra una función propia para buscar sin mayúsculas ni tildes.
    conn.create_function("normalizar", 1, normalizar, deterministic=True)
    return conn


def get_db() -> Iterator[sqlite3.Connection]:
    """Dependencia de FastAPI: una conexión por petición."""
    conn = conectar()
    try:
        yield conn
    finally:
        conn.close()


def _aplicar_migraciones(conn: sqlite3.Connection) -> None:
    conn.execute("CREATE TABLE IF NOT EXISTS schema_migrations (nombre TEXT PRIMARY KEY)")
    aplicadas = {fila[0] for fila in conn.execute("SELECT nombre FROM schema_migrations")}
    for archivo in sorted(config.MIGRATIONS_DIR.glob("*.sql")):
        if archivo.name in aplicadas:
            continue
        conn.executescript(archivo.read_text(encoding="utf-8"))
        conn.execute("INSERT INTO schema_migrations (nombre) VALUES (?)", (archivo.name,))
        conn.commit()


def inicializar(ruta: Path | None = None, reset: bool = False) -> Path:
    ruta = Path(ruta or config.DATABASE_PATH)
    if reset and ruta.exists():
        ruta.unlink()
    nueva = not ruta.exists()
    ruta.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(ruta)
    try:
        if nueva:
            conn.executescript(config.SEED_SQL_PATH.read_text(encoding="utf-8"))
        _aplicar_migraciones(conn)
    finally:
        conn.close()
    return ruta


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Inicializa la base de datos SQLite")
    parser.add_argument("--reset", action="store_true", help="borra la BD y la recrea con los datos de prueba")
    args = parser.parse_args()
    print(f"Base de datos lista en {inicializar(reset=args.reset)}")
