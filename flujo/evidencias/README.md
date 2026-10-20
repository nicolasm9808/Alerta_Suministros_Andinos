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

Se usó un servidor que simula Gemini y Telegram para forzar cada falla:

| Caso | Resultado |
|---|---|
| JSON inválido en el 1er intento | Reintento con el error explicado al modelo → clasificado (`intentos_llm: 2`). |
| JSON inválido dos veces | Guardada sin clasificar, `requiere_revision: true`, motivo `llm_invalido`, alerta. |
| HTTP 429 en el 1er intento | Espera 2 s, reintenta y clasifica. |
| Entrada sin correo válido ni mensaje | `400` con la lista de errores, sin llamar al LLM. |
| Telegram rechaza el mensaje | La solicitud se registra igual; `notificacion.enviada: false` con el error. |
| API caída | `502` con JSON claro (`etapa: "Obtener catálogo"`) y alerta técnica por Telegram. |

## Capturas

<!-- Agregar aquí: ejecución en n8n de cada mensaje y las alertas recibidas en Telegram. -->
