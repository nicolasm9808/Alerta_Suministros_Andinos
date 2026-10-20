# Suministros Andinos: gestión de solicitudes con IA

Prototipo que recibe solicitudes en texto libre, las clasifica con un LLM, las relaciona con clientes y productos,
las registra en una base SQL a través de una API propia y avisa por Telegram cuando algo necesita atención.

```
 POST /webhook/solicitud                                   Telegram
 {cliente_email, mensaje}                                  (alertas)
          │                                                    ▲
          ▼                                                    │
 ┌──────────────────────────┐   HTTP    ┌──────────────────────┴──┐
 │ n8n (Ejercicio 1)        │ ────────▶ │ API FastAPI (Ejercicio 2)│
 │ valida → Gemini → valida │           │ /clientes /productos     │
 │ → reintenta → asocia     │           │ /solicitudes             │
 │ → registra → alerta      │           └────────────┬────────────┘
 └────────────┬─────────────┘                        ▼
              ▼                               SQLite (Ejercicio 3)
   Gemini 3.5 Flash-Lite (JSON con schema)
```

| Ejercicio | Dónde | Estado |
|---|---|---|
| 1. Flujo n8n con IA | [`flujo/`](flujo/), [`prompts/clasificador.md`](prompts/clasificador.md) | Completo y probado de punta a punta |
| 2. API REST | [`api/`](api/) | Completo, 27 pruebas con pytest |
| 3. Consultas SQL | [`sql/consultas.sql`](sql/consultas.sql), [resultados](sql/resultados_consultas.md) | Completo |
| 4. Prompt y agentes | [`prompts/`](prompts/) | Completo, probado con Gemini |
| Bonus: despliegue | [`docker-compose.yml`](docker-compose.yml), [`deploy/`](deploy/), [`bonus/`](bonus/) | **Desplegado en Google Cloud con HTTPS** |

## Demo en línea

Desplegado en una VM de Google Cloud (e2-small, Ubuntu 24.04) con Docker Compose y HTTPS automático (Caddy):

| Qué | URL |
|---|---|
| API: documentación Swagger | <https://api.34-26-7-154.sslip.io/docs> |
| API: ejemplo | <https://api.34-26-7-154.sslip.io/clientes?email=compras@ferreteriaeltornillo.com> |
| Webhook del flujo | `POST https://n8n.34-26-7-154.sslip.io/webhook/solicitud` |

```bash
curl -X POST https://n8n.34-26-7-154.sslip.io/webhook/solicitud -H 'Content-Type: application/json' \
  -d '{"cliente_email":"compras@oficinasmodernassas.com","mensaje":"Es la segunda vez que el tóner llega dañado."}'
```

Las alertas llegan al bot de Telegram `@alertas_suministros_andinos_bot` (al chat configurado). El editor de n8n no
se expone a internet: se accede por túnel SSH (ver [`bonus/README.md`](bonus/README.md)).

## Estructura

```
api/                  API FastAPI (Ejercicio 2)
  app/                  main, routers, esquemas, BD, emparejamiento de productos
  migrations/           001_campos_ia.sql: columnas nuevas (ver "Cambios al modelo de datos")
  tests/                pytest
  openapi.json          especificación OpenAPI exportada
flujo/                Ejercicio 1
  flujo_solicitudes.json      flujo principal (importar en n8n)
  flujo_alertas_error.json    flujo de respaldo (Error Trigger → Telegram)
  configurar_n8n.sh           importa credenciales y flujos en un n8n local
  probar_anexo_b.py           envía los 5 mensajes del Anexo B y guarda la evidencia
  evidencias/                 respuestas y capturas
sql/
  datos_prueba.sql      datos entregados (sin modificar)
  consultas.sql         las 6 consultas + inconsistencias encontradas
  ejecutar_consultas.py corre las consultas y muestra los resultados
prompts/
  clasificador.md       prompt del flujo y por qué está diseñado así
  chatbot_sistema.md    prompt del chatbot (Parte A)
  probar_chatbot.py     corre el chatbot contra Gemini con el Anexo C
  pruebas_chatbot.md    resultados y ajustes (Parte B)
  respuestas.md         preguntas conceptuales (Parte C)
bonus/                notas del despliegue con Docker
docker-compose.yml    API + n8n
.env.example
```

## Cómo ejecutarlo

Requisitos: Python 3.11+ y Node.js 24+ (para n8n), o solo Docker (paso 6). Probado en Ubuntu 24.04 con Python 3.12,
Node 24, n8n 2.43.8 y Docker 29.9 / Compose 5.6.

### 1. Variables de entorno

```bash
cp .env.example .env
```

Completar en `.env`:

