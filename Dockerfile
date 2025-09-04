# === Builder stage ===
FROM ghcr.io/astral-sh/uv:python3.13-alpine AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy

RUN apk update \
  && apk add --no-cache gcc musl-dev

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN uv pip install --system --no-cache-dir . \
  && apk del gcc musl-dev \
  && rm -rf $(which uv) \
    /var/cache/apk/*

# === Runtime stage ===
FROM python:3.13-alpine AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.13/site-packages \
                    /usr/local/lib/python3.13/site-packages

COPY . /app

RUN rm -rf $(which pip) $(which pip3) \
    /usr/local/lib/python3.13/site-packages/pip* \
    /usr/local/lib/python3.13/site-packages/setuptools* \
    /usr/local/lib/python3.13/site-packages/pkg_resources* \
    /usr/local/bin/idle* \
    /usr/local/bin/pydoc* \
 && addgroup -S appuser \
 && adduser -S appuser -G appuser \ && mkdir -p /app/logs
 && chown -R appuser:appuser /app

USER appuser

CMD ["python", "main.py"]