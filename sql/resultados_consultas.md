
### 1. Solicitudes pendientes con cliente, producto, tipo y urgencia,

| solicitud_id | fecha_creacion      | cliente                 | producto            | tipo     | urgencia |
|--------------|---------------------|-------------------------|---------------------|----------|----------|
| 56           | 2026-07-03 17:15:00 | Ferretería El Tornillo  | Caja de esferos x12 | queja    | alta     |
| 49           | 2026-07-07 10:00:00 | Papelería Central       | Tablero acrílico    | pedido   | alta     |
| 1            | 2026-07-12 16:45:00 | Ferretería El Tornillo  | Monitor 24 pulgadas | consulta | baja     |
| 15           | 2026-07-14 15:45:00 | Constructora Horizonte  | Monitor 24 pulgadas | consulta | baja     |
| 60           | 2026-08-06 08:15:00 | Constructora Horizonte  | Tóner HP 85A        | consulta | alta     |
| 2            | 2026-09-12 17:45:00 | Ferretería El Tornillo  | Escritorio en L     | queja    | alta     |
| 8            | 2026-09-15 15:45:00 | Comercializadora Rivera | Teclado USB         | consulta | media    |
| 10           | 2026-09-17 09:45:00 | Constructora Horizonte  | Teclado USB         | pedido   | baja     |
| 42           | 2026-09-25 12:45:00 | Oficinas Modernas SAS   | Silla ergonómica    | consulta | alta     |
| 24           | 2026-10-01 13:30:00 | Comercializadora Rivera | Teclado USB         | consulta | alta     |
| 27           | 2026-10-04 09:15:00 | Oficinas Modernas SAS   | Tablero acrílico    | consulta | media    |
(11 filas)

### 2. Cantidad de solicitudes por tipo y porcentaje sobre el total

| tipo     | cantidad | porcentaje |
|----------|----------|------------|
| pedido   | 30       | 50.0       |
| consulta | 18       | 30.0       |
| queja    | 12       | 20.0       |
(3 filas)

### 3. Clientes con 2 o más quejas: nombre, ciudad y número de quejas,

| cliente                | ciudad      | numero_quejas |
|------------------------|-------------|---------------|
| Ferretería El Tornillo | Bogotá      | 4             |
| Clínica Los Andes      | Bogotá      | 2             |
| Colegio San Martín     | Bucaramanga | 2             |
| Oficinas Modernas SAS  | Cali        | 2             |
(4 filas)

### 4. Tiempo promedio de resolución en horas por tipo, solo resueltas.

| tipo     | solicitudes_resueltas | horas_promedio_resolucion |
|----------|-----------------------|---------------------------|
| queja    | 10                    | 72.8                      |
| pedido   | 18                    | 66.6                      |
| consulta | 8                     | 51.0                      |
(3 filas)

### 5. Pedidos cuya cantidad supera el stock actual del producto:

| solicitud_id | cliente                      | producto              | cantidad_pedida | stock_actual | faltante | estado     |
|--------------|------------------------------|-----------------------|-----------------|--------------|----------|------------|
| 6            | Universidad del Norte Andino | Escritorio en L       | 10              | 3            | 7        | en_proceso |
| 9            | Restaurante La Fogata        | Archivador metálico   | 1               | 0            | 1        | en_proceso |
| 16           | Restaurante La Fogata        | Archivador metálico   | 1               | 0            | 1        | resuelta   |
| 54           | Oficinas Modernas SAS        | Diadema con micrófono | 1               | 0            | 1        | resuelta   |
(4 filas)

### 6. Para cada cliente, solo su solicitud más reciente (fecha, tipo, estado).

| cliente_id | cliente                      | solicitud_id | fecha_ultima_solicitud | tipo     | estado     |
|------------|------------------------------|--------------|------------------------|----------|------------|
| 3          | Oficinas Modernas SAS        | 20           | 2026-10-06 16:30:00    | queja    | resuelta   |
| 10         | Constructora Horizonte       | 26           | 2026-10-05 11:45:00    | pedido   | resuelta   |
| 9          | Tienda Don Pedro             | 59           | 2026-10-05 11:15:00    | pedido   | resuelta   |
| 5          | Clínica Los Andes            | 58           | 2026-10-04 16:00:00    | consulta | resuelta   |
| 6          | Comercializadora Rivera      | 24           | 2026-10-01 13:30:00    | consulta | pendiente  |
| 1          | Ferretería El Tornillo       | 4            | 2026-09-30 09:00:00    | pedido   | resuelta   |
| 2          | Papelería Central            | 25           | 2026-09-18 17:00:00    | consulta | resuelta   |
| 12         | Restaurante La Fogata        | 17           | 2026-09-17 14:15:00    | pedido   | resuelta   |
| 4          | Colegio San Martín           | 45           | 2026-09-06 11:00:00    | queja    | resuelta   |
| 8          | Universidad del Norte Andino | 6            | 2026-09-02 13:45:00    | pedido   | en_proceso |
| 7          | Hotel Plaza Real             | 44           | 2026-07-09 12:00:00    | pedido   | resuelta   |
| 11         | Agencia Creativa Pixel       |              |                        |          |            |
(12 filas)
