# Imagen base de Python
FROM python:3.13-slim

# Instalar dependencias del sistema para pyodbc y SQL Server
RUN apt-get update && \
    apt-get install -y curl gnupg apt-transport-https unixodbc unixodbc-dev && \
    curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - && \
    curl https://packages.microsoft.com/config/debian/12/prod.list > /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update && ACCEPT_EULA=Y apt-get install -y msodbcsql18 && \
    rm -rf /var/lib/apt/lists/*

# Directorio de trabajo
WORKDIR /app

# Instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código
COPY . .

# Comando para iniciar FastAPI con uvicorn.
# Railway expone el puerto en la variable $PORT, así que la usamos.
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
