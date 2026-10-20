# Ejercicio 4, parte C: preguntas conceptuales

### 1. ¿Cómo evitar que el chatbot invente precios o disponibilidad?

- **El dato sale de la BD, no del modelo**: precio y stock llegan por herramienta o contexto en cada consulta.
- **Una salida permitida**: "si no tienes el dato, dilo y ofrece un asesor". Sin esa salida, el modelo rellena.
- **Validación posterior en código**: cada precio o cantidad de la respuesta se compara con la BD antes de enviarla.
- **Plantillas para lo crítico**: el modelo elige el producto y el sistema escribe el precio desde la BD.
- **Temperatura baja** y un banco de preguntas trampa ("¿cuánto vale la impresora X?") en cada cambio de prompt.

### 2. ¿Qué es RAG y cuándo usarlo en vez de poner todo en el prompt?

RAG (*Retrieval-Augmented Generation*): antes de responder se buscan los fragmentos relevantes en una base de
conocimiento (*embeddings* en una base vectorial, a veces más búsqueda por palabras) y solo esos van al prompt.
Lo usaría cuando la información no cabe o no conviene meterla entera: miles de fichas técnicas, manuales,
políticas de garantía o preguntas frecuentes que cambian seguido. Gasta menos tokens, se actualiza sin tocar el
prompt y permite citar la fuente. Para 12 productos no hace falta: caben enteros. Y los datos exactos y
cambiantes (stock, estado de un pedido) no van por RAG sino por una consulta a la API (pregunta 3).

### 3. ¿Qué es *function calling* y cómo lo usaría para consultar el estado de una solicitud?

Se le dan al modelo funciones con nombre, descripción y parámetros (JSON Schema). El modelo no las ejecuta:
pide "llamar a `consultar_solicitud` con `{"id": 61}`", **mi código** la ejecuta y le devuelve el resultado.
Definiría `consultar_solicitud(id)` y `listar_mis_solicitudes(estado?)`, que llaman a `GET /solicitudes/{id}`
y `GET /solicitudes` de la API. Lo clave es que **el código valida, no el modelo**: el `cliente_id` sale de la
sesión autenticada del canal, nunca del chat, y si la solicitud no es de ese cliente responde "no encontrada".
Así, aunque engañen al modelo, no puede leer datos ajenos. Las herramientas que escriben piden confirmación.

### 4. ¿Diferencia entre chatbot y agente de IA? Ejemplo para este caso

Un **chatbot** responde mensajes en un solo paso con lo que tiene en el contexto. Un **agente** persigue un
objetivo: decide qué pasos dar, usa herramientas (API, BD, correo), revisa los resultados y sigue hasta terminar
o escalar. Ejemplo: un **agente de pedidos sin stock**. Cuando entra un pedido con `sin_stock: true`, revisa el
inventario y los pedidos abiertos del producto, calcula el faltante, busca un sustituto con stock y deja al
asesor un borrador de propuesta al cliente (entrega parcial más sustituto) para aprobar con un clic.

### 5. ¿Cómo controlar el costo con 5.000 solicitudes diarias?

- **Medir**: 5.000 × ~1.200 tokens ≈ 6 M tokens/día; con un modelo *flash* son pocos dólares al día.
- **El modelo más pequeño que cumpla**, sin razonamiento extendido; solo los casos dudosos pasan a uno mayor.
- **Filtrar antes del LLM**: duplicados, spam o respuestas automáticas no llaman al modelo; caché de mensajes idénticos.
- **Prompt corto y cacheable** (la parte fija primero, para el *context caching*) y `maxOutputTokens` bajo.
- **Batch API** (~50 % más barata) para lo que no es urgente, como reclasificaciones nocturnas.
- **Límites**: tope diario de gasto, un solo reintento y un tablero de tokens y costo por solicitud.
