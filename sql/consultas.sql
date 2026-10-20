-- =============================================================
-- Ejercicio 3 - Consultas SQL
-- Motor: SQLite 3.25+ (usa funciones de ventana y julianday).
-- Funcionan sobre datos_prueba.sql tal cual y también después de la
-- migración api/migrations/001_campos_ia.sql (que solo agrega columnas).
--
-- Ejecutar:  sqlite3 api/data/suministros.db < sql/consultas.sql
--      o:    python sql/ejecutar_consultas.py
-- =============================================================


-- -------------------------------------------------------------
-- 1. Solicitudes pendientes con cliente, producto, tipo y urgencia,
--    de la más antigua a la más reciente.
--    LEFT JOIN: producto_id (y, tras la migración, cliente_id) pueden ser
--    NULL, y una solicitud sin producto no debe desaparecer del listado.
-- -------------------------------------------------------------
SELECT
    s.id                AS solicitud_id,
    s.fecha_creacion,
    c.nombre            AS cliente,
    p.nombre            AS producto,
    s.tipo,
    s.urgencia
FROM solicitudes AS s
LEFT JOIN clientes  AS c ON c.id = s.cliente_id
LEFT JOIN productos AS p ON p.id = s.producto_id
WHERE s.estado = 'pendiente'
ORDER BY s.fecha_creacion ASC, s.id ASC;


-- -------------------------------------------------------------
-- 2. Cantidad de solicitudes por tipo y porcentaje sobre el total
--    (un decimal). SUM(COUNT(*)) OVER () calcula el total en la misma
--    pasada, sin subconsulta. 100.0 fuerza división decimal.
--    COALESCE: tras la migración, las solicitudes que el LLM no pudo
--    clasificar tienen tipo NULL y se muestran como 'sin_clasificar'.
-- -------------------------------------------------------------
SELECT
    COALESCE(s.tipo, 'sin_clasificar')                     AS tipo,
    COUNT(*)                                               AS cantidad,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1)     AS porcentaje
FROM solicitudes AS s
GROUP BY COALESCE(s.tipo, 'sin_clasificar')
ORDER BY cantidad DESC;


-- -------------------------------------------------------------
-- 3. Clientes con 2 o más quejas: nombre, ciudad y número de quejas,
--    de mayor a menor.
-- -------------------------------------------------------------
SELECT
    c.nombre      AS cliente,
    c.ciudad,
    COUNT(*)      AS numero_quejas
FROM solicitudes AS s
INNER JOIN clientes AS c ON c.id = s.cliente_id
WHERE s.tipo = 'queja'
GROUP BY c.id, c.nombre, c.ciudad
HAVING COUNT(*) >= 2
ORDER BY numero_quejas DESC, c.nombre ASC;


-- -------------------------------------------------------------
-- 4. Tiempo promedio de resolución en horas por tipo, solo resueltas.
--    julianday() devuelve días con decimales; x 24 = horas.
--    En PostgreSQL sería: AVG(EXTRACT(EPOCH FROM (fecha_resolucion - fecha_creacion)) / 3600).
-- -------------------------------------------------------------
SELECT
    s.tipo,
    COUNT(*)                                                                   AS solicitudes_resueltas,
    ROUND(AVG((julianday(s.fecha_resolucion) - julianday(s.fecha_creacion)) * 24), 1) AS horas_promedio_resolucion
FROM solicitudes AS s
WHERE s.estado = 'resuelta'
  AND s.fecha_resolucion IS NOT NULL
GROUP BY s.tipo
ORDER BY horas_promedio_resolucion DESC;


-- -------------------------------------------------------------
-- 5. Pedidos cuya cantidad supera el stock actual del producto:
--    cliente, producto, cantidad pedida, stock y faltante.
--    Se muestra el estado porque cambia la lectura (ver nota de datos).
-- -------------------------------------------------------------
SELECT
    s.id                       AS solicitud_id,
    c.nombre                   AS cliente,
    p.nombre                   AS producto,
    s.cantidad                 AS cantidad_pedida,
    p.stock                    AS stock_actual,
    s.cantidad - p.stock       AS faltante,
    s.estado
