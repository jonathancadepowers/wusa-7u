from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from .models import Player
import pandas as pd
import os
from datetime import datetime


def settings_view(request):
    """Main settings page"""
    return render(request, 'players/settings.html')


@require_http_methods(["POST"])
def import_players_view(request):
    """Handle Excel file upload and import"""
    if 'excel_file' not in request.FILES:
        return JsonResponse({
            'success': False,
            'error': 'No file uploaded'
        }, status=400)

    excel_file = request.FILES['excel_file']

    # Validate file extension
    if not excel_file.name.endswith('.xlsx'):
        return JsonResponse({
            'success': False,
            'error': 'Invalid file type. Please upload an Excel file (.xlsx)'
        }, status=400)

    try:
        # Save file temporarily
        file_path = default_storage.save(f'tmp/{excel_file.name}', ContentFile(excel_file.read()))
        full_path = default_storage.path(file_path)

        # Read Excel file
        df = pd.read_excel(full_path)

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
            default_storage.delete(file_path)
            return JsonResponse({
                'success': False,
                'error': f'Missing required columns: {", ".join(missing_columns)}'
            }, status=400)

        # Process the data
        players_to_create = []
        errors = []

        for idx, row in df.iterrows():
            try:
                # Handle school field
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

                # Convert birthday to date
                birthday_value = pd.to_datetime(row['Enrollee Birthday'], errors='coerce')
                if pd.isna(birthday_value):
                    raise ValueError(f"Invalid birthday")
                birthday = birthday_value.date()

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
                errors.append({
                    'row': idx + 2,
                    'name': f"{row.get('Enrollee First Name', 'Unknown')} {row.get('Enrollee Last Name', 'Unknown')}",
                    'error': str(e)
                })

        # Import the players
        if players_to_create:
            Player.objects.bulk_create(players_to_create)

        # Clean up temp file
        default_storage.delete(file_path)

        # Return success response
        return JsonResponse({
            'success': True,
            'total_rows': len(df),
            'imported': len(players_to_create),
            'errors': errors,
            'total_players': Player.objects.count()
        })

    except Exception as e:
        # Clean up temp file if it exists
        if 'file_path' in locals():
            default_storage.delete(file_path)

        return JsonResponse({
            'success': False,
            'error': f'Error processing file: {str(e)}'
        }, status=500)