- `GEMINI_API_KEY`: llave gratuita de [Google AI Studio](https://aistudio.google.com/apikey).
- `TELEGRAM_BOT_TOKEN`: crear un bot con [@BotFather](https://t.me/BotFather) (`/newbot`).
- `TELEGRAM_CHAT_ID`: escribirle cualquier cosa al bot y abrir
  `https://api.telegram.org/bot<TOKEN>/getUpdates`; el número está en `message.chat.id`.

`.env` está en `.gitignore`. En n8n las llaves se guardan como **credenciales cifradas**, no en el flujo:
el JSON exportado solo tiene una referencia al id de la credencial.

### 2. API (Ejercicio 2)

```bash
cd api
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload          # http://localhost:8000/docs
pytest                                 # 27 pruebas
```

La primera vez crea `api/data/suministros.db` desde `sql/datos_prueba.sql` y aplica la migración.
Para volver a los datos originales: `python -m app.db --reset`.

Documentación: Swagger en <http://localhost:8000/docs>, ReDoc en `/redoc` y la especificación en
[`api/openapi.json`](api/openapi.json).

### 3. Flujo de n8n (Ejercicio 1)

Con n8n **detenido** y la API corriendo:

```bash
./flujo/configurar_n8n.sh                    # importa credenciales (desde .env) y flujos, y publica
set -a; source .env; set +a; npx n8n@2.43.8 start
python3 flujo/probar_anexo_b.py              # los 5 mensajes del Anexo B
```

O a mano en una instancia existente: importar `flujo/flujo_alertas_error.json` y `flujo/flujo_solicitudes.json`,
crear una credencial **Header Auth** (`x-goog-api-key: <llave>`) y una **Telegram API**, asignarlas a los nodos
*Gemini intento 1/2* y *Enviar alerta / Alertar error técnico*, y publicar el flujo. Si la instancia no permite
`$env`, el nodo *Config y validar entrada* usa valores por defecto (`http://localhost:8000`, `gemini-3.5-flash-lite`);
el chat de Telegram debe definirse ahí.

Ejemplo:

```bash
curl -X POST http://localhost:5678/webhook/solicitud -H 'Content-Type: application/json' \
  -d '{"cliente_email":"compras@ferreteriaeltornillo.com","mensaje":"Buenos días, necesitamos 10 resmas de papel carta para el viernes, es urgente."}'
```

```json
{
  "id": 61,
  "clasificacion": {"tipo": "pedido", "producto": "Resma papel carta", "cantidad": 10, "urgencia": "alta",
                    "resumen": "..."},
  "cliente": {"id": 1, "nombre": "Ferretería El Tornillo"},
  "producto_catalogo": {"id": 1, "nombre": "Resma papel carta", "stock": 340},
  "estado": "pendiente", "sin_stock": false, "requiere_revision": false, "intentos_llm": 1,
  "alertas": [{"condicion": "urgencia_alta", "detalle": "Urgencia alta"}],
  "notificacion": {"requerida": true, "enviada": true, "error": null}
}
```

### 4. Consultas SQL (Ejercicio 3)

```bash
python3 sql/ejecutar_consultas.py                         # sobre los datos originales
python3 sql/ejecutar_consultas.py api/data/suministros.db # sobre la BD de la API
```

(o `sqlite3 api/data/suministros.db < sql/consultas.sql` si se tiene el cliente `sqlite3`).

### 5. Chatbot (Ejercicio 4)

```bash
python3 prompts/probar_chatbot.py     # usa GEMINI_API_KEY de .env; sin dependencias externas
```

### 6. Docker (bonus)

```bash
docker compose up -d --build          # API en :8000, n8n en :5678 con el flujo ya importado y publicado
```

## Herramientas elegidas y por qué

| Herramienta | Por qué |
|---|---|
| **n8n** (self-hosted) | Es la herramienta que uso a diario. Corre local o en Docker sin costo, exporta el flujo como JSON versionable, tiene manejo de errores por nodo (`continueErrorOutput`) y nodos Code para la validación. Make o Zapier exigen cuenta en la nube y no exponen la API local sin túnel. |
| **Gemini 3.5 Flash-Lite** | Plan gratuito, ~1 s por clasificación y **salida estructurada** (`responseSchema` con `enum`), que reduce mucho los JSON inválidos. Se llama por HTTP Request en vez de un nodo de agente para controlar exactamente el cuerpo, el reintento y la validación. Lo elegí comparando con `gemini-3.8-flash` sobre el Anexo B: los dos clasificaron igual, pero el modelo grande tardó de 5 a 50 s y tuvo timeouts. (`gemini-2.5-flash` ya no está disponible para cuentas nuevas.) El modelo se cambia con `GEMINI_MODEL`. |
| **FastAPI** | Validación con Pydantic y Swagger automático: el contrato de la API se documenta solo. |
| **SQLite** | Cero configuración para quien evalúa: la BD se crea sola al arrancar la API. Las consultas usan funciones de ventana (SQLite ≥ 3.25). El código SQL es estándar salvo `julianday` (se indica el equivalente en PostgreSQL). |
| **sqlite3 de la biblioteca estándar** (sin ORM) | Seis endpoints con SQL simple; un ORM agregaría más código que el que ahorra, y el SQL queda visible para la sustentación. |
| **Telegram** | Bot gratuito en dos minutos, nodo nativo en n8n y llega al celular al instante. |

## Decisiones técnicas y supuestos

### Cómo maneja el flujo cada caso del Anexo B

| # | Caso | Qué hace el flujo |
|---|---|---|
| 1 | Pedido urgente de resmas | Pedido de "Resma papel carta" (340 en stock) → alerta por **urgencia alta**. |
| 2 | Consulta de diademas | Consulta de "Diadema con micrófono". Tiene stock 0, pero **no** es alerta de stock: solo aplica a pedidos (regla del enunciado). El stock 0 queda visible en la respuesta para el asesor. |
| 3 | Queja del tóner | Queja reiterada y con enojo → alerta por **queja** y **urgencia alta** (las dos condiciones). |
| 4 | 6 escritorios en L (stock 3) | **Se registra igual** (regla de negocio) y la API responde `sin_stock: true` → alerta por **sin stock** con el faltante (piden 6, hay 3, faltan 3). Rechazarlo perdería la venta; el asesor decide si ofrece entrega parcial. |
| 5 | Correo no registrado | **No se inventa un cliente**. La solicitud se guarda con `cliente_id = NULL`, el correo en `email_remitente`, y `requiere_revision = true` con motivo `cliente_no_registrado`. Se clasifica igual y se envía una alerta de **revisión manual**: es un posible cliente nuevo que pregunta precios y no debe perderse. Crear el cliente automáticamente exigiría inventar razón social y ciudad. |

### Flujo de n8n

- **Validación de entrada antes del LLM**: correo con formato válido y mensaje no vacío; si no, responde `400`
  sin gastar una llamada al modelo.
- **Catálogo dinámico en el prompt**: `GET /productos` en cada ejecución, para que el LLM devuelva el nombre
  exacto del catálogo.
- **Reintento**: si la respuesta no es un JSON válido o completo (o hubo HTTP 429/5xx o timeout), espera 2 s y
  reintenta **una vez**. En el reintento le muestra al modelo su respuesta y el error para que lo corrija. Si vuelve
  a fallar, la solicitud se guarda **sin clasificar** (`tipo` y `urgencia` en NULL) con `requiere_revision = true`
  y motivo `llm_invalido`, y se envía una alerta.
- **Asociación de producto en dos capas**: (1) el LLM ya devuelve el nombre del catálogo; (2)
  `GET /productos/coincidencia?texto=` en la API compara por palabras sin tildes, plurales ni palabras vacías, y
  tolera errores de tipeo. Así "resmas de papel", "escritorios en L" o "mouse inalambricos" encuentran su producto
  aunque el LLM no normalice el nombre. Si nada supera el umbral, se guarda el texto en `producto_texto` sin
  `producto_id`.
- **Alertas**: las tres condiciones del enunciado (`queja`, `urgencia_alta`, `sin_stock`) más una adicional,
  `revision_manual`, para que lo que el sistema no pudo procesar solo no se pierda. Cada alerta dice qué
  condición se cumplió y con qué datos.
- **El flujo nunca queda sin responder**: cada llamada HTTP tiene timeout y salida de error. Si la API se cae, se
  envía una alerta técnica y el webhook responde `502` con un JSON claro. Si Telegram falla, la solicitud ya quedó
  registrada y la respuesta lo indica (`notificacion.enviada: false`). Para errores no previstos, el flujo tiene
  configurado un *Error Workflow* que avisa por Telegram.
- La respuesta del webhook es `201` con el `id` y la clasificación, más el cliente y el producto asociados, las
  alertas y el estado de la notificación.

### API

- `GET /productos?q=` es la búsqueda parcial que pide el enunciado. Como `lower()` de SQLite solo entiende ASCII
  ("TÓNER" no encontraría "Tóner"), se registra una función `normalizar()` que quita mayúsculas y tildes.
- `GET /productos/coincidencia?texto=` es un **endpoint adicional** para el emparejamiento aproximado. Se separó
  para no cambiar la semántica de `?q=`.
- `POST /solicitudes` devuelve `201`. Errores: `422` por validación (campo faltante, `tipo` o `urgencia` no
  permitidos, `cantidad <= 0`, cliente o producto inexistente), `404` si no existe y `500` genérico sin filtrar
  detalles internos. Todos con el formato `{"error", "mensaje", "detalles"}`.
- `sin_stock` se calcula solo para `tipo = pedido` con producto y cantidad. Además se devuelve `stock_disponible`.
- `PATCH /solicitudes/{id}`: al pasar a `resuelta` se guarda `fecha_resolucion`; `resuelta → pendiente` responde
  **`409 Conflict`** (es un conflicto con el estado actual del recurso, no un dato mal formado). Supuesto:
  `resuelta → en_proceso` se permite como **reapertura** y borra la fecha de resolución, para que la métrica de
  tiempo de resolución no quede con una fecha falsa. Repetir el mismo estado no cambia nada (idempotente).
- Las fechas nuevas se guardan en hora de Colombia, igual que los datos de ejemplo.
- `GET /solicitudes` admite además `requiere_revision=true` para la bandeja de revisión manual.

### Cambios al modelo de datos

Aplicados en [`api/migrations/001_campos_ia.sql`](api/migrations/001_campos_ia.sql) (no se modificó `datos_prueba.sql`):

| Cambio | Para qué |
|---|---|
| `cliente_id` admite NULL | Guardar solicitudes de correos no registrados (Anexo B, mensaje 5). |
| `tipo` y `urgencia` admiten NULL **solo si** `requiere_revision = 1` | Guardar lo que el LLM no pudo clasificar. Un `CHECK` impide que una solicitud normal quede incompleta. |
| `email_remitente` | Correo con el que llegó (también para clientes registrados: trazabilidad). |
| `producto_texto` | El producto como lo escribió el cliente o lo devolvió el LLM. |
| `resumen` | Resumen generado por el LLM. |
| `requiere_revision`, `motivo_revision` | Bandeja de revisión manual (`llm_invalido`, `cliente_no_registrado`). |
| `CHECK (cantidad > 0)`, índices por cliente y estado | Integridad y consultas de la bandeja. |

SQLite no tiene `ALTER COLUMN`, así que la migración reconstruye la tabla conservando los 60 registros y sus id.

### Supuestos

- La identidad del cliente es su correo; no se verifica que el correo sea auténtico (en producción vendría del
  canal: SPF/DKIM en correo, número verificado en WhatsApp).
- Una solicitud se refiere a un producto principal (el modelo de datos tiene un solo `producto_id`); si hay más,
  quedan en el resumen.
- El stock **no** se descuenta al crear un pedido: el enunciado solo pide avisar. Descontarlo sería parte del
  despacho.

## Evidencias

- Ejercicio 1: [`flujo/evidencias/`](flujo/evidencias/README.md). Contiene una tabla con el resultado real de los
  5 mensajes del Anexo B (los cinco bien clasificados al primer intento y 4 alertas enviadas a Telegram), las
  respuestas completas del webhook y las capturas de n8n y de Telegram.
- Ejercicio 4: [`prompts/pruebas_chatbot.md`](prompts/pruebas_chatbot.md).
- Además del Anexo B, se probaron los caminos de error con un servidor que simula Gemini y Telegram: JSON inválido
  que se corrige en el reintento, JSON inválido dos veces (revisión manual), HTTP 429 en el primer intento,
  entrada inválida (400), Telegram caído (la solicitud se registra igual) y API caída (502 y alerta técnica).

## Pendiente y mejoras con más tiempo

- **Seguridad del webhook**: hoy es público. Agregaría autenticación por header o firma HMAC y límite de peticiones.
- **API**: autenticación (API key o OAuth2 entre n8n y la API), PostgreSQL con migraciones versionadas (Alembic)
  y logs estructurados con id de correlación compartido con la ejecución de n8n.
- **Calidad del clasificador**: un conjunto de 100 a 200 mensajes reales etiquetados para medir precisión por
  campo cada vez que cambie el prompt o el modelo, en vez de probar a ojo.
- **Varios productos por solicitud**: tabla `solicitud_items` para pedidos con varias líneas.
- **Deduplicación**: los datos tienen solicitudes repetidas (ver comentarios en `consultas.sql`). Un hash de
  correo + mensaje en una ventana de tiempo evitaría registrarlas dos veces.
- **Despliegue público**: el `docker-compose.yml` corre local. Para un servidor faltaría un proxy con HTTPS (Caddy
  o Traefik), `WEBHOOK_URL` con el dominio y backups del volumen de SQLite.
- **Chatbot con herramientas** en vez de catálogo en el contexto (ver `prompts/respuestas.md`, pregunta 3), y el
  agente del bonus con LangGraph.
