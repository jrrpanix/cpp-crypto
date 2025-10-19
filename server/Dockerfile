FROM python:3.12-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy pyproject.toml (context is project root now)
COPY pyproject.toml /workspace/pyproject.toml

# Install dependencies using uv
RUN cd /workspace && uv pip install --system --no-cache .

# Copy API server
COPY server/backtest_api.py .

# Create signal_utils directory structure (will be mounted via volume)
RUN mkdir -p /app/signal_utils

# Set Python path
ENV PYTHONPATH=/app

# Expose Flask port
EXPOSE 5000

CMD ["python", "backtest_api.py"]
