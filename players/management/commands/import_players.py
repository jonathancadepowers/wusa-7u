"""
Django management command to import player data from Excel files.

Usage:
    python manage.py import_players <excel_file_path> [options]

Examples:
    python manage.py import_players /path/to/players.xlsx
    python manage.py import_players /path/to/players.xlsx --dry-run
    python manage.py import_players /path/to/players.xlsx --clear
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from players.models import Player
import pandas as pd
from datetime import datetime


class Command(BaseCommand):
    help = 'Import player data from an Excel file'

    def add_arguments(self, parser):
        parser.add_argument(
            'excel_file',
            type=str,
            help='Path to the Excel file to import'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview the import without saving to database'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear all existing player records before importing'
        )

    def handle(self, *args, **options):
        excel_file = options['excel_file']
        dry_run = options['dry_run']
        clear_existing = options['clear']

        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(self.style.SUCCESS('Player Data Import Tool'))
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(f'File: {excel_file}')
        self.stdout.write(f'Mode: {"DRY RUN (no changes will be saved)" if dry_run else "LIVE IMPORT"}')
        self.stdout.write(f'Clear existing: {"YES" if clear_existing else "NO"}')
        self.stdout.write(self.style.SUCCESS('=' * 80))

        # Read the Excel file
        try:
            df = pd.read_excel(excel_file)
            self.stdout.write(self.style.SUCCESS(f'✓ Successfully read Excel file: {len(df)} rows found'))
        except Exception as e:
            raise CommandError(f'Error reading Excel file: {e}')

        # Validate required columns
        required_columns = [
            'Enrollee Last Name',
            'Enrollee First Name',
            'Enrollee Birthday',
            'Customer Phone Number',
            'Customer Email Address',
        ]

        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise CommandError(f'Missing required columns: {", ".join(missing_columns)}')

        self.stdout.write(self.style.SUCCESS('✓ All required columns present'))

        # Process the data
        players_to_create = []
        errors = []

        for idx, row in df.iterrows():
            try:
                # Skip rows where Enrollment Type is not "Player"
                enrollment_type = row.get('Enrollment Type')
                if pd.isna(enrollment_type) or str(enrollment_type).strip().lower() != 'player':
                    continue

                # Handle school field (combine School + Other School)
                school = row.get('School')
                if pd.notna(row.get('Other School')) and str(school).lower() == 'other':
                    school = row['Other School']

                # Combine additional info fields
                additional_info_parts = []
                if pd.notna(row.get('Additional Information')):
                    additional_info_parts.append(f"Additional Info: {row['Additional Information']}")
                if pd.notna(row.get('Coach/Player Request')):
                    additional_info_parts.append(f"Coach/Player Request: {row['Coach/Player Request']}")
                if pd.notna(row.get('Special Request')):
                    additional_info_parts.append(f"Special Request: {row['Special Request']}")
                if pd.notna(row.get('Pitcher Interest')):
                    additional_info_parts.append(f"Pitcher Interest: {row['Pitcher Interest']}")
                if pd.notna(row.get('Pitching Experience')):
                    additional_info_parts.append(f"Pitching Experience: {row['Pitching Experience']}")
                if pd.notna(row.get('Pitching Level')):
                    additional_info_parts.append(f"Pitching Level: {row['Pitching Level']}")
                if pd.notna(row.get('Catcher Interest')):
                    additional_info_parts.append(f"Catcher Interest: {row['Catcher Interest']}")

                additional_info = "\n".join(additional_info_parts) if additional_info_parts else None

                # Convert birthday to date (allow blank/null birthdays)
                birthday_value = pd.to_datetime(row['Enrollee Birthday'], errors='coerce')
                birthday = birthday_value.date() if pd.notna(birthday_value) else None

                # Create player object
                player = Player(
                    last_name=row['Enrollee Last Name'],
                    first_name=row['Enrollee First Name'],
                    birthday=birthday,
                    history=row.get('New vs Returning') if pd.notna(row.get('New vs Returning')) else None,
                    school=school if pd.notna(school) else None,
                    conflict=row.get('Day Conflict') if pd.notna(row.get('Day Conflict')) else None,
                    additional_registration_info=additional_info,
                    parent_phone_1=row['Customer Phone Number'],
                    parent_email_1=row['Customer Email Address'],
                    parent_phone_2=row.get('Customer 2 Phone Number') if pd.notna(row.get('Customer 2 Phone Number')) else None,
                    parent_email_2=row.get('Customer 2 Email') if pd.notna(row.get('Customer 2 Email')) else None,
                    jersey_size=row.get('Jersey Size') if pd.notna(row.get('Jersey Size')) else None,
                    manager_volunteer_name=row.get('Manager Name') if pd.notna(row.get('Manager Name')) else None,
                    assistant_manager_volunteer_name=row.get('Asst Manager Name') if pd.notna(row.get('Asst Manager Name')) else None,
                )

                players_to_create.append(player)

            except Exception as e:
                errors.append(f"Row {idx + 2}: {str(e)}")

        # Display summary
        self.stdout.write(self.style.SUCCESS('\n' + '=' * 80))
        self.stdout.write(self.style.SUCCESS('Import Summary'))
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(f'Total rows in Excel: {len(df)}')
        self.stdout.write(f'Players ready to import: {len(players_to_create)}')
        self.stdout.write(f'Errors encountered: {len(errors)}')

        if errors:
            self.stdout.write(self.style.ERROR('\nErrors:'))
            for error in errors[:10]:  # Show first 10 errors
                self.stdout.write(self.style.ERROR(f'  - {error}'))
            if len(errors) > 10:
                self.stdout.write(self.style.ERROR(f'  ... and {len(errors) - 10} more errors'))

        # Show preview of first 3 records
        if players_to_create:
            self.stdout.write(self.style.SUCCESS('\nPreview (first 3 records):'))
            for i, player in enumerate(players_to_create[:3], 1):
                self.stdout.write(f'\n  Record {i}:')
                self.stdout.write(f'    Name: {player.first_name} {player.last_name}')
                self.stdout.write(f'    Birthday: {player.birthday}')
                self.stdout.write(f'    School: {player.school}')
                self.stdout.write(f'    Email: {player.parent_email_1}')
                self.stdout.write(f'    Phone: {player.parent_phone_1}')

        # Perform the import if not dry run
        if not dry_run and players_to_create:
            self.stdout.write(self.style.WARNING('\n' + '=' * 80))

            with transaction.atomic():
                if clear_existing:
                    existing_count = Player.objects.count()
                    Player.objects.all().delete()
                    self.stdout.write(self.style.WARNING(f'✓ Cleared {existing_count} existing player records'))

                Player.objects.bulk_create(players_to_create)
                self.stdout.write(self.style.SUCCESS(f'✓ Successfully imported {len(players_to_create)} players'))

            self.stdout.write(self.style.SUCCESS('=' * 80))
            self.stdout.write(self.style.SUCCESS('Import completed successfully!'))

        elif dry_run:
            self.stdout.write(self.style.WARNING('\n' + '=' * 80))
            self.stdout.write(self.style.WARNING('DRY RUN - No data was saved to the database'))
            self.stdout.write(self.style.WARNING('Run without --dry-run to perform actual import'))

        self.stdout.write(self.style.SUCCESS('=' * 80))
