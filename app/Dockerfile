FROM python:3.12-alpine AS builder

RUN apk add --no-cache \
    ca-certificates \
    mariadb-dev \
    gcc \
    musl-dev \
    build-base \
    linux-headers \
    uv

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN UV_SYSTEM_PYTHON=1 uv sync --frozen --no-install-project --no-cache

FROM python:3.12-alpine

RUN apk add --no-cache \
    ca-certificates \
    mariadb-connector-c

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/uv.lock /app/uv.lock
COPY --from=builder /usr/bin/uv /usr/local/bin/uv

COPY . .

EXPOSE 5000
CMD ["uv", "run", "--frozen", "uwsgi", "--http", "0.0.0.0:5000", "--wsgi-file", "main.py", "--callable", "app"]