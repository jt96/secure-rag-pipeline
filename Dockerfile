# Build stage
FROM python:3.11-slim as builder

WORKDIR /app

# Virtualenv to keep dependencies isolated
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .

# Explicitly pull CPU-only torch. 
# Optimized from original 12GB GPU image -> 2.6GB (~80% reduction).
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir torch==2.9.1 --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt

# Final runtime image
FROM python:3.11-slim

WORKDIR /app

# Copy venv from builder; discards build cache and temp files
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

ENV PYTHONUNBUFFERED=1

COPY . .

# Add src to PYTHONPATH
ENV PYTHONPATH="${PYTHONPATH}:/app/src"

# Forcing new update.
ENV FORCE_UPDATE=v1

EXPOSE 8501

RUN chmod +x start.sh

CMD ["./start.sh"]