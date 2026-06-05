FROM python:3.12-alpine

RUN apk add --no-cache \
    mariadb-dev \
    gcc \
    musl-dev \
    build-base \
    linux-headers

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

RUN apk del gcc musl-dev build-base linux-headers

COPY . .

EXPOSE 5000

CMD ["uwsgi", "--http", "0.0.0.0:5000", "--wsgi-file", "main.py", "--callable", "app"]