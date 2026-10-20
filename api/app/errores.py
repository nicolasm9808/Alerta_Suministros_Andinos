"""Formato único de errores: {"error": "<codigo>", "mensaje": "...", "detalles": [...]}."""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

log = logging.getLogger("api")


class ApiError(Exception):
    def __init__(self, status: int, codigo: str, mensaje: str, detalles: list[dict] | None = None):
        self.status, self.codigo, self.mensaje, self.detalles = status, codigo, mensaje, detalles or []


def _respuesta(status: int, codigo: str, mensaje: str, detalles: list[dict] | None = None) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": codigo, "mensaje": mensaje, "detalles": detalles or []})


def _traducir(err: dict) -> str:
    """Mensajes de Pydantic en español para los casos frecuentes."""
    tipo, ctx = err.get("type", ""), err.get("ctx") or {}
    if tipo == "missing":
        return "campo obligatorio"
    if tipo == "literal_error":
        return f"valor no permitido; opciones válidas: {ctx.get('expected', '')}"
    if tipo == "extra_forbidden":
        return "campo no reconocido"
    if tipo in ("int_parsing", "int_type"):
        return "debe ser un número entero"
    if tipo == "greater_than":
        return f"debe ser mayor que {ctx.get('gt')}"
    if tipo in ("string_too_short", "string_too_long"):
        return err["msg"].replace("String should have", "debe tener").replace("characters", "caracteres")
    if tipo == "value_error":
        return err["msg"].removeprefix("Value error, ")
    return err["msg"]


def registrar_manejadores(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def _api_error(_: Request, exc: ApiError):
        return _respuesta(exc.status, exc.codigo, exc.mensaje, exc.detalles)

    @app.exception_handler(RequestValidationError)
    async def _validacion(_: Request, exc: RequestValidationError):
        detalles = []
        for err in exc.errors():
            loc = [str(p) for p in err["loc"] if p not in ("body", "query", "path")]
            detalles.append({"campo": ".".join(loc) or None, "mensaje": _traducir(err)})
        return _respuesta(422, "validacion", "La petición tiene datos inválidos", detalles)

    @app.exception_handler(StarletteHTTPException)
    async def _http(_: Request, exc: StarletteHTTPException):
        codigo = {404: "no_encontrado", 405: "metodo_no_permitido"}.get(exc.status_code, "error_http")
        mensaje = "Recurso no encontrado" if exc.status_code == 404 else str(exc.detail)
        return _respuesta(exc.status_code, codigo, mensaje)

    @app.exception_handler(Exception)
    async def _inesperado(_: Request, exc: Exception):
        log.exception("Error no controlado")
        return _respuesta(500, "error_interno", "Ocurrió un error inesperado en el servidor")
