FROM python:3.11-slim

WORKDIR /app

# Install system deps (poppler-utils for pdf2image)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    poppler-utils \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python deps
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared modules
COPY backend/common/ /app/common/

# Copy service code
COPY backend/Information-Extraction/unified/ /app/Information-Extraction/unified/

WORKDIR /app/Information-Extraction/unified

EXPOSE 8006

CMD ["python", "unified_pdf_extraction_service.py"]
