import sqlite3

from fastapi import APIRouter, Depends, Query

from app.db import get_db
from app.errores import ApiError
from app.schemas import ErrorRespuesta, Producto, ProductoCoincidencia
from app.texto import UMBRAL_COINCIDENCIA, normalizar, puntaje

router = APIRouter(prefix="/productos", tags=["productos"])

COLUMNAS = "id, nombre, categoria, precio, stock"


@router.get("", response_model=list[Producto])
def buscar(
    q: str | None = Query(None, description="Texto parcial del nombre; sin q devuelve todo el catálogo"),
    db: sqlite3.Connection = Depends(get_db),
):
    """Búsqueda parcial por nombre, sin distinguir mayúsculas ni tildes."""
    if not q or not q.strip():
        filas = db.execute(f"SELECT {COLUMNAS} FROM productos ORDER BY nombre").fetchall()
    else:
        filas = db.execute(
            f"SELECT {COLUMNAS} FROM productos "
            "WHERE normalizar(nombre) LIKE '%' || normalizar(?) || '%' ORDER BY nombre",
            (q,),
        ).fetchall()
    return [dict(f) for f in filas]


@router.get(
    "/coincidencia",
    response_model=ProductoCoincidencia,
    responses={404: {"model": ErrorRespuesta}},
)
def mejor_coincidencia(
    texto: str = Query(min_length=2, description='Producto como lo escribió el cliente, p. ej. "resmas de papel"'),
    db: sqlite3.Connection = Depends(get_db),
):
    """Relaciona el texto libre del cliente con el producto más parecido del catálogo.

    Lo usa el flujo de n8n: el cliente puede escribir "resmas de papel" para
    "Resma papel carta". Devuelve 404 si ningún producto supera el umbral."""
    productos = [dict(f) for f in db.execute(f"SELECT {COLUMNAS} FROM productos").fetchall()]
    candidatos = sorted(
        ((puntaje(texto, p["nombre"]), p) for p in productos),
        key=lambda par: (-par[0], par[1]["id"]),
    )
    candidatos = [(s, p) for s, p in candidatos if s >= UMBRAL_COINCIDENCIA]
    if not candidatos:
        raise ApiError(404, "producto_no_encontrado", f"Ningún producto del catálogo coincide con '{normalizar(texto)}'")
    mejor_puntaje, mejor = candidatos[0]
    return {"producto": mejor, "puntaje": mejor_puntaje, "alternativas": [p for _, p in candidatos[1:4]]}
