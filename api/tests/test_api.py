import pytest
from fastapi.testclient import TestClient

from app import config
from app.main import app
from app.texto import puntaje


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Cada prueba corre sobre una BD nueva creada desde datos_prueba.sql."""
    monkeypatch.setattr(config, "DATABASE_PATH", tmp_path / "prueba.db")
    with TestClient(app) as c:
        yield c


def pedido(**cambios):
    base = {
        "cliente_id": 10,
        "email_remitente": "compras@constructorahorizonte.com",
        "producto_id": 4,
        "tipo": "pedido",
        "cantidad": 2,
        "urgencia": "media",
        "mensaje": "Por favor despachar escritorios en L",
    }
    return {**base, **cambios}


# --- clientes y productos -------------------------------------------------

def test_cliente_por_email_sin_distinguir_mayusculas(client):
    r = client.get("/clientes", params={"email": "  COMPRAS@FerreteriaElTornillo.com "})
    assert r.status_code == 200
    assert r.json()["nombre"] == "Ferretería El Tornillo"


def test_cliente_inexistente_devuelve_404_en_json(client):
    r = client.get("/clientes", params={"email": "juanperez.compras@gmail.com"})
    assert r.status_code == 404
    assert r.json()["error"] == "cliente_no_encontrado"


def test_productos_busqueda_parcial_sin_mayusculas_ni_tildes(client):
    r = client.get("/productos", params={"q": "TONER"})
    assert r.status_code == 200
    assert [p["nombre"] for p in r.json()] == ["Tóner HP 85A"]
    assert r.json()[0]["stock"] == 12


@pytest.mark.parametrize("texto, esperado", [
    ("resmas de papel", "Resma papel carta"),
    ("escritorios en L", "Escritorio en L"),
    ("mouse inalambricos", "Mouse inalámbrico"),
    ("diademas con micrófono", "Diadema con micrófono"),
    ("tóner", "Tóner HP 85A"),
])
def test_coincidencia_de_producto_con_texto_libre(client, texto, esperado):
    r = client.get("/productos/coincidencia", params={"texto": texto})
    assert r.status_code == 200
    assert r.json()["producto"]["nombre"] == esperado


def test_coincidencia_sin_producto_devuelve_404(client):
    r = client.get("/productos/coincidencia", params={"texto": "impresora láser"})
    assert r.status_code == 404


def test_puntaje_prefiere_el_producto_correcto():
    assert puntaje("resmas de papel", "Resma papel carta") > puntaje("resmas de papel", "Caja de esferos x12")


# --- POST /solicitudes ----------------------------------------------------

def test_crear_solicitud_queda_pendiente(client):
    r = client.post("/solicitudes", json=pedido())
    assert r.status_code == 201
    cuerpo = r.json()
    assert cuerpo["estado"] == "pendiente"
    assert cuerpo["id"] == 61
    assert cuerpo["cliente_nombre"] == "Constructora Horizonte"
    assert cuerpo["sin_stock"] is False


def test_pedido_que_supera_stock_marca_sin_stock_y_se_guarda(client):
    r = client.post("/solicitudes", json=pedido(cantidad=6))  # stock del escritorio en L = 3
    assert r.status_code == 201
    assert r.json()["sin_stock"] is True
    assert r.json()["stock_disponible"] == 3
    assert client.get(f"/solicitudes/{r.json()['id']}").status_code == 200


def test_consulta_nunca_es_sin_stock(client):
    r = client.post("/solicitudes", json=pedido(tipo="consulta", producto_id=11, cantidad=None))
    assert r.json()["sin_stock"] is False


@pytest.mark.parametrize("cambio, campo", [
    ({"tipo": "reclamo"}, "tipo"),
    ({"urgencia": "urgente"}, "urgencia"),
    ({"cantidad": 0}, "cantidad"),
    ({"mensaje": "   "}, "mensaje"),
])
def test_valores_no_permitidos_devuelven_422(client, cambio, campo):
    r = client.post("/solicitudes", json=pedido(**cambio))
    assert r.status_code == 422
    assert r.json()["error"] == "validacion"
    assert any(d["campo"] == campo for d in r.json()["detalles"])


def test_campos_obligatorios_sin_revision(client):
    datos = pedido()
    del datos["tipo"]
    r = client.post("/solicitudes", json=datos)
    assert r.status_code == 422
    assert "tipo" in r.json()["detalles"][0]["mensaje"]


def test_cliente_inexistente_en_post_devuelve_422(client):
    r = client.post("/solicitudes", json=pedido(cliente_id=999))
    assert r.status_code == 422


def test_solicitud_para_revision_manual_sin_cliente_ni_clasificacion(client):
    r = client.post("/solicitudes", json={
        "email_remitente": "juanperez.compras@gmail.com",
        "mensaje": "hola buenas q precio tienen los mouse",
        "requiere_revision": True,
        "motivo_revision": "llm_invalido",
    })
    assert r.status_code == 201
    assert r.json()["requiere_revision"] is True
    assert r.json()["tipo"] is None


# --- GET /solicitudes -----------------------------------------------------

def test_listar_con_filtros_y_paginacion(client):
    r = client.get("/solicitudes", params={"tipo": "queja", "estado": "pendiente", "limit": 2})
    cuerpo = r.json()
    assert r.status_code == 200
    assert cuerpo["total"] == 2  # solicitudes 2 y 56
    assert {s["id"] for s in cuerpo["items"]} == {2, 56}

    pagina2 = client.get("/solicitudes", params={"limit": 50, "offset": 50}).json()
    assert pagina2["total"] == 60 and len(pagina2["items"]) == 10


def test_filtro_invalido_devuelve_422(client):
    assert client.get("/solicitudes", params={"estado": "cerrada"}).status_code == 422


def test_detalle_incluye_nombres(client):
    r = client.get("/solicitudes/2")
    assert r.json()["cliente_nombre"] == "Ferretería El Tornillo"
    assert r.json()["producto_nombre"] == "Escritorio en L"
    assert client.get("/solicitudes/9999").status_code == 404


# --- PATCH /solicitudes/{id} ----------------------------------------------

def test_resolver_registra_fecha_de_resolucion(client):
    r = client.patch("/solicitudes/1", json={"estado": "resuelta"})
    assert r.status_code == 200
    assert r.json()["estado"] == "resuelta"
    assert r.json()["fecha_resolucion"] is not None


def test_resuelta_no_vuelve_a_pendiente(client):
    r = client.patch("/solicitudes/3", json={"estado": "pendiente"})  # la 3 ya está resuelta
    assert r.status_code == 409
    assert r.json()["error"] == "transicion_no_permitida"
    assert client.get("/solicitudes/3").json()["estado"] == "resuelta"


def test_reabrir_resuelta_a_en_proceso_borra_fecha(client):
    r = client.patch("/solicitudes/3", json={"estado": "en_proceso"})
    assert r.status_code == 200
    assert r.json()["fecha_resolucion"] is None


def test_patch_estado_invalido_y_solicitud_inexistente(client):
    assert client.patch("/solicitudes/1", json={"estado": "cerrada"}).status_code == 422
    assert client.patch("/solicitudes/9999", json={"estado": "resuelta"}).status_code == 404
