FROM alpine:3.20

RUN apk add --no-cache \
    ca-certificates \
    mariadb-dev \
    gcc \
    musl-dev \
    build-base \
    linux-headers \
    python3 \
    py3-pip

WORKDIR /app

COPY requirements.txt ./
RUN pip3 install --no-cache-dir --retries 10 --default-timeout=100 -r requirements.txt \
    && apk del gcc musl-dev build-base linux-headers

COPY . .

EXPOSE 5000

CMD ["uwsgi", "--http", "0.0.0.0:5000", "--wsgi-file", "main.py", "--callable", "app"]
