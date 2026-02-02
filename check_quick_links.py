#!/usr/bin/env python
"""
Script to check quick links in the database.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from players.models import QuickLink

def main():
    print("\nAll Quick Links in database:")
    print("=" * 80)
    links = QuickLink.objects.all().order_by('display_order', 'name')
    for link in links:
        print(f"ID: {link.id}")
        print(f"  Name: {link.name}")
        print(f"  URL: {link.url}")
        print(f"  Display Order: {link.display_order}")
        print(f"  Is Active: {link.is_active}")
        print(f"  Is Fixed: {link.is_fixed}")
        print(f"  Icon: {link.icon}")
        print("-" * 80)

    print(f"\nTotal links: {links.count()}")

if __name__ == '__main__':
    main()
