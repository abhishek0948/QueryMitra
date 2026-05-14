FROM python:3.9-slim

WORKDIR /app

# Install system dependencies (Tesseract OCR + Poppler for pdf2image)
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Make sure the uploads folder exists
RUN mkdir -p uploads

# Expose the port
EXPOSE 10000

# Run with gunicorn (production server)
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "--workers", "2", "--timeout", "120", "run:app"]
