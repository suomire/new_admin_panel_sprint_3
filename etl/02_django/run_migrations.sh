#!/usr/src/app bash
python3 manage.py migrate --noinput
python3 manage.py collectstatic
python3 manage.py runserver