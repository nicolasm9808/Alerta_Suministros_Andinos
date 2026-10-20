-- =============================================================
-- Prueba técnica - Base de datos de ejemplo
-- Compatible con SQLite y PostgreSQL
-- =============================================================

DROP TABLE IF EXISTS solicitudes;
DROP TABLE IF EXISTS productos;
DROP TABLE IF EXISTS clientes;

CREATE TABLE clientes (
    id              INTEGER PRIMARY KEY,
    nombre          VARCHAR(120) NOT NULL,
    ciudad          VARCHAR(60)  NOT NULL,
    email           VARCHAR(120) NOT NULL UNIQUE,
    fecha_registro  DATE         NOT NULL
);

CREATE TABLE productos (
    id         INTEGER PRIMARY KEY,
    nombre     VARCHAR(120) NOT NULL,
    categoria  VARCHAR(60)  NOT NULL,
    precio     NUMERIC(12,2) NOT NULL,
    stock      INTEGER      NOT NULL DEFAULT 0
);

CREATE TABLE solicitudes (
    id                INTEGER PRIMARY KEY,
    cliente_id        INTEGER NOT NULL REFERENCES clientes(id),
    producto_id       INTEGER REFERENCES productos(id),
    tipo              VARCHAR(20) NOT NULL CHECK (tipo IN ('pedido','consulta','queja')),
    cantidad          INTEGER,
    urgencia          VARCHAR(10) NOT NULL CHECK (urgencia IN ('baja','media','alta')),
    estado            VARCHAR(20) NOT NULL CHECK (estado IN ('pendiente','en_proceso','resuelta')),
    mensaje           TEXT NOT NULL,
    fecha_creacion    TIMESTAMP NOT NULL,
    fecha_resolucion  TIMESTAMP
);

INSERT INTO clientes (id, nombre, ciudad, email, fecha_registro) VALUES
(1, 'Ferretería El Tornillo', 'Bogotá', 'compras@ferreteriaeltornillo.com', '2024-11-27'),
(2, 'Papelería Central', 'Medellín', 'compras@papeleriacentral.com', '2024-06-03'),
(3, 'Oficinas Modernas SAS', 'Cali', 'compras@oficinasmodernassas.com', '2025-02-08'),
(4, 'Colegio San Martín', 'Bucaramanga', 'compras@colegiosanmartin.com', '2024-02-19'),
(5, 'Clínica Los Andes', 'Bogotá', 'compras@clinicalosandes.com', '2024-03-15'),
(6, 'Comercializadora Rivera', 'Barranquilla', 'compras@comercializadorarivera.com', '2025-07-02'),
(7, 'Hotel Plaza Real', 'Cartagena', 'compras@hotelplazareal.com', '2024-04-06'),
(8, 'Universidad del Norte Andino', 'Bucaramanga', 'compras@universidaddelnorteandino.com', '2025-01-09'),
(9, 'Tienda Don Pedro', 'Cúcuta', 'compras@tiendadonpedro.com', '2025-08-19'),
(10, 'Constructora Horizonte', 'Medellín', 'compras@constructorahorizonte.com', '2024-02-29'),
(11, 'Agencia Creativa Pixel', 'Bogotá', 'compras@agenciacreativapixel.com', '2025-06-03'),
(12, 'Restaurante La Fogata', 'Pereira', 'compras@restaurantelafogata.com', '2024-08-07');

INSERT INTO productos (id, nombre, categoria, precio, stock) VALUES
(1, 'Resma papel carta', 'Papelería', 21000.00, 340),
(2, 'Tóner HP 85A', 'Impresión', 185000.00, 12),
(3, 'Silla ergonómica', 'Mobiliario', 450000.00, 8),
(4, 'Escritorio en L', 'Mobiliario', 780000.00, 3),
(5, 'Mouse inalámbrico', 'Tecnología', 45000.00, 120),
(6, 'Teclado USB', 'Tecnología', 38000.00, 95),
(7, 'Monitor 24 pulgadas', 'Tecnología', 620000.00, 15),
(8, 'Archivador metálico', 'Mobiliario', 390000.00, 0),
(9, 'Caja de esferos x12', 'Papelería', 15000.00, 500),
(10, 'Cartucho Epson 664', 'Impresión', 32000.00, 60),
(11, 'Diadema con micrófono', 'Tecnología', 89000.00, 0),
(12, 'Tablero acrílico', 'Papelería', 160000.00, 22);

