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

# Copy research modules (signal_utils and data_utils)
COPY src/research/signal_utils /app/signal_utils
COPY src/research/data_utils /app/data_utils

# Set Python path
ENV PYTHONPATH=/app

# Expose Flask port
EXPOSE 5000

CMD ["python", "backtest_api.py"]
