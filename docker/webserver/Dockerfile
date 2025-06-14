FROM python:3.12-slim

WORKDIR /app

# Install uv
RUN pip install --no-cache-dir uv

# Copy metadata
COPY pyproject.toml uv.lock* ./

# Install dependencies globally (Docker-safe)
RUN uv pip install --system --upgrade pip && \
    uv pip install --system .

# Copy app code
COPY app ./app

# Run FastAPI app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

