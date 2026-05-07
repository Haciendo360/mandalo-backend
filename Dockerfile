FROM python:3.11-slim

# Instalar dependencias del sistema que Reflex requiere
RUN apt-get update && apt-get install -y \
    unzip \
    curl \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del proyecto
COPY . .

# Railway asigna el puerto via $PORT (normalmente 8080)
EXPOSE 3000

# Arrancar Reflex en producción usando el puerto de Railway
CMD reflex run --env prod --backend-host 0.0.0.0 --frontend-port ${PORT:-3000} --backend-port ${PORT:-8000}
