FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Make sure the uploads folder exists
RUN mkdir -p uploads

# Expose the port
EXPOSE 5000

# Run the application
CMD ["python", "run.py"]
