FROM python:3.11-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python deps
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared modules
COPY backend/common/ /app/common/

# Copy service code
COPY backend/Database/milvus_server/ /app/Database/milvus_server/

WORKDIR /app/Database/milvus_server

EXPOSE 8000

CMD ["python", "milvus_api.py"]
