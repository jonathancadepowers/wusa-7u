from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Add requests_separate_team_from_sibling column to players table'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            try:
                cursor.execute("""
                    ALTER TABLE players
                    ADD COLUMN IF NOT EXISTS requests_separate_team_from_sibling BOOLEAN DEFAULT FALSE NOT NULL;
                """)
                self.stdout.write(
                    self.style.SUCCESS('Successfully added requests_separate_team_from_sibling column')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error: {e}')
                )
