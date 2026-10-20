"""API REST de Suministros Andinos SAS.

Ejecutar desde la carpeta api/:  uvicorn app.main:app --reload
Documentación interactiva:       http://localhost:8000/docs
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import db
from app.errores import registrar_manejadores
from app.routers import clientes, productos, solicitudes

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(_: FastAPI):
    db.inicializar()  # crea la BD desde datos_prueba.sql la primera vez
    yield


app = FastAPI(
    title="Suministros Andinos - API de solicitudes",
    description="Clientes, catálogo y solicitudes clasificadas por IA (prueba técnica).",
    version="1.0.0",
    lifespan=lifespan,
)
registrar_manejadores(app)

app.include_router(clientes.router)
app.include_router(productos.router)
app.include_router(solicitudes.router)


@app.get("/salud", tags=["sistema"])
def salud():
    return {"estado": "ok"}
