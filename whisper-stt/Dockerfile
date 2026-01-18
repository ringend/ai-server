FROM python:3.12-slim

WORKDIR /app

# Copy requirements first for caching
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy your application code
COPY . .

# Ensure the script is executable
RUN chmod +x start.docker.sh

EXPOSE 8001

ENTRYPOINT ["./start.docker.sh"]

