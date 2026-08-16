FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Librerías de sistema para WeasyPrint (Pango/Cairo) y psycopg.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt requirements-pdf.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-pdf.txt

COPY . .

EXPOSE 8000
CMD ["/app/docker-entrypoint.sh"]
