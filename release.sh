#!/bin/bash
# Release script for Heroku

# Fake migrations 0053, 0054, 0055, and 0056 if they haven't been applied yet
# (these migrations have conflicts with existing tables on Heroku)
python manage.py migrate players 0053 --fake --noinput 2>/dev/null || true
python manage.py migrate players 0054 --fake --noinput 2>/dev/null || true
python manage.py migrate players 0055 --fake --noinput 2>/dev/null || true
python manage.py migrate players 0056 --fake --noinput 2>/dev/null || true

# Run normal migrations
python manage.py migrate --noinput

# Run the is_fixed column fix script
python fix_is_fixed_column.py 2>/dev/null || true
