#!/usr/bin/env bash
# Render build script — runs before the app starts
# Installs system-level dependencies (Tesseract OCR + Poppler for pdf2image)
# then installs Python packages.

set -e  # Exit on any error

echo "📦 Installing system dependencies..."
apt-get update -qq
apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    poppler-utils

echo "🐍 Installing Python dependencies..."
pip install --no-cache-dir -r requirements.txt

echo "✅ Build complete"
