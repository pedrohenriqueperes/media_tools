# Usar uma imagem Python oficial e leve (3.12+ necessário para Django 6.0)
FROM python:3.12-slim

# Evitar que o Python gere arquivos .pyc e que o stdout/stderr seja bufferizado
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Definir o diretório de trabalho
WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    ffmpeg \
    libsm6 \
    libxext6 \
    netcat-openbsd \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependências do Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o restante do código
COPY . .

# Criar diretórios necessários
RUN mkdir -p /app/staticfiles /app/media /app/videos

# Copiar o script de entrada e dar permissão de execução
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Expor a porta 8000
EXPOSE 8000

# Definir o script de entrada
ENTRYPOINT ["/app/entrypoint.sh"]
