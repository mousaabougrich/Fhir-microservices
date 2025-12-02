FROM python:3.11-slim
WORKDIR /app

# Minimal system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Container environment defaults
ENV DEID_BASE_URL=http://deid:8000
ENV DATABASE_URL=postgresql://postgres:root@postgres_feat:5432/featDB
ENV USE_BIOBERT=false
ENV PYTHONUNBUFFERED=1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
