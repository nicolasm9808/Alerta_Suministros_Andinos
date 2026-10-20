#!/usr/bin/env bash
# Despliega la API y n8n en un VPS Ubuntu limpio, con HTTPS por Caddy y dominios sslip.io.
#
# Uso, desde la raíz del repo en tu máquina (con .env completo):
#   ./deploy/desplegar.sh <IP_DEL_SERVIDOR> [usuario_ssh] [llave_ssh]
#   ORIGEN=local ./deploy/desplegar.sh ...   # envía el último commit local por SSH en vez de clonar GitHub
#
# Qué hace en el servidor: instala Docker si falta, crea 2 GB de swap, abre solo los puertos
# 22/80/443, clona (o actualiza) el repositorio, copia el .env por SSH y levanta los contenedores.
set -euo pipefail

IP="${1:?Uso: ./deploy/desplegar.sh <IP> [usuario] [llave]}"
USUARIO="${2:-root}"
LLAVE="${3:-$HOME/.ssh/vps_unidrogas}"
REPO="${REPO:-https://github.com/nicolasm9808/Alerta_Suministros_Andinos.git}"
DESTINO="/opt/suministros"
RAIZ="$(cd "$(dirname "$0")/.." && pwd)"

[ -f "$RAIZ/.env" ] || { echo "Falta $RAIZ/.env"; exit 1; }
SSH=(ssh -i "$LLAVE" -o StrictHostKeyChecking=accept-new "$USUARIO@$IP")
SUDO=$([ "$USUARIO" = root ] && echo "" || echo "sudo")

IP_GUIONES="${IP//./-}"
DOMINIO_API="api.$IP_GUIONES.sslip.io"
DOMINIO_N8N="n8n.$IP_GUIONES.sslip.io"

echo "==> Preparando el servidor $IP"
"${SSH[@]}" "SUDO='$SUDO' DESTINO='$DESTINO' REPO='$REPO' USUARIO='$USUARIO' ORIGEN='${ORIGEN:-github}' bash -s" <<'REMOTO'
set -euo pipefail
# Las imágenes "Minimal" de Ubuntu no traen git ni ufw.
if ! command -v git >/dev/null || ! command -v curl >/dev/null || ! command -v ufw >/dev/null; then
  $SUDO apt-get update -qq && $SUDO DEBIAN_FRONTEND=noninteractive apt-get install -y -qq git curl ufw >/dev/null
fi
if ! command -v docker >/dev/null; then
  curl -fsSL https://get.docker.com | $SUDO sh
  [ "$USUARIO" = root ] || $SUDO usermod -aG docker "$USUARIO"
fi
if [ ! -f /swapfile ]; then
  $SUDO fallocate -l 2G /swapfile && $SUDO chmod 600 /swapfile && $SUDO mkswap /swapfile >/dev/null
  $SUDO swapon /swapfile && echo '/swapfile none swap sw 0 0' | $SUDO tee -a /etc/fstab >/dev/null
fi
if command -v ufw >/dev/null; then
  $SUDO ufw allow 22/tcp >/dev/null && $SUDO ufw allow 80/tcp >/dev/null && $SUDO ufw allow 443/tcp >/dev/null
  $SUDO ufw --force enable >/dev/null
fi
$SUDO mkdir -p "$DESTINO" && $SUDO chown "$USUARIO" "$DESTINO"
if [ "$ORIGEN" != local ]; then
  if [ -d "$DESTINO/.git" ]; then git -C "$DESTINO" pull --ff-only; else git clone "$REPO" "$DESTINO"; fi
fi
REMOTO

if [ "${ORIGEN:-github}" = local ]; then
  echo "==> Enviando el commit $(git -C "$RAIZ" rev-parse --short HEAD) por SSH"
  git -C "$RAIZ" archive --format=tar HEAD | "${SSH[@]}" "tar -x -C $DESTINO"
fi

echo "==> Copiando .env (con los dominios públicos)"
{ grep -vE '^(DOMINIO_API|DOMINIO_N8N)=' "$RAIZ/.env"; echo "DOMINIO_API=$DOMINIO_API"; echo "DOMINIO_N8N=$DOMINIO_N8N"; } \
  | "${SSH[@]}" "umask 077 && cat > $DESTINO/.env"

echo "==> Levantando contenedores"
COMPOSE="$SUDO docker compose -f docker-compose.yml -f deploy/docker-compose.prod.yml"
# n8n-import vuelve a cargar el flujo, pero un n8n que ya estaba corriendo sigue usando la versión
# que tiene en memoria: se reinicia para que tome la recién publicada.
"${SSH[@]}" "cd $DESTINO && $COMPOSE up -d --build && $COMPOSE restart n8n"

echo
echo "Listo:"
echo "  API (Swagger): https://$DOMINIO_API/docs"
echo "  Webhook:       POST https://$DOMINIO_N8N/webhook/solicitud"
echo "  Editor n8n:    ssh -i $LLAVE -L 5678:localhost:5678 $USUARIO@$IP   y abrir http://localhost:5678"
