#!/usr/src/app bash
python3 manage.py migrate --noinput
python3 manage.py createsuperuser --noinput
python3 manage.py collectstatic
uwsgi --strict --ini uwsgi.ini