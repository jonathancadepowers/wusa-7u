release: python manage.py migrate players 0053 --fake --noinput; python manage.py migrate --noinput
web: daphne -b 0.0.0.0 -p $PORT config.asgi:application
