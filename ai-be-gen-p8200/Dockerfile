FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential curl \
    && rm -rf /var/lib/apt/lists/*

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir -p /app/logs

EXPOSE 8200

HEALTHCHECK --interval=10s --timeout=3s --retries=3 \
  CMD curl -f http://localhost:8200/health || exit 1

CMD ["uvicorn", "ai-backend-server:app", "--host", "0.0.0.0", "--port", "8200"]


