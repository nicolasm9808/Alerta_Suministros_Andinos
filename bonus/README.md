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

## Despliegue público (Google Cloud)

- **Swagger:** <https://api.34-26-7-154.sslip.io/docs>
- **Webhook:** `POST https://n8n.34-26-7-154.sslip.io/webhook/solicitud`

| Pieza | Detalle |
|---|---|
| Servidor | VM e2-small (2 vCPU compartidas, 2 GB + 2 GB de swap), Ubuntu 24.04, `us-east1` |
| HTTPS | [Caddy](../deploy/Caddyfile) obtiene certificados de Let's Encrypt solo; los dominios son de [sslip.io](https://sslip.io), que resuelve `api.34-26-7-154.sslip.io` a esa IP, así que no hace falta comprar dominio |
| Puertos | Solo 22, 80 y 443 abiertos (firewall `ufw` + reglas de Google Cloud). La API (8000) y n8n (5678) escuchan solo en `127.0.0.1`: se llega a ellos únicamente a través de Caddy |
| Editor de n8n | No se publica. Caddy solo deja pasar `/webhook/*` hacia n8n. Para administrar: `ssh -L 5678:localhost:5678 usuario@IP` y abrir `http://localhost:5678` |
| Secretos | El `.env` se copia por SSH con permisos `600`; no pasa por GitHub |

Archivos: [`deploy/docker-compose.prod.yml`](../deploy/docker-compose.prod.yml) (se suma al compose base) y
[`deploy/desplegar.sh`](../deploy/desplegar.sh), que en un Ubuntu limpio instala Docker, crea el swap, configura el
firewall, trae el código, copia el `.env` y levanta todo:

```bash
./deploy/desplegar.sh <IP> <usuario> [llave_ssh]            # clona el repo de GitHub
ORIGEN=local ./deploy/desplegar.sh <IP> <usuario>           # envía el último commit local por SSH
```

### Prueba en el servidor (2026-10-20)

Anexo B contra la URL pública ([`anexo_b_respuestas_servidor.json`](../flujo/evidencias/anexo_b_respuestas_servidor.json)):
los 5 mensajes respondieron `201` y las 5 alertas llegaron a Telegram. Mensajes 1, 3, 4 y 5 bien clasificados.
El **mensaje 2 quedó en revisión manual** porque Gemini devolvió errores `503` (modelo sobrecargado) en los dos
intentos. En ese momento la API de Gemini respondía con 503 o tardaba de 15 a 60 s también desde fuera del
servidor y con otros modelos. Es justo el caso que el flujo está diseñado para absorber: la solicitud no se
pierde y alguien la clasifica a mano.

Mejora pendiente que mostró esta prueba: ante un 503 conviene esperar más de 2 s antes de reintentar (por
ejemplo 10 s con *backoff*), o usar un segundo modelo de respaldo en el reintento.

## Prueba (2026-10-20, Docker 29.9.1, Compose 5.6.0)

- `docker compose up -d --build` desde cero: la API queda *healthy*, `n8n-import` termina con código 0 y `n8n`
  arranca con el flujo publicado.
- Los 5 mensajes del Anexo B con `python3 flujo/probar_anexo_b.py` dan los mismos resultados que en la instalación
  con npm: las 5 clasificaciones correctas al primer intento y 4 alertas en Telegram.
- Con `docker compose stop api` el webhook responde `502` (`etapa: "Obtener catálogo"`) y avisa por Telegram;
  al levantar la API de nuevo, los datos siguen en el volumen.

Detener: `docker compose down` (agregar `-v` para borrar también la BD y los datos de n8n).
