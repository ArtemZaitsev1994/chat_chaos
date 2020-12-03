#!/bin/sh

if [ "$DATABASE" = "postgres" ]
then
  echo "Waiting for postgres..."

  while ! nc -z $POSTGRES_HOST $POSTGRES_PORT; do
      sleep 0.1
  done
fi
  echo "PostgreSQL started"

alembic upgrade head 

exec "$@"