FROM python:3.12-slim

# Системные библиотеки: WeasyPrint (Pango/Cairo/HarfBuzz), OpenCV headless (libglib)
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz0b libharfbuzz-subset0 \
        libcairo2 libgdk-pixbuf-2.0-0 libffi8 shared-mime-info \
        libglib2.0-0 fonts-dejavu-core tzdata \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir "uv>=0.8"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH" \
    TZ=UTC

WORKDIR /app

# Зависимости отдельным слоем — пересборка только при изменении lock-файла
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project

COPY . .

CMD ["python", "-m", "bot"]
