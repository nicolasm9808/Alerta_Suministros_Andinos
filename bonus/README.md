# Bonus: despliegue con Docker

Opción elegida: **despliegue con `docker-compose`** de la API y n8n con el flujo ya importado.

Archivos:

- [`../api/Dockerfile`](../api/Dockerfile): imagen de la API (`python:3.12-slim`, usuario sin privilegios,
  *healthcheck* sobre `/salud`, la BD SQLite en un volumen `/data`).
- [`../docker-compose.yml`](../docker-compose.yml): tres servicios.
  - `api`: la API en el puerto 8000.
  - `n8n-import`: contenedor de un solo uso que crea las credenciales desde las variables de `.env` (n8n las
    cifra), importa los dos flujos y publica el principal. Comparte el volumen con `n8n` para usar la misma
    llave de cifrado.
  - `n8n`: arranca cuando la API está sana y la importación terminó. Dentro de la red de Docker la API se llama
    `http://api:8000` (`API_BASE_URL`).

```bash
cp .env.example .env      # completar GEMINI_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
docker compose up -d --build
python3 flujo/probar_anexo_b.py   # webhook en http://localhost:5678/webhook/solicitud
```

Para dejarlo accesible desde internet bastaría con un VPS con Docker y un proxy inverso con HTTPS (Caddy o
Traefik) delante de n8n, más `WEBHOOK_URL` apuntando al dominio público.

## Prueba (2026-10-20, Docker 29.9.1, Compose 5.6.0)

- `docker compose up -d --build` desde cero: la API queda *healthy*, `n8n-import` termina con código 0 y `n8n`
  arranca con el flujo publicado.
- Los 5 mensajes del Anexo B con `python3 flujo/probar_anexo_b.py` dan los mismos resultados que en la instalación
  con npm: las 5 clasificaciones correctas al primer intento y 4 alertas en Telegram.
- Con `docker compose stop api` el webhook responde `502` (`etapa: "Obtener catálogo"`) y avisa por Telegram;
  al levantar la API de nuevo, los datos siguen en el volumen.

Detener: `docker compose down` (agregar `-v` para borrar también la BD y los datos de n8n).