INSERT INTO solicitudes (id, cliente_id, producto_id, tipo, cantidad, urgencia, estado, mensaje, fecha_creacion, fecha_resolucion) VALUES
(1, 1, 7, 'consulta', NULL, 'baja', 'pendiente', '¿Manejan descuento por volumen en monitor 24 pulgadas?', '2026-07-12 16:45:00', NULL),
(2, 1, 4, 'queja', NULL, 'alta', 'pendiente', 'El escritorio en l que nos llegó vino defectuoso, necesitamos solución.', '2026-09-12 17:45:00', NULL),
(3, 1, 3, 'pedido', 5, 'baja', 'resuelta', 'Buenos días, necesitamos 5 unidades de silla ergonómica para esta semana.', '2026-07-16 17:30:00', '2026-07-20 10:30:00'),
(4, 1, 10, 'pedido', 3, 'baja', 'resuelta', 'Quiero hacer un pedido de 3 cartucho epson 664, gracias.', '2026-09-30 09:00:00', '2026-10-03 02:00:00'),
(5, 5, 6, 'consulta', NULL, 'media', 'en_proceso', '¿Tienen disponible teclado usb? ¿Qué precio maneja?', '2026-08-28 13:30:00', NULL),
(6, 8, 4, 'pedido', 10, 'baja', 'en_proceso', 'Buenos días, necesitamos 10 unidades de escritorio en l para esta semana.', '2026-09-02 13:45:00', NULL),
(7, 1, 7, 'pedido', 3, 'baja', 'resuelta', 'Quiero hacer un pedido de 3 monitor 24 pulgadas, gracias.', '2026-09-01 14:00:00', '2026-09-02 01:00:00'),
(8, 6, 6, 'consulta', NULL, 'media', 'pendiente', '¿Tienen disponible teclado usb? ¿Qué precio maneja?', '2026-09-15 15:45:00', NULL),
(9, 12, 8, 'pedido', 1, 'media', 'en_proceso', 'Por favor enviar 1 archivador metálico a la sede principal.', '2026-08-09 17:45:00', NULL),
(10, 10, 6, 'pedido', 5, 'baja', 'pendiente', 'Por favor enviar 5 teclado usb a la sede principal.', '2026-09-17 09:45:00', NULL),
(11, 1, 4, 'consulta', NULL, 'baja', 'resuelta', 'Quisiera saber el tiempo de entrega de escritorio en l.', '2026-09-02 09:15:00', '2026-09-05 09:15:00'),
(12, 10, 7, 'queja', NULL, 'media', 'resuelta', 'El monitor 24 pulgadas que nos llegó vino defectuoso, necesitamos solución.', '2026-08-23 13:45:00', '2026-08-24 10:45:00'),
(13, 1, 4, 'pedido', 1, 'media', 'en_proceso', 'Buenos días, necesitamos 1 unidades de escritorio en l para esta semana.', '2026-09-14 10:30:00', NULL),
(14, 4, 6, 'queja', NULL, 'alta', 'resuelta', 'Nos cobraron dos veces el pedido de teclado usb.', '2026-07-17 16:00:00', '2026-07-22 09:00:00'),
(15, 10, 7, 'consulta', NULL, 'baja', 'pendiente', '¿Tienen disponible monitor 24 pulgadas? ¿Qué precio maneja?', '2026-07-14 15:45:00', NULL),
(16, 12, 8, 'pedido', 1, 'baja', 'resuelta', 'Buenos días, necesitamos 1 unidades de archivador metálico para esta semana.', '2026-07-07 09:00:00', '2026-07-10 07:00:00'),
(17, 12, 10, 'pedido', 1, 'alta', 'resuelta', 'Quiero hacer un pedido de 1 cartucho epson 664, gracias.', '2026-09-17 14:15:00', '2026-09-19 12:15:00'),
(18, 3, 2, 'pedido', 5, 'alta', 'en_proceso', 'Buenos días, necesitamos 5 unidades de tóner hp 85a para esta semana.', '2026-08-29 15:45:00', NULL),
(19, 1, 6, 'pedido', 5, 'alta', 'en_proceso', 'Quiero hacer un pedido de 5 teclado usb, gracias.', '2026-07-21 16:00:00', NULL),
(20, 3, 12, 'queja', NULL, 'alta', 'resuelta', 'El tablero acrílico que nos llegó vino defectuoso, necesitamos solución.', '2026-10-06 16:30:00', '2026-10-11 08:30:00'),
(21, 8, 5, 'queja', NULL, 'media', 'resuelta', 'Nos cobraron dos veces el pedido de mouse inalámbrico.', '2026-07-22 13:15:00', '2026-07-26 18:15:00'),
(22, 3, 4, 'queja', NULL, 'alta', 'resuelta', 'El escritorio en l que nos llegó vino defectuoso, necesitamos solución.', '2026-10-06 11:15:00', '2026-10-10 11:15:00'),
(23, 2, 8, 'consulta', NULL, 'media', 'en_proceso', '¿Manejan descuento por volumen en archivador metálico?', '2026-07-04 12:45:00', NULL),
(24, 6, 6, 'consulta', NULL, 'alta', 'pendiente', '¿Tienen disponible teclado usb? ¿Qué precio maneja?', '2026-10-01 13:30:00', NULL),
(25, 2, 4, 'consulta', NULL, 'baja', 'resuelta', 'Quisiera saber el tiempo de entrega de escritorio en l.', '2026-09-18 17:00:00', '2026-09-22 06:00:00'),
(26, 10, 2, 'pedido', 5, 'media', 'resuelta', 'Quiero hacer un pedido de 5 tóner hp 85a, gracias.', '2026-10-05 11:45:00', '2026-10-07 20:45:00'),
(27, 3, 12, 'consulta', NULL, 'media', 'pendiente', '¿Tienen disponible tablero acrílico? ¿Qué precio maneja?', '2026-10-04 09:15:00', NULL),
(28, 1, 10, 'consulta', NULL, 'alta', 'resuelta', '¿Tienen disponible cartucho epson 664? ¿Qué precio maneja?', '2026-07-19 17:45:00', '2026-07-21 15:45:00'),
(29, 5, 3, 'pedido', 1, 'media', 'resuelta', 'Buenos días, necesitamos 1 unidades de silla ergonómica para esta semana.', '2026-10-01 09:15:00', '2026-10-06 02:15:00'),
(30, 10, 4, 'pedido', 3, 'baja', 'en_proceso', 'Por favor enviar 3 escritorio en l a la sede principal.', '2026-09-03 11:30:00', NULL),
(31, 10, 1, 'consulta', NULL, 'alta', 'resuelta', '¿Manejan descuento por volumen en resma papel carta?', '2026-09-23 17:45:00', '2026-09-28 11:45:00'),
(32, 1, 3, 'queja', NULL, 'alta', 'resuelta', 'El silla ergonómica que nos llegó vino defectuoso, necesitamos solución.', '2026-08-26 10:00:00', '2026-08-27 07:00:00'),
(33, 1, 10, 'pedido', 10, 'baja', 'resuelta', 'Quiero hacer un pedido de 10 cartucho epson 664, gracias.', '2026-09-26 16:45:00', '2026-09-27 07:45:00'),
(34, 1, 4, 'pedido', 1, 'media', 'resuelta', 'Buenos días, necesitamos 1 unidades de escritorio en l para esta semana.', '2026-09-03 15:00:00', '2026-09-08 13:00:00'),
(35, 5, 10, 'queja', NULL, 'alta', 'resuelta', 'Llevamos varios días esperando el cartucho epson 664 y no ha llegado.', '2026-07-26 12:45:00', '2026-07-30 21:45:00'),
(36, 5, 4, 'queja', NULL, 'alta', 'resuelta', 'Llevamos varios días esperando el escritorio en l y no ha llegado.', '2026-08-03 16:15:00', '2026-08-04 11:15:00'),
(37, 1, 8, 'consulta', NULL, 'baja', 'en_proceso', 'Quisiera saber el tiempo de entrega de archivador metálico.', '2026-07-31 14:00:00', NULL),
(38, 9, 3, 'consulta', NULL, 'baja', 'resuelta', 'Quisiera saber el tiempo de entrega de silla ergonómica.', '2026-07-18 15:15:00', '2026-07-19 05:15:00'),
(39, 10, 3, 'pedido', 2, 'media', 'resuelta', 'Por favor enviar 2 silla ergonómica a la sede principal.', '2026-09-04 14:30:00', '2026-09-06 13:30:00'),
(40, 1, 6, 'pedido', 3, 'media', 'en_proceso', 'Quiero hacer un pedido de 3 teclado usb, gracias.', '2026-08-26 08:45:00', NULL),
(41, 3, 2, 'pedido', 2, 'alta', 'en_proceso', 'Buenos días, necesitamos 2 unidades de tóner hp 85a para esta semana.', '2026-07-14 09:30:00', NULL),
(42, 3, 3, 'consulta', NULL, 'alta', 'pendiente', '¿Manejan descuento por volumen en silla ergonómica?', '2026-09-25 12:45:00', NULL),
(43, 6, 12, 'consulta', NULL, 'baja', 'resuelta', '¿Tienen disponible tablero acrílico? ¿Qué precio maneja?', '2026-07-08 10:45:00', '2026-07-09 22:45:00'),
(44, 7, 5, 'pedido', 10, 'alta', 'resuelta', 'Quiero hacer un pedido de 10 mouse inalámbrico, gracias.', '2026-07-09 12:00:00', '2026-07-11 09:00:00'),
(45, 4, 5, 'queja', NULL, 'media', 'resuelta', 'El mouse inalámbrico que nos llegó vino defectuoso, necesitamos solución.', '2026-09-06 11:00:00', '2026-09-07 22:00:00'),
(46, 2, 5, 'pedido', 10, 'media', 'en_proceso', 'Buenos días, necesitamos 10 unidades de mouse inalámbrico para esta semana.', '2026-08-07 15:15:00', NULL),
(47, 12, 1, 'pedido', 1, 'media', 'en_proceso', 'Por favor enviar 1 resma papel carta a la sede principal.', '2026-09-09 11:45:00', NULL),
(48, 1, 11, 'consulta', NULL, 'media', 'resuelta', 'Quisiera saber el tiempo de entrega de diadema con micrófono.', '2026-09-08 14:30:00', '2026-09-09 21:30:00'),
(49, 2, 12, 'pedido', 5, 'alta', 'pendiente', 'Quiero hacer un pedido de 5 tablero acrílico, gracias.', '2026-07-07 10:00:00', NULL),
(50, 10, 7, 'pedido', 1, 'baja', 'resuelta', 'Por favor enviar 1 monitor 24 pulgadas a la sede principal.', '2026-08-18 16:30:00', '2026-08-22 10:30:00'),
(51, 1, 3, 'pedido', 3, 'media', 'resuelta', 'Por favor enviar 3 silla ergonómica a la sede principal.', '2026-08-03 13:30:00', '2026-08-06 13:30:00'),
(52, 2, 5, 'pedido', 3, 'baja', 'resuelta', 'Quiero hacer un pedido de 3 mouse inalámbrico, gracias.', '2026-08-12 14:00:00', '2026-08-15 08:00:00'),
(53, 2, 9, 'pedido', 1, 'baja', 'resuelta', 'Buenos días, necesitamos 1 unidades de caja de esferos x12 para esta semana.', '2026-07-12 10:45:00', '2026-07-14 14:45:00'),
(54, 3, 11, 'pedido', 1, 'media', 'resuelta', 'Por favor enviar 1 diadema con micrófono a la sede principal.', '2026-09-06 10:45:00', '2026-09-10 08:45:00'),
(55, 1, 12, 'queja', NULL, 'alta', 'resuelta', 'Nos cobraron dos veces el pedido de tablero acrílico.', '2026-07-06 16:45:00', '2026-07-11 01:45:00'),
(56, 1, 9, 'queja', NULL, 'alta', 'pendiente', 'El caja de esferos x12 que nos llegó vino defectuoso, necesitamos solución.', '2026-07-03 17:15:00', NULL),
(57, 1, 6, 'pedido', 5, 'alta', 'resuelta', 'Buenos días, necesitamos 5 unidades de teclado usb para esta semana.', '2026-09-10 08:00:00', '2026-09-14 01:00:00'),
(58, 5, 1, 'consulta', NULL, 'media', 'resuelta', '¿Manejan descuento por volumen en resma papel carta?', '2026-10-04 16:00:00', '2026-10-05 02:00:00'),
(59, 9, 5, 'pedido', 3, 'baja', 'resuelta', 'Por favor enviar 3 mouse inalámbrico a la sede principal.', '2026-10-05 11:15:00', '2026-10-07 23:15:00'),
(60, 10, 2, 'consulta', NULL, 'alta', 'pendiente', '¿Tienen disponible tóner hp 85a? ¿Qué precio maneja?', '2026-08-06 08:15:00', NULL);
