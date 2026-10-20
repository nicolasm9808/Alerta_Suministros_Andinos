-- =============================================================
-- Migración 001: campos para la automatización con IA
--
-- Cambios sobre el esquema original de datos_prueba.sql:
--   * cliente_id pasa a ser NULL-able: una solicitud de un correo que no
--     existe en clientes se guarda igual (no se inventa un cliente) y queda
--     marcada para revisión manual.
--   * tipo y urgencia pasan a ser NULL-ables SOLO cuando requiere_revision = 1
--     (el LLM falló dos veces y nadie ha clasificado aún el mensaje).
--   * Columnas nuevas:
--       email_remitente   correo con el que llegó la solicitud
--       producto_texto    producto tal como lo escribió el cliente / LLM
--       resumen           frase corta generada por el LLM
--       requiere_revision 1 si una persona debe revisarla
--       motivo_revision   por qué (llm_invalido, cliente_no_registrado, ...)
--
-- SQLite no permite ALTER COLUMN, por eso se reconstruye la tabla.
-- Los 60 registros originales se conservan con sus mismos id.
-- =============================================================

CREATE TABLE solicitudes_nueva (
    id                INTEGER PRIMARY KEY,
    cliente_id        INTEGER REFERENCES clientes(id),
    producto_id       INTEGER REFERENCES productos(id),
    tipo              VARCHAR(20) CHECK (tipo IN ('pedido','consulta','queja')),
    cantidad          INTEGER CHECK (cantidad IS NULL OR cantidad > 0),
    urgencia          VARCHAR(10) CHECK (urgencia IN ('baja','media','alta')),
    estado            VARCHAR(20) NOT NULL CHECK (estado IN ('pendiente','en_proceso','resuelta')),
    mensaje           TEXT NOT NULL,
    fecha_creacion    TIMESTAMP NOT NULL,
    fecha_resolucion  TIMESTAMP,
    email_remitente   VARCHAR(120),
    producto_texto    VARCHAR(200),
    resumen           VARCHAR(300),
    requiere_revision INTEGER NOT NULL DEFAULT 0 CHECK (requiere_revision IN (0, 1)),
    motivo_revision   VARCHAR(60),
    -- Sin revisión manual, la solicitud debe estar completa y tener cliente.
    CHECK (requiere_revision = 1 OR (tipo IS NOT NULL AND urgencia IS NOT NULL AND cliente_id IS NOT NULL)),
    -- Debe saberse quién la envió: un cliente registrado o al menos su correo.
    CHECK (cliente_id IS NOT NULL OR email_remitente IS NOT NULL)
);

INSERT INTO solicitudes_nueva (id, cliente_id, producto_id, tipo, cantidad, urgencia, estado,
                               mensaje, fecha_creacion, fecha_resolucion)
SELECT id, cliente_id, producto_id, tipo, cantidad, urgencia, estado,
       mensaje, fecha_creacion, fecha_resolucion
FROM solicitudes;

DROP TABLE solicitudes;
ALTER TABLE solicitudes_nueva RENAME TO solicitudes;

CREATE INDEX idx_solicitudes_cliente ON solicitudes (cliente_id);
CREATE INDEX idx_solicitudes_estado ON solicitudes (estado, tipo, urgencia);
