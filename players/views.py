from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, Http404
from django.views.decorators.http import require_http_methods
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.contrib import messages
from django.core.paginator import Paginator
from .models import Player, Team
import pandas as pd
import os
from datetime import datetime


def settings_view(request):
    """Main settings page"""
    return render(request, 'players/settings.html')


def players_list_view(request):
    """List all players with search, sorting, and pagination"""
    search_query = request.GET.get('search', '')
    sort_by = request.GET.get('sort', 'last_name')
    order = request.GET.get('order', 'asc')

    players = Player.objects.all()

    # Apply search
    if search_query:
        from django.db.models import Q
        players = players.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(school__icontains=search_query) |
            Q(parent_email_1__icontains=search_query) |
            Q(parent_phone_1__icontains=search_query)
        )

    # Apply sorting
    valid_sort_fields = ['last_name', 'first_name', 'birthday', 'school', 'jersey_size', 'parent_email_1']
    if sort_by in valid_sort_fields:
        if order == 'desc':
            players = players.order_by(f'-{sort_by}')
        else:
            players = players.order_by(sort_by)
    else:
        players = players.order_by('last_name', 'first_name')

    # Pagination
    paginator = Paginator(players, 25)  # 25 players per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'sort_by': sort_by,
        'order': order,
        'total_players': Player.objects.count()
    }
    return render(request, 'players/players_list.html', context)


def player_detail_view(request, pk):
    """View and edit a single player"""
    player = get_object_or_404(Player, pk=pk)

    if request.method == 'POST':
        # Update player
        player.first_name = request.POST.get('first_name')
        player.last_name = request.POST.get('last_name')
        player.birthday = request.POST.get('birthday')
        player.history = request.POST.get('history') or None
        player.school = request.POST.get('school') or None
        player.conflict = request.POST.get('conflict') or None
        player.additional_registration_info = request.POST.get('additional_registration_info') or None
        player.parent_phone_1 = request.POST.get('parent_phone_1')
        player.parent_email_1 = request.POST.get('parent_email_1')
        player.parent_phone_2 = request.POST.get('parent_phone_2') or None
        player.parent_email_2 = request.POST.get('parent_email_2') or None
        player.jersey_size = request.POST.get('jersey_size') or None
        player.manager_volunteer_name = request.POST.get('manager_volunteer_name') or None
        player.assistant_manager_volunteer_name = request.POST.get('assistant_manager_volunteer_name') or None

        player.save()
        messages.success(request, f'Player {player.first_name} {player.last_name} updated successfully!')
        return redirect('players:detail', pk=player.pk)

    context = {'player': player}
    return render(request, 'players/player_detail.html', context)


def player_create_view(request):
    """Create a new player"""
    if request.method == 'POST':
        player = Player(
            first_name=request.POST.get('first_name'),
            last_name=request.POST.get('last_name'),
            birthday=request.POST.get('birthday'),
            history=request.POST.get('history') or None,
            school=request.POST.get('school') or None,
            conflict=request.POST.get('conflict') or None,
            additional_registration_info=request.POST.get('additional_registration_info') or None,
            parent_phone_1=request.POST.get('parent_phone_1'),
            parent_email_1=request.POST.get('parent_email_1'),
            parent_phone_2=request.POST.get('parent_phone_2') or None,
            parent_email_2=request.POST.get('parent_email_2') or None,
            jersey_size=request.POST.get('jersey_size') or None,
            manager_volunteer_name=request.POST.get('manager_volunteer_name') or None,
            assistant_manager_volunteer_name=request.POST.get('assistant_manager_volunteer_name') or None,
        )
        player.save()
        messages.success(request, f'Player {player.first_name} {player.last_name} created successfully!')
        return redirect('players:list')

    return render(request, 'players/player_create.html')


def player_delete_view(request, pk):
    """Delete a player"""
    player = get_object_or_404(Player, pk=pk)

    if request.method == 'POST':
        player_name = f"{player.first_name} {player.last_name}"
        player.delete()
        messages.success(request, f'Player {player_name} deleted successfully!')
        return redirect('players:list')

    context = {'player': player}
    return render(request, 'players/player_confirm_delete.html', context)


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
                # Skip rows where Enrollment Type is not "Player"
                enrollment_type = row.get('Enrollment Type')
                if pd.isna(enrollment_type) or str(enrollment_type).strip().lower() != 'player':
                    continue

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


def team_detail_view(request, team_secret):
    """Display team info and roster based on manager_secret"""
    try:
        team = Team.objects.get(manager_secret=team_secret)
    except Team.DoesNotExist:
        raise Http404("Team not found")

    # Get all players assigned to this team
    players = team.players.all().order_by('last_name', 'first_name')

    context = {
        'team': team,
        'players': players
    }
    return render(request, 'players/team_detail.html', context)
