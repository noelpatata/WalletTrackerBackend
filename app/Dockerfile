FROM python:3.12-alpine

RUN apk add --no-cache \
    ca-certificates \
    mariadb-dev \
    gcc \
    musl-dev \
    build-base \
    linux-headers \
    uv

WORKDIR /app

COPY pyproject.toml ./
RUN UV_SYSTEM_PYTHON=1 uv sync --no-install-project

RUN apk del gcc musl-dev build-base linux-headers

COPY . .

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 5000

CMD ["uwsgi", "--http", "0.0.0.0:5000", "--wsgi-file", "main.py", "--callable", "app"]
