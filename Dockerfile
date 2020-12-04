FROM python:3.8.3-alpine

WORKDIR /usr/src/app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1


RUN pip install --upgrade pip
RUN apk update && apk add gcc postgresql-dev dos2unix musl-dev libc-dev make libffi-dev openssl-dev python3-dev \
    libxml2-dev libxslt-dev zlib-dev jpeg-dev \
&& pip3 install --upgrade --no-cache-dir pip setuptools==49.6.0 \
&& pip install psycopg2-binary==2.8.6

COPY ./requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN chmod +x /usr/src/app/entrypoint.sh

ENTRYPOINT ["/usr/src/app/entrypoint.sh"]