FROM solicitudes AS s
INNER JOIN clientes  AS c ON c.id = s.cliente_id
INNER JOIN productos AS p ON p.id = s.producto_id
WHERE s.tipo = 'pedido'
  AND s.cantidad > p.stock
ORDER BY faltante DESC, s.id;


-- -------------------------------------------------------------
-- 6. Para cada cliente, solo su solicitud más reciente (fecha, tipo, estado).
--    ROW_NUMBER() numera las solicitudes de cada cliente de la más nueva a
--    la más vieja; se queda la número 1. El id desempata si dos solicitudes
--    tienen la misma fecha. LEFT JOIN para que los clientes sin
--    solicitudes también aparezcan (Agencia Creativa Pixel), con NULL.
-- -------------------------------------------------------------
WITH solicitudes_numeradas AS (
    SELECT
        s.cliente_id,
        s.id,
        s.fecha_creacion,
        s.tipo,
        s.estado,
        ROW_NUMBER() OVER (
            PARTITION BY s.cliente_id
            ORDER BY s.fecha_creacion DESC, s.id DESC
        ) AS orden
    FROM solicitudes AS s
    WHERE s.cliente_id IS NOT NULL
)
SELECT
    c.id               AS cliente_id,
    c.nombre           AS cliente,
    sn.id              AS solicitud_id,
    sn.fecha_creacion  AS fecha_ultima_solicitud,
    sn.tipo,
    sn.estado
FROM clientes AS c
LEFT JOIN solicitudes_numeradas AS sn
       ON sn.cliente_id = c.id
      AND sn.orden = 1
ORDER BY sn.fecha_creacion DESC, c.nombre;


-- =============================================================
-- Inconsistencias encontradas en los datos de ejemplo
-- =============================================================
-- a) Sobreventa del Escritorio en L: stock = 3, pero hay pedidos abiertos
--    (pendiente/en_proceso) por 14 unidades (#6: 10, #13: 1, #30: 3).
--    El #6 por sí solo pide 10. El stock no se descuenta al despachar.
-- b) Pedidos resueltos de productos con stock 0: #16 (Archivador metálico)
--    y #54 (Diadema con micrófono). O el stock es una foto actual y no
--    histórica (se agotó después), o se despachó sin inventario. Por eso la
--    consulta 5 muestra el estado: solo los abiertos (#6, #9) son un
--    faltante real hoy.
-- c) 9 de las 12 quejas se refieren a un producto que ese cliente nunca pidió
--    (p. ej. #14 "nos cobraron dos veces el pedido de teclado usb" del
--    Colegio San Martín, que no tiene pedidos de teclado; #36 "esperando el
--    escritorio en L" de Clínica Los Andes, sin pedido de escritorio).
--    Falta una referencia de la queja al pedido que la origina.
-- d) Posibles duplicados: #8 y #24 (Comercializadora Rivera, mismo texto
--    "¿Tienen disponible teclado usb?") con urgencia distinta (media / alta);
--    #13 y #34 (Ferretería El Tornillo, mismo pedido de 1 escritorio) con
--    estados distintos.
-- e) Urgencia incoherente: consultas simples de precio marcadas 'alta'
--    (#24, #28, #31, #42, #60), mientras quejas parecidas están en 'media'.
--    Muestra por qué conviene un criterio de urgencia explícito (prompt).
-- f) 14 solicitudes se resolvieron entre las 8 p. m. y las 6 a. m.
--    (p. ej. #4 a las 02:00, #7 a la 01:00): posible carga masiva o
--    zona horaria (¿UTC vs. hora Colombia?) mezclada en fecha_resolucion.
-- g) Solicitudes urgentes olvidadas: la queja #56 (alta) lleva pendiente
--    desde el 2026-07-03 y el pedido #49 (alta) desde el 2026-07-07:
--    justo el problema de negocio que describe el caso.
-- h) Menores: textos generados con plantilla ("El caja de esferos",
--    "1 unidades", "escritorio en l" en minúscula) y un cliente sin
--    solicitudes (Agencia Creativa Pixel).
