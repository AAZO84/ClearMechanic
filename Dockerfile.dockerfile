# Imagen base
FROM python:3.13-slim

# Evita prompts en instalaciones
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Paquetes del sistema necesarios para pyodbc y SQL Server ODBC
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl ca-certificates gnupg apt-transport-https \
        unixodbc unixodbc-dev && \
    rm -rf /var/lib/apt/lists/*

# Repositorio de Microsoft (ODBC Driver 18 para SQL Server - Debian 12 / Bookworm)
RUN set -eux; \
    mkdir -p /etc/apt/keyrings; \
    curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /etc/apt/keyrings/microsoft.gpg; \
    echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/microsoft.gpg] https://packages.microsoft.com/debian/12/prod bookworm main" \
    > /etc/apt/sources.list.d/mssql-release.list; \
    apt-get update; \
    ACCEPT_EULA=Y apt-get install -y --no-install-recommends msodbcsql18; \
    rm -rf /var/lib/apt/lists/*

# Directorio de trabajo
WORKDIR /app

# Instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código
COPY . .

# Comando de arranque (Railway usa la variable $PORT)
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]


