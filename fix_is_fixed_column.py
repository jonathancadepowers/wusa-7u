#!/usr/bin/env python
"""
Script to add is_fixed column to quick_links table and populate it.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection

def main():
    with connection.cursor() as cursor:
        # Add the is_fixed column
        print("Adding is_fixed column...")
        cursor.execute("ALTER TABLE quick_links ADD COLUMN IF NOT EXISTS is_fixed BOOLEAN DEFAULT FALSE")

        # Update existing links to mark fixed ones (handle both possible names)
        print("Marking fixed links...")
        cursor.execute("UPDATE quick_links SET is_fixed = TRUE WHERE name IN ('All Division Players', 'Manager Data', 'Manager Contact Info')")

        # Set correct display orders
        print("Setting display orders...")
        cursor.execute("UPDATE quick_links SET display_order = 0 WHERE name = 'All Division Players'")

        # Update Manager Data OR Manager Contact Info (whichever exists)
        cursor.execute("UPDATE quick_links SET display_order = 1, url = '#manager-contact-info', is_active = TRUE WHERE name = 'Manager Data'")
        cursor.execute("UPDATE quick_links SET display_order = 1, url = '#manager-contact-info', is_fixed = TRUE, is_active = TRUE WHERE name = 'Manager Contact Info'")

        # Check if All Division Players exists
        cursor.execute("SELECT COUNT(*) FROM quick_links WHERE name = 'All Division Players'")
        count = cursor.fetchone()[0]

        if count == 0:
            print("Creating All Division Players link...")
            cursor.execute("""
                INSERT INTO quick_links (name, url, icon, display_order, is_active, is_fixed, created_at, updated_at)
                VALUES ('All Division Players', '#all-division-players', 'bi-people-fill', 0, TRUE, TRUE, NOW(), NOW())
            """)

        # Check if Manager Data or Manager Contact Info exists
        cursor.execute("SELECT COUNT(*) FROM quick_links WHERE name IN ('Manager Data', 'Manager Contact Info')")
        manager_count = cursor.fetchone()[0]

        if manager_count == 0:
            print("Creating Manager Data link...")
            cursor.execute("""
                INSERT INTO quick_links (name, url, icon, display_order, is_active, is_fixed, created_at, updated_at)
                VALUES ('Manager Data', '#manager-contact-info', 'bi-person-lines-fill', 1, TRUE, TRUE, NOW(), NOW())
            """)

        print("Success! is_fixed column added and data updated.")

if __name__ == '__main__':
    main()
