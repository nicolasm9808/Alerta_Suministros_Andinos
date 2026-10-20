import sqlite3

from fastapi import APIRouter, Depends, Query

from app.db import get_db
from app.errores import ApiError
from app.schemas import Cliente, ErrorRespuesta

router = APIRouter(prefix="/clientes", tags=["clientes"])


@router.get("", response_model=Cliente, responses={404: {"model": ErrorRespuesta}})
def buscar_por_email(
    email: str = Query(min_length=3, description="Correo del cliente (no distingue mayúsculas)"),
    db: sqlite3.Connection = Depends(get_db),
):
    fila = db.execute(
        "SELECT id, nombre, ciudad, email, fecha_registro FROM clientes WHERE lower(email) = lower(?)",
        (email.strip(),),
    ).fetchone()
    if fila is None:
        raise ApiError(404, "cliente_no_encontrado", f"No existe un cliente con el correo {email.strip()}")
    return dict(fila)
