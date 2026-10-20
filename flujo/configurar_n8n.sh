#!/usr/bin/env bash
# Importa las credenciales (desde .env) y los dos flujos en una instancia local de n8n,
# y publica el flujo principal para que el webhook de producción quede activo.
#
# Uso (desde la raíz del repo, con n8n DETENIDO):
#   ./flujo/configurar_n8n.sh
#   N8N_BIN="n8n" ./flujo/configurar_n8n.sh        # si n8n está instalado globalmente
set -euo pipefail

RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="${ENV_FILE:-$RAIZ/.env}"
[ -f "$ENV_FILE" ] || { echo "Falta $ENV_FILE (copia .env.example y complétalo)"; exit 1; }
set -a; source "$ENV_FILE"; set +a

N8N_BIN="${N8N_BIN:-npx -y n8n@2.43.8}"
: "${GEMINI_API_KEY:?Falta GEMINI_API_KEY en .env}"
: "${TELEGRAM_BOT_TOKEN:?Falta TELEGRAM_BOT_TOKEN en .env}"

# Las credenciales se escriben en un archivo temporal que se borra al terminar;
# n8n las cifra al importarlas en su base de datos.
CREDS="$(mktemp)"
chmod 600 "$CREDS"
trap 'rm -f "$CREDS"' EXIT

python3 - "$CREDS" <<'PY'
import json, os, sys
creds = [
    {"id": "GeminiApiKeySA01", "name": "Gemini API key (x-goog-api-key)", "type": "httpHeaderAuth",
     "data": {"name": "x-goog-api-key", "value": os.environ["GEMINI_API_KEY"]}},
    {"id": "TelegramBotSA0001", "name": "Telegram bot Suministros Andinos", "type": "telegramApi",
     "data": {"accessToken": os.environ["TELEGRAM_BOT_TOKEN"],
              "baseUrl": os.environ.get("TELEGRAM_BASE_URL", "https://api.telegram.org")}},
]
json.dump(creds, open(sys.argv[1], "w"))
PY

$N8N_BIN import:credentials --input="$CREDS"
$N8N_BIN import:workflow --input="$RAIZ/flujo/flujo_alertas_error.json"
$N8N_BIN import:workflow --input="$RAIZ/flujo/flujo_solicitudes.json"
$N8N_BIN publish:workflow --id=SolicitudesSA001

echo
echo "Listo. Inicia n8n con las variables del .env:"
echo "  set -a; source .env; set +a; $N8N_BIN start"
echo "Webhook: POST http://localhost:${N8N_PORT:-5678}/webhook/solicitud"
