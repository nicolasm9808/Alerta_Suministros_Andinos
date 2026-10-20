"""Configuración leída de variables de entorno (.env en la raíz del repo)."""

import os
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

API_DIR = Path(__file__).resolve().parent.parent
REPO_DIR = API_DIR.parent

load_dotenv(REPO_DIR / ".env")


def _ruta(variable: str, por_defecto: Path) -> Path:
    """Las rutas relativas del .env se toman desde la raíz del repo, no desde donde se ejecute."""
    ruta = Path(os.getenv(variable) or por_defecto)
    return ruta if ruta.is_absolute() else REPO_DIR / ruta


DATABASE_PATH = _ruta("DATABASE_PATH", API_DIR / "data" / "suministros.db")
SEED_SQL_PATH = _ruta("SEED_SQL_PATH", REPO_DIR / "sql" / "datos_prueba.sql")
MIGRATIONS_DIR = API_DIR / "migrations"

# Los datos de ejemplo están en hora local de Colombia; las fechas nuevas se guardan igual.
ZONA_HORARIA = ZoneInfo(os.getenv("TZ_NEGOCIO", "America/Bogota"))
