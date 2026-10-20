"""Envía los 5 mensajes del Anexo B al webhook de n8n y guarda las respuestas como evidencia.

Uso (con la API y n8n corriendo):
    python flujo/probar_anexo_b.py [http://localhost:5678/webhook/solicitud]
"""

import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

WEBHOOK = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5678/webhook/solicitud"
SALIDA = Path(__file__).resolve().parent / "evidencias" / "anexo_b_respuestas.json"

MENSAJES = [
    ("compras@ferreteriaeltornillo.com",
     "Buenos días, necesitamos 10 resmas de papel carta para el viernes, es urgente."),
    ("compras@clinicalosandes.com",
     "Hola, ¿tienen diademas con micrófono? ¿Cuánto valen y en cuánto tiempo llegan?"),
    ("compras@oficinasmodernassas.com",
     "Es la segunda vez que el tóner llega dañado. Estamos muy molestos, necesitamos que nos respondan hoy mismo."),
    ("compras@constructorahorizonte.com",
     "Por favor despachar 6 escritorios en L para la nueva oficina de Rionegro."),
    ("juanperez.compras@gmail.com",
     "hola buenas q precio tienen los mouse inalambricos y si hacen envios"),
]


def enviar(email: str, mensaje: str) -> tuple[int, dict, float]:
    datos = json.dumps({"cliente_email": email, "mensaje": mensaje}).encode()
    peticion = urllib.request.Request(WEBHOOK, data=datos, method="POST", headers={"Content-Type": "application/json"})
    inicio = time.perf_counter()
    try:
        with urllib.request.urlopen(peticion, timeout=90) as r:
            return r.status, json.load(r), time.perf_counter() - inicio
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}"), time.perf_counter() - inicio


def main() -> None:
    evidencias = []
    for n, (email, mensaje) in enumerate(MENSAJES, 1):
        status, cuerpo, segundos = enviar(email, mensaje)
        evidencias.append({"n": n, "entrada": {"cliente_email": email, "mensaje": mensaje},
                           "http_status": status, "segundos": round(segundos, 2), "respuesta": cuerpo})
        c = cuerpo.get("clasificacion") or {}
        alertas = ", ".join(a["condicion"] for a in cuerpo.get("alertas", [])) or "ninguna"
        print(f"#{n} HTTP {status} id={cuerpo.get('id')} tipo={c.get('tipo')} producto={c.get('producto')} "
              f"cantidad={c.get('cantidad')} urgencia={c.get('urgencia')} sin_stock={cuerpo.get('sin_stock')} "
              f"alertas=[{alertas}] ({segundos:.1f}s)")
        time.sleep(1)  # margen para el límite por minuto del plan gratuito
    SALIDA.parent.mkdir(exist_ok=True)
    SALIDA.write_text(json.dumps(evidencias, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nGuardado en {SALIDA}")


if __name__ == "__main__":
    main()
