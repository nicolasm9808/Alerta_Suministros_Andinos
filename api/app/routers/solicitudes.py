import sqlite3
from datetime import datetime

from fastapi import APIRouter, Depends, Query

from app import config
from app.db import get_db
from app.errores import ApiError
from app.schemas import (
    ErrorRespuesta,
    Estado,
    PaginaSolicitudes,
    Solicitud,
    SolicitudActualizar,
    SolicitudCrear,
    SolicitudCreada,
    Tipo,
    Urgencia,
)

router = APIRouter(prefix="/solicitudes", tags=["solicitudes"])

SELECT_DETALLE = """
    SELECT s.id, s.cliente_id, c.nombre AS cliente_nombre, s.email_remitente,
           s.producto_id, p.nombre AS producto_nombre, s.producto_texto,
           s.tipo, s.cantidad, s.urgencia, s.estado, s.mensaje, s.resumen,
           s.requiere_revision, s.motivo_revision, s.fecha_creacion, s.fecha_resolucion
    FROM solicitudes AS s
    LEFT JOIN clientes  AS c ON c.id = s.cliente_id
    LEFT JOIN productos AS p ON p.id = s.producto_id
"""

ERRORES_404 = {404: {"model": ErrorRespuesta}}


def _ahora() -> str:
    return datetime.now(config.ZONA_HORARIA).strftime("%Y-%m-%d %H:%M:%S")


def _obtener(db: sqlite3.Connection, solicitud_id: int) -> dict:
    fila = db.execute(SELECT_DETALLE + " WHERE s.id = ?", (solicitud_id,)).fetchone()
    if fila is None:
        raise ApiError(404, "solicitud_no_encontrada", f"No existe la solicitud {solicitud_id}")
    return dict(fila)


@router.post(
    "",
    status_code=201,
    response_model=SolicitudCreada,
    responses={422: {"model": ErrorRespuesta}},
)
def crear(datos: SolicitudCrear, db: sqlite3.Connection = Depends(get_db)):
    """Crea una solicitud en estado `pendiente`.

    Si es un pedido y la cantidad supera el stock del producto, responde
    `sin_stock: true`; la solicitud se guarda de todas formas."""
    if datos.cliente_id is not None and not db.execute(
        "SELECT 1 FROM clientes WHERE id = ?", (datos.cliente_id,)
    ).fetchone():
        raise ApiError(422, "validacion", "La petición tiene datos inválidos",
                       [{"campo": "cliente_id", "mensaje": f"no existe el cliente {datos.cliente_id}"}])

    stock = None
    if datos.producto_id is not None:
        fila = db.execute("SELECT stock FROM productos WHERE id = ?", (datos.producto_id,)).fetchone()
        if fila is None:
            raise ApiError(422, "validacion", "La petición tiene datos inválidos",
                           [{"campo": "producto_id", "mensaje": f"no existe el producto {datos.producto_id}"}])
        stock = fila["stock"]

    cursor = db.execute(
        """
        INSERT INTO solicitudes (cliente_id, email_remitente, producto_id, producto_texto, tipo,
                                 cantidad, urgencia, estado, mensaje, resumen,
                                 requiere_revision, motivo_revision, fecha_creacion)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'pendiente', ?, ?, ?, ?, ?)
        """,
        (
            datos.cliente_id, datos.email_remitente, datos.producto_id, datos.producto_texto, datos.tipo,
            datos.cantidad, datos.urgencia, datos.mensaje, datos.resumen,
            int(datos.requiere_revision), datos.motivo_revision, _ahora(),
        ),
    )
    db.commit()

    sin_stock = (
        datos.tipo == "pedido" and stock is not None and datos.cantidad is not None and datos.cantidad > stock
    )
    return {**_obtener(db, cursor.lastrowid), "sin_stock": sin_stock, "stock_disponible": stock}


@router.get("", response_model=PaginaSolicitudes)
def listar(
    tipo: Tipo | None = None,
    estado: Estado | None = None,
    urgencia: Urgencia | None = None,
    requiere_revision: bool | None = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: sqlite3.Connection = Depends(get_db),
):
    """Lista solicitudes, de la más reciente a la más antigua."""
    filtros, params = [], []
    for columna, valor in (("tipo", tipo), ("estado", estado), ("urgencia", urgencia)):
        if valor is not None:
            filtros.append(f"s.{columna} = ?")
            params.append(valor)
    if requiere_revision is not None:
        filtros.append("s.requiere_revision = ?")
        params.append(int(requiere_revision))
    where = (" WHERE " + " AND ".join(filtros)) if filtros else ""

    total = db.execute(f"SELECT COUNT(*) FROM solicitudes AS s{where}", params).fetchone()[0]
    filas = db.execute(
        SELECT_DETALLE + where + " ORDER BY s.fecha_creacion DESC, s.id DESC LIMIT ? OFFSET ?",
        [*params, limit, offset],
    ).fetchall()
    return {"total": total, "limit": limit, "offset": offset, "items": [dict(f) for f in filas]}


@router.get("/{solicitud_id}", response_model=Solicitud, responses=ERRORES_404)
def detalle(solicitud_id: int, db: sqlite3.Connection = Depends(get_db)):
    return _obtener(db, solicitud_id)


@router.patch(
    "/{solicitud_id}",
    response_model=Solicitud,
    responses={**ERRORES_404, 409: {"model": ErrorRespuesta}},
)
def cambiar_estado(solicitud_id: int, cambio: SolicitudActualizar, db: sqlite3.Connection = Depends(get_db)):
    """Cambia el estado de una solicitud.

    * Al pasar a `resuelta` se registra la fecha de resolución.
    * Una solicitud `resuelta` no puede volver a `pendiente` (409).
    * `resuelta` → `en_proceso` se permite como reapertura y borra la fecha de resolución."""
    actual = _obtener(db, solicitud_id)
    nuevo = cambio.estado
    if nuevo == actual["estado"]:
        return actual  # idempotente: no reescribe la fecha de resolución

    if actual["estado"] == "resuelta" and nuevo == "pendiente":
        raise ApiError(409, "transicion_no_permitida", "Una solicitud resuelta no puede volver a pendiente")

    fecha_resolucion = _ahora() if nuevo == "resuelta" else None
    db.execute(
        "UPDATE solicitudes SET estado = ?, fecha_resolucion = ? WHERE id = ?",
        (nuevo, fecha_resolucion, solicitud_id),
    )
    db.commit()
    return _obtener(db, solicitud_id)
