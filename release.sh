#!/bin/bash
# Release script for Heroku

# Fake migrations that have conflicts with existing tables on Heroku
python manage.py migrate players 0053 --fake --noinput 2>/dev/null || true
python manage.py migrate players 0054 --fake --noinput 2>/dev/null || true
python manage.py migrate players 0055 --fake --noinput 2>/dev/null || true
python manage.py migrate players 0056 --fake --noinput 2>/dev/null || true
python manage.py migrate players 0057 --fake --noinput 2>/dev/null || true
python manage.py migrate players 0058 --fake --noinput 2>/dev/null || true
python manage.py migrate players 0059 --fake --noinput 2>/dev/null || true
python manage.py migrate players 0060 --fake --noinput 2>/dev/null || true
python manage.py migrate players 0061 --fake --noinput 2>/dev/null || true
python manage.py migrate players 0062 --fake --noinput 2>/dev/null || true
python manage.py migrate players 0063 --fake --noinput 2>/dev/null || true
python manage.py migrate players 0064 --fake --noinput 2>/dev/null || true

# Run normal migrations
python manage.py migrate --noinput

# Run the is_fixed column fix script
python fix_is_fixed_column.py 2>/dev/null || true
