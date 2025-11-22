# Imagen base
FROM python:3.13-slim

ENV DEBIAN_FRONTEND=noninteractive     PYTHONDONTWRITEBYTECODE=1     PYTHONUNBUFFERED=1

# Dependencias del sistema para pyodbc y SQL Server ODBC
RUN apt-get update &&     apt-get install -y --no-install-recommends         curl ca-certificates gnupg apt-transport-https         unixodbc unixodbc-dev &&     rm -rf /var/lib/apt/lists/*

# Repositorio Microsoft ODBC Driver 18 (Debian 12 / bookworm)
RUN set -eux;     mkdir -p /etc/apt/keyrings;     curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /etc/apt/keyrings/microsoft.gpg;     echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/microsoft.gpg] https://packages.microsoft.com/debian/12/prod bookworm main"     > /etc/apt/sources.list.d/mssql-release.list;     apt-get update;     ACCEPT_EULA=Y apt-get install -y --no-install-recommends msodbcsql18;     rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Railway inyecta $PORT
CMD [ "sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}" ]
