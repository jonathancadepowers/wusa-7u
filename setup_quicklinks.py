#!/usr/bin/env python
"""Setup script to create quick_links table and populate it with initial data"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wusa_7u.settings')
django.setup()

from django.db import connection
from players.models import QuickLink

# Create the quick_links table if it doesn't exist
print("Creating quick_links table...")
with connection.cursor() as cursor:
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quick_links (
            id SERIAL PRIMARY KEY,
            name VARCHAR(200) NOT NULL,
            url VARCHAR(500) NOT NULL,
            icon VARCHAR(100) NOT NULL,
            display_order INTEGER NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)
print("Table quick_links created successfully")

# Check if links already exist
existing_count = QuickLink.objects.count()
if existing_count > 0:
    print(f"Quick links already exist ({existing_count} links). Skipping creation.")
else:
    # Create the 6 quick links from the original hardcoded list
    links_data = [
        {
            'name': 'Submit Team Preferences',
            'url': '/players/team_preferences/',
            'icon': 'bi-clipboard-check',
            'display_order': 1
        },
        {
            'name': 'Manager Data',
            'url': '#',
            'icon': 'bi-people-fill',
            'display_order': 2
        },
        {
            'name': 'Pre-Season Info Deck',
            'url': 'https://docs.google.com/presentation/d/1NdUP0QAdI8vp_TmofHwIEyrsXc5GKPEP8b_yEoDk1VQ/edit?usp=sharing',
            'icon': 'bi-file-earmark-slides',
            'display_order': 3
        },
        {
            'name': 'Player Data & Eval Template',
            'url': 'https://docs.google.com/spreadsheets/d/1eo7L0w6liR51sMMBjkwuxvdPCPKYLsFR/edit?usp=sharing&ouid=106177974752139787465&rtpof=true&sd=true',
            'icon': 'bi-table',
            'display_order': 4
        },
        {
            'name': 'Try Out Registrations',
            'url': 'https://docs.google.com/spreadsheets/d/1Kdw5pIWtB9i2cjqwVGx6Iry5fJgojsUj/edit?usp=sharing&ouid=106177974752139787465&rtpof=true&sd=true',
            'icon': 'bi-clipboard-data',
            'display_order': 5
        },
        {
            'name': 'WUSA Field Locations',
            'url': 'https://www.wusa.org/locations',
            'icon': 'bi-geo-alt',
            'display_order': 6
        }
    ]

    for link_data in links_data:
        QuickLink.objects.create(**link_data)
        print(f'Created: {link_data["name"]}')

    print(f'Total quick links created: {QuickLink.objects.count()}')

# Mark migration as fake
print("Marking migration as applied...")
from django.db.migrations.recorder import MigrationRecorder
recorder = MigrationRecorder(connection)
recorder.record_applied('players', '0053_divisionvalidationregistry_quicklink_validationcode')
print("Migration marked as applied successfully!")
