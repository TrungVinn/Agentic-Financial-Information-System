FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Cài các thư viện hệ thống cần cho psycopg2, numpy, pandas...
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements chung ở root (chứa cả Django, psycopg2, langchain, v.v.)
COPY ../requirements.txt /app/requirements.txt

RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy source backend
COPY . /app

# Mặc định Django đang ở DEBUG=True và dùng PostgreSQL từ config.py
# Các biến DB sẽ được truyền từ docker-compose

EXPOSE 8000

# Lệnh chạy mặc định: dev server Django
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]


