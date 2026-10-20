# Se construye desde la raíz del repo (necesita sql/datos_prueba.sql):
#   docker build -f api/Dockerfile -t suministros-api .
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DATABASE_PATH=/data/suministros.db

WORKDIR /app/api
COPY api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY sql/datos_prueba.sql /app/sql/datos_prueba.sql
COPY api/app ./app
COPY api/migrations ./migrations

RUN useradd --create-home appuser && mkdir -p /data && chown appuser /data
USER appuser

EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=3s --retries=5 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/salud')"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
