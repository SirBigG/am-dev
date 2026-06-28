FROM python:3.12.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

COPY requirements.txt constraints.txt /app/

# Install build deps required to compile psycopg and other native extensions.
# Keep the list conservative but include common headers.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       gcc \
       gettext \
       libpq-dev \
       libssl-dev \
       libffi-dev \
       ca-certificates \
       && pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt -c constraints.txt \
    && apt-get remove -y build-essential gcc \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/* /root/.cache

# Copy app code
COPY . /app

# Add entrypoint
COPY docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh

ENTRYPOINT ["/app/docker-entrypoint.sh"]
