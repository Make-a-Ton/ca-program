#!/bin/bash

pip install -r requirements.txt
python3 manage.py migrate
# Run server using manage.py in debug mode or using gunicorn in production
if [ "$DEBUG" = "True" ]; then
  python3 manage.py runserver 0.0.0.0:8000
else
  python3 manage.py collectstatic --noinput

  gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3

fi
