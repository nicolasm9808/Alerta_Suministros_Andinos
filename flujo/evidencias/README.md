# Evidencias del Ejercicio 1

Ejecución real del 2026-10-20 con `docker compose` (el 2026-10-19 se ejecutó también con n8n instalado por npm,
con las mismas clasificaciones): n8n 2.43.8, `gemini-3.5-flash-lite`, API local y bot de Telegram
`@alertas_suministros_andinos_bot`. Las respuestas completas del webhook están en
[`anexo_b_respuestas.json`](anexo_b_respuestas.json); se generaron con `python3 flujo/probar_anexo_b.py`.

| # | Cliente | Tipo | Producto asociado | Cant. | Urgencia | Resultado | Alertas enviadas | Tiempo |
|---|---|---|---|---|---|---|---|---|
| 1 | Ferretería El Tornillo | pedido | Resma papel carta (stock 340) | 10 | alta | id 61 | `urgencia_alta` | 2,8 s |
| 2 | Clínica Los Andes | consulta | Diadema con micrófono (stock 0) | – | baja | id 62 | ninguna | 1,6 s |
| 3 | Oficinas Modernas SAS | queja | Tóner HP 85A | – | alta | id 63 | `queja`, `urgencia_alta` | 2,5 s |
| 4 | Constructora Horizonte | pedido | Escritorio en L (stock 3) | 6 | media | id 64, `sin_stock: true` | `sin_stock` (faltan 3) | 3,0 s |
| 5 | No registrado (juanperez.compras@gmail.com) | consulta | Mouse inalámbrico | – | baja | id 65, revisión manual (`cliente_no_registrado`) | `revision_manual` | 2,0 s |

Los cinco se clasificaron bien al primer intento. El LLM devolvió el nombre exacto del catálogo en todos los casos
("resmas de papel" → "Resma papel carta", "escritorios en L" → "Escritorio en L").

## Caminos de error probados

Durante el desarrollo se usó un servidor que simula Gemini y Telegram para forzar cada falla. Las de entrada
inválida y API caída se repitieron después en el servidor real (ver capturas).

| Caso | Resultado |
|---|---|
| JSON inválido en el 1er intento | Reintento con el error explicado al modelo → clasificado (`intentos_llm: 2`). |
| JSON inválido dos veces | Guardada sin clasificar, `requiere_revision: true`, motivo `llm_invalido`, alerta. |
| HTTP 429 en el 1er intento | Espera 2 s, reintenta y clasifica. |
| Entrada sin correo válido ni mensaje | `400` con la lista de errores, sin llamar al LLM. |
| Telegram rechaza el mensaje | La solicitud se registra igual; `notificacion.enviada: false` con el error. |
| API caída | `502` con JSON claro (`etapa: "Obtener catálogo"`) y alerta técnica por Telegram. |

## Capturas (servidor público, 2026-10-20)

Tomadas en la instancia desplegada en Google Cloud (`https://n8n.34-26-7-154.sslip.io/webhook/solicitud`), con la
base de datos reiniciada para que los id coincidan con la tabla de arriba (61 a 65). Las pruebas se enviaron una por
una por el webhook público.

### El flujo

![Flujo completo en n8n](01_flujo.png)

### Mensaje 1: pedido urgente → alerta `urgencia_alta`

| Ejecución | Validación de la respuesta de Gemini | Alerta |
|---|---|---|
| ![](02_pedido_urgente.png) | ![](02.1_pedido_urgente.png) | ![](03_telegram_urgente.png) |

### Mensaje 2: consulta de un producto agotado → sin alerta

La regla de "sin stock" solo aplica a pedidos. El flujo conoce el stock (0) y aun así no alerta.

| Ejecución (pasa de *¿Requiere alerta?* a *Armar respuesta*) | Producto encontrado con stock 0 |
|---|---|
| ![](04_consulta_sin_alerta.png) | ![](04.1_consulta_sin_alerta.png) |

### Mensaje 3: queja → alertas `queja` y `urgencia_alta`, con reintento

El primer intento de Gemini devolvió el JSON con un escape Unicode equivocado: `"T3ner"` (`3` es "3")
en lugar de `"Tóner"` ("ó"). La validación lo detectó, el flujo reintentó y el segundo intento fue correcto.

| Camino con reintento | Intento 1: rechazado por texto dañado | Intento 2: válido | Alerta |
|---|---|---|---|
| ![](05_queja_reintento.png) | ![](05.1_queja_intento1_fallido.png) | ![](05.2_queja_intento2_valido.png) | ![](06_telegram_queja.png) |

### Mensaje 4: pedido mayor al stock → alerta `sin_stock`

Se piden 6 escritorios en L y hay 3. La API responde `sin_stock: true` y la solicitud se guarda igual.

| Ejecución | Respuesta de `POST /solicitudes` | Alerta |
|---|---|---|
| ![](07_sin_stock.png) | ![](07.1_sin_stock_api.png) | ![](08_telegram_sin_stock.png) |

### Mensaje 5: correo no registrado → revisión manual

`GET /clientes` responde 404 y el flujo lo trata como un dato, no como un error. La solicitud se guarda con
`cliente_id: null` y `requiere_revision: true`. Aquí el primer intento de Gemini tardó más de 30 s (timeout) y
el reintento lo resolvió.

| Ejecución | Cliente no encontrado (404) | Solicitud marcada para revisión | Intento 1: timeout | Alerta |
|---|---|---|---|---|
| ![](09_cliente_no_registrado.png) | ![](09.1_cliente_404.png) | ![](09.2_revision_manual.png) | ![](09.3_timeout_reintento.png) | ![](10_telegram_no_registrado.png) |

### Error: entrada inválida → 400 sin llamar al LLM

`{"cliente_email": "esto-no-es-un-correo", "mensaje": "   "}` → `400` en 0,7 s con la lista de errores.

| Ejecución (camino corto) | Detalle de la validación |
|---|---|
| ![](11_entrada_invalida.png) | ![](11.1_entrada_invalida_detalle.png) |

### Error: API caída → 502 y alerta técnica

Con el contenedor de la API detenido, el webhook respondió `502` en 6 s con
`{"error": "error_procesando", "etapa": "Obtener catálogo", "detalle": "getaddrinfo EAI_AGAIN api"}`.

| Ejecución (salida de error hacia *Error técnico*) | Detalle | Alerta técnica |
|---|---|---|
| ![](12_api_caida.png) | ![](12.1_api_caida_detalle.png) | ![](13_telegram_error_tecnico.png) |
