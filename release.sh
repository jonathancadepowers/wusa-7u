#!/bin/bash
# Release script for Heroku

# Fake migrations 0053 and 0054 if they haven't been applied yet
# (these migrations have conflicts with existing tables on Heroku)
python manage.py migrate players 0053 --fake --noinput 2>/dev/null || true
python manage.py migrate players 0054 --fake --noinput 2>/dev/null || true

# Run normal migrations
python manage.py migrate --noinput
