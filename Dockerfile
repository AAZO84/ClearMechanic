FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Railway inyecta $PORT; dejamos un default por si corres local
ENV PORT=8000

# IMPORTANTE: Usa 0.0.0.0 y ${PORT} para que el healthcheck funcione
CMD ["sh","-c","uvicorn main:app --host 0.0.0.0 --port ${PORT}"]

