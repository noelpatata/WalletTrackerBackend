FROM python:3.12-alpine

RUN apk add --no-cache \
    mariadb-dev \
    gcc \
    musl-dev \
    build-base \
    linux-headers

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

COPY requirements.txt ./
RUN uv pip install --system --no-cache -r requirements.txt

RUN apk del gcc musl-dev build-base linux-headers

COPY . .

EXPOSE 5000

CMD ["uwsgi", "--http", "0.0.0.0:5000", "--wsgi-file", "main.py", "--callable", "app"]
