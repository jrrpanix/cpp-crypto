FROM python:3.12-slim

# Match the compose volume path
WORKDIR /app

# Install uv (Astral) and add to PATH
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates \
  && rm -rf /var/lib/apt/lists/* \
  && curl -Ls https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}" \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# If your pyproject.toml is at repo root, copy it from there:
COPY pyproject.toml ./
# If it's actually under server/, use: COPY server/pyproject.toml ./

# Install runtime deps (either from pyproject or explicitly)
# If your project isn't installable by itself yet, install the basics explicitly:
RUN uv pip install --system --upgrade pip && uv pip install --system uvicorn[standard] fastapi

# You don't need to copy code because compose bind-mounts ./server -> /app
# If you want the image to run without the volume, uncomment:
# COPY server/ ./

EXPOSE 8000

# IMPORTANT: target the FastAPI instance "app" inside apps/main.py
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

