"""Modelos de entrada y salida (Pydantic). Definen la validación y el Swagger."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

Tipo = Literal["pedido", "consulta", "queja"]
Urgencia = Literal["baja", "media", "alta"]
Estado = Literal["pendiente", "en_proceso", "resuelta"]


class Cliente(BaseModel):
    id: int
    nombre: str
    ciudad: str
    email: str
    fecha_registro: str


class Producto(BaseModel):
    id: int
    nombre: str
    categoria: str
    precio: float
    stock: int


class ProductoCoincidencia(BaseModel):
    producto: Producto
    puntaje: float = Field(description="0 a 1; 1 es coincidencia exacta de palabras")
    alternativas: list[Producto] = Field(default_factory=list, description="otros candidatos sobre el umbral")


class SolicitudCrear(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [{
                "cliente_id": 1,
                "email_remitente": "compras@ferreteriaeltornillo.com",
                "producto_id": 1,
                "producto_texto": "resmas de papel carta",
                "tipo": "pedido",
                "cantidad": 10,
                "urgencia": "alta",
                "mensaje": "Buenos días, necesitamos 10 resmas de papel carta para el viernes, es urgente.",
                "resumen": "Pedido urgente de 10 resmas de papel carta para el viernes",
            }]
        },
    )

    cliente_id: int | None = Field(None, description="Obligatorio salvo que la solicitud requiera revisión")
    email_remitente: EmailStr | None = None
    producto_id: int | None = None
    producto_texto: str | None = Field(None, max_length=200)
    tipo: Tipo | None = Field(None, description="Obligatorio salvo que la solicitud requiera revisión")
    cantidad: int | None = Field(None, gt=0)
    urgencia: Urgencia | None = Field(None, description="Obligatorio salvo que la solicitud requiera revisión")
    mensaje: str = Field(min_length=1, max_length=5000)
    resumen: str | None = Field(None, max_length=300)
    requiere_revision: bool = False
    motivo_revision: str | None = Field(None, max_length=60)

    @field_validator("mensaje")
    @classmethod
    def mensaje_no_vacio(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("el mensaje no puede estar vacío")
        return v.strip()

    @model_validator(mode="after")
    def reglas_de_completitud(self):
        if self.requiere_revision:
            if not self.motivo_revision:
                raise ValueError("motivo_revision es obligatorio cuando requiere_revision es true")
            if self.cliente_id is None and self.email_remitente is None:
                raise ValueError("se necesita cliente_id o email_remitente para saber quién envió la solicitud")
        else:
            faltantes = [c for c in ("cliente_id", "tipo", "urgencia") if getattr(self, c) is None]
            if faltantes:
                raise ValueError(
                    f"campos obligatorios faltantes: {', '.join(faltantes)} "
                    "(solo pueden omitirse si requiere_revision es true)"
                )
        return self


class SolicitudActualizar(BaseModel):
    model_config = ConfigDict(extra="forbid")
    estado: Estado


class Solicitud(BaseModel):
    id: int
    cliente_id: int | None
    cliente_nombre: str | None
    email_remitente: str | None
    producto_id: int | None
    producto_nombre: str | None
    producto_texto: str | None
    tipo: Tipo | None
    cantidad: int | None
    urgencia: Urgencia | None
    estado: Estado
    mensaje: str
    resumen: str | None
    requiere_revision: bool
    motivo_revision: str | None
    fecha_creacion: datetime
    fecha_resolucion: datetime | None


class SolicitudCreada(Solicitud):
    sin_stock: bool = Field(description="true si es un pedido y la cantidad supera el stock del producto")
    stock_disponible: int | None = None


class PaginaSolicitudes(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[Solicitud]


class ErrorDetalle(BaseModel):
    campo: str | None = None
    mensaje: str


class ErrorRespuesta(BaseModel):
    error: str
    mensaje: str
    detalles: list[ErrorDetalle] = Field(default_factory=list)
