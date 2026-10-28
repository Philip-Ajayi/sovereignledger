# Multi-stage production container for SovereignLedger on Render
FROM python:3.11-slim-bookworm AS base

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    iptables \
    net-tools \
    iproute2 \
    libsqlite3-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Create non-root user
RUN groupadd -r sovereign && useradd -r -g sovereign -d /app -s /sbin/nologin sovereign

COPY requirements.txt pyproject.toml ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN pip install --no-cache-dir -e .

# Establish directories and permissions
RUN mkdir -p /app/data/incoming /app/db /app/skills/parsers \
    && chown -R sovereign:sovereign /app

USER sovereign

# Render injects $PORT at runtime (defaults to 8080 locally)
ENV PORT=8080
EXPOSE 8080

CMD ["sh", "-c", "python3 -m src.cli serve-web --host 0.0.0.0 --port ${PORT:-8080}"]
