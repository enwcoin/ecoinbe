#!/usr/bin/env bash

set -e

python manage.py makemigrations
python manage.py migrate
gunicorn ecommerce.wsgi:application -b 0.0.0.0:8080 -w 3 -k gevent --name ecoin --timeout 200 --keep-alive 30