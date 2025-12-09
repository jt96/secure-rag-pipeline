# Build stage
FROM python:3.11-slim as builder

WORKDIR /app

# Virtualenv to keep dependencies isolated
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .

# Explicitly pull CPU-only torch to avoid massive NVIDIA driver bloat (~1.5GB saved)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir torch==2.9.1 --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt

# Final runtime image
FROM python:3.11-slim

WORKDIR /app

# Copy venv from builder; discards build cache and temp files
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY . .

EXPOSE 8501

RUN chmod +x start.sh

CMD ["./start.sh"]