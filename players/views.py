from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, Http404
from django.views.decorators.http import require_http_methods
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.contrib import messages
from django.core.paginator import Paginator
from django.views.decorators.csrf import csrf_exempt
from django.db import models
from .models import Player, Team, Manager, PlayerRanking, ManagerDaughterRanking, Draft, DraftPick
import pandas as pd
import json
import os
from datetime import datetime


def settings_view(request):
    """Main settings page"""
    from .models import Draft

    # Check if there's an existing draft
    draft_exists = Draft.objects.exists()

    context = {
        'draft_exists': draft_exists
    }
    return render(request, 'players/settings.html', context)


def create_draft_view(request):
    """Create a new draft"""
    from .models import Draft

    if request.method == 'POST':
        draft = Draft(
            rounds=request.POST.get('rounds'),
            status=request.POST.get('status'),
            draft_date=request.POST.get('draft_date'),
            picks_per_round=request.POST.get('picks_per_round'),
            public_url_secret=request.POST.get('public_url_secret'),
            order=request.POST.get('order', '')
        )
        draft.save()
        messages.success(request, 'Draft created successfully!')
        return redirect('players:edit_draft')

    return render(request, 'players/draft_form.html', {'draft': None, 'is_create': True})


def edit_draft_view(request):
    """Edit existing draft or create new one"""
    from .models import Draft
    import string
    import random
    import json

    # Get the first (and should be only) draft
    draft = Draft.objects.first()

    if request.method == 'POST':
        rounds = int(request.POST.get('rounds'))
        picks_per_round = int(request.POST.get('picks_per_round'))
        order = request.POST.get('order', '')

        # Calculate if we need a final round with partial picks
        player_count = Player.objects.count()
        total_regular_picks = rounds * picks_per_round

        # Generate final round draft order if needed
        final_round_draft_order = ''
        if player_count > total_regular_picks:
            # We need extra picks
            extra_picks_needed = player_count - total_regular_picks
            # Parse the order to get team IDs
            if order:
                team_ids = [int(tid) for tid in order.split(',') if tid]
                # Use the first N teams from the draft order for final round
                final_round_teams = team_ids[:extra_picks_needed]
                final_round_draft_order = ','.join(map(str, final_round_teams))

        if draft:
            # Update existing draft
            draft.rounds = rounds
            draft.picks_per_round = picks_per_round
            draft.order = order
            draft.final_round_draft_order = final_round_draft_order
            draft.save()
            messages.success(request, 'Draft updated successfully!')
        else:
            # Create new draft
            draft = Draft(
                rounds=rounds,
                picks_per_round=picks_per_round,
                order=order,
                final_round_draft_order=final_round_draft_order
            )
            draft.save()
            messages.success(request, 'Draft created successfully!')
        return redirect('players:edit_draft')

    is_create = draft is None

    # Calculate default values for new draft
    suggested_rounds = 0
    suggested_picks_per_round = 0

    if is_create:
        # Count players and teams
        player_count = Player.objects.count()
        team_count = Team.objects.count()

        # Calculate suggested rounds (players / teams)
        if team_count > 0:
            suggested_rounds = int(player_count / team_count)
            suggested_picks_per_round = team_count

    # Get total player count
    player_count = Player.objects.count()

    # Check if there are any draft picks
    has_draft_picks = DraftPick.objects.exists()

    # Get all teams for draft order
    all_teams = Team.objects.all().order_by('name')

    # Parse existing draft order if it exists
    ordered_team_ids = []
    if draft and draft.order:
        ordered_team_ids = [int(tid) for tid in draft.order.split(',') if tid]

    # Calculate extra round info if draft exists
    needs_extra_round = False
    total_regular_picks = 0
    extra_picks_needed = 0
    final_round_number = 0
    final_round_team_names = []

    if draft:
        total_regular_picks = draft.rounds * draft.picks_per_round
        if player_count > total_regular_picks:
            needs_extra_round = True
            extra_picks_needed = player_count - total_regular_picks
            final_round_number = draft.rounds + 1

            # Get team names for final round order if it exists
            if draft.final_round_draft_order:
                final_round_team_ids = [int(tid) for tid in draft.final_round_draft_order.split(',') if tid]
                teams_dict = {team.id: team.name for team in all_teams}
                final_round_team_names = [teams_dict.get(tid, '') for tid in final_round_team_ids]

    context = {
        'draft': draft,
        'is_create': is_create,
        'suggested_rounds': suggested_rounds,
        'suggested_picks_per_round': suggested_picks_per_round,
        'all_teams': all_teams,
        'ordered_team_ids': ordered_team_ids,
        'player_count': player_count,
        'needs_extra_round': needs_extra_round,
        'total_regular_picks': total_regular_picks,
        'extra_picks_needed': extra_picks_needed,
        'final_round_number': final_round_number,
        'final_round_team_names': final_round_team_names,
        'has_draft_picks': has_draft_picks,
    }
    return render(request, 'players/draft_form.html', context)


def admin_dashboard_view(request):
    """Admin dashboard with links to main pages"""
    return render(request, 'players/admin_dashboard.html')


def public_portal_view(request):
    """Public portal listing all teams"""
    teams = Team.objects.all().order_by('name')
    context = {
        'teams': teams
    }
    return render(request, 'players/public_portal.html', context)


@require_http_methods(["POST"])
def validate_team_secret_view(request):
    """Validate team secret and return team URL if valid"""
    team_secret = request.POST.get('team_secret', '').strip()

    if not team_secret:
        return JsonResponse({
            'success': False,
            'error': 'Please enter a team secret.'
        }, status=400)

    try:
        team = Team.objects.get(manager_secret=team_secret)
        return JsonResponse({
            'success': True,
            'team_url': f'/teams/{team_secret}/'
        })
    except Team.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Invalid team secret. Please check and try again.'
        }, status=400)


def players_list_view(request):
    """List all players with search, sorting, and pagination"""
    search_query = request.GET.get('search', '')
    sort_by = request.GET.get('sort', 'last_name')
    order = request.GET.get('order', 'asc')

    players = Player.objects.select_related('team').all()

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
    valid_sort_fields = ['last_name', 'first_name', 'team__name', 'school', 'history', 'attended_try_out', 'draftable']
    if sort_by in valid_sort_fields:
        if order == 'desc':
            # For team sorting, handle null values
            if sort_by == 'team__name':
                players = players.order_by(f'-{sort_by}', 'last_name', 'first_name')
            else:
                players = players.order_by(f'-{sort_by}', 'last_name', 'first_name')
        else:
            if sort_by == 'team__name':
                players = players.order_by(f'{sort_by}', 'last_name', 'first_name')
            else:
                players = players.order_by(sort_by, 'last_name', 'first_name')
    else:
        players = players.order_by('last_name', 'first_name')

    # Pagination
    paginator = Paginator(players, 50)  # 50 players per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Get all teams for the team assignment dropdown
    all_teams = Team.objects.all().order_by('name')

    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'sort_by': sort_by,
        'order': order,
        'total_players': Player.objects.count(),
        'all_teams': all_teams
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
        player.attended_try_out = request.POST.get('attended_try_out') == 'on'
        player.draftable = request.POST.get('draftable') == 'on'

        # Handle team assignment
        team_id = request.POST.get('team_id')
        if team_id == '':
            player.team = None
        else:
            try:
                team = Team.objects.get(pk=team_id)
                player.team = team
            except Team.DoesNotExist:
                pass

        player.save()
        messages.success(request, f'Player {player.first_name} {player.last_name} updated successfully!')
        return redirect('players:detail', pk=player.pk)

    # Get all teams for dropdown
    all_teams = Team.objects.all().order_by('name')

    context = {
        'player': player,
        'all_teams': all_teams
    }
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
def assign_manager_team_view(request, pk):
    """Assign or remove a manager from a team"""
    manager = get_object_or_404(Manager, pk=pk)
    team_id = request.POST.get('team_id')

    if team_id == '':  # Remove from team
        # Find and release any team currently managed by this manager
        current_teams = Team.objects.filter(manager=manager)
        for team in current_teams:
            team.manager = None
            team.save()
        return JsonResponse({
            'success': True,
            'message': f'{manager.first_name} {manager.last_name} removed from team',
            'team_name': None
        })
    else:
        # Assign to team
        try:
            team = Team.objects.get(pk=team_id)
            # Release manager from any current team first
            current_teams = Team.objects.filter(manager=manager)
            for current_team in current_teams:
                current_team.manager = None
                current_team.save()
            # Assign to new team
            team.manager = manager
            team.save()
            return JsonResponse({
                'success': True,
                'message': f'{manager.first_name} {manager.last_name} assigned to {team.name}',
                'team_name': team.name
            })
        except Team.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Invalid team selected'
            }, status=400)


@require_http_methods(["POST"])
def assign_player_team_view(request, pk):
    """Assign or remove a player from a team"""
    player = get_object_or_404(Player, pk=pk)
    team_id = request.POST.get('team_id')

    if team_id == '':  # Remove from team
        player.team = None
        player.save()
        return JsonResponse({
            'success': True,
            'message': f'{player.first_name} {player.last_name} removed from team',
            'team_name': None
        })
    else:
        # Assign to team
        try:
            team = Team.objects.get(pk=team_id)
            player.team = team
            player.save()
            return JsonResponse({
                'success': True,
                'message': f'{player.first_name} {player.last_name} assigned to {team.name}',
                'team_name': team.name
            })
        except Team.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Invalid team selected'
            }, status=400)


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
    """Display team info and roster based on manager_secret (read-only)"""
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


def managers_list_view(request):
    """List all managers with search, sorting, and pagination"""
    search_query = request.GET.get('search', '')
    sort_by = request.GET.get('sort', 'last_name')
    order = request.GET.get('order', 'asc')

    managers = Manager.objects.prefetch_related('teams').all()

    # Apply search
    if search_query:
        from django.db.models import Q
        managers = managers.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone__icontains=search_query)
        )

    # Apply sorting
    valid_sort_fields = ['last_name', 'first_name', 'email', 'teams__name']
    if sort_by in valid_sort_fields:
        if order == 'desc':
            if sort_by == 'teams__name':
                managers = managers.order_by(f'-{sort_by}', 'last_name', 'first_name')
            else:
                managers = managers.order_by(f'-{sort_by}', 'last_name', 'first_name')
        else:
            if sort_by == 'teams__name':
                managers = managers.order_by(f'{sort_by}', 'last_name', 'first_name')
            else:
                managers = managers.order_by(sort_by, 'last_name', 'first_name')
    else:
        managers = managers.order_by('last_name', 'first_name')

    # Pagination
    paginator = Paginator(managers, 25)  # 25 managers per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Get unassigned teams (teams with no manager)
    unassigned_teams = Team.objects.filter(manager__isnull=True).order_by('name')

    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'sort_by': sort_by,
        'order': order,
        'total_managers': Manager.objects.count(),
        'unassigned_teams': unassigned_teams
    }
    return render(request, 'players/managers_list.html', context)


def manager_detail_view(request, pk):
    """View and edit a single manager"""
    manager = get_object_or_404(Manager, pk=pk)

    if request.method == 'POST':
        # Update manager
        manager.first_name = request.POST.get('first_name')
        manager.last_name = request.POST.get('last_name')
        manager.email = request.POST.get('email')
        manager.phone = request.POST.get('phone')

        # Update daughter assignment
        daughter_id = request.POST.get('daughter')
        if daughter_id:
            manager.daughter = Player.objects.get(pk=daughter_id)
        else:
            manager.daughter = None

        manager.save()
        messages.success(request, f'Manager {manager.first_name} {manager.last_name} updated successfully!')
        return redirect('players:manager_detail', pk=manager.pk)

    # Get available players (not already assigned to another manager as daughter)
    available_players = Player.objects.filter(manager_parent__isnull=True).order_by('last_name', 'first_name')

    # If this manager already has a daughter, include her in the list
    if manager.daughter:
        available_players = available_players | Player.objects.filter(pk=manager.daughter.pk)
        available_players = available_players.distinct().order_by('last_name', 'first_name')

    context = {
        'manager': manager,
        'available_players': available_players
    }
    return render(request, 'players/manager_detail.html', context)


def manager_create_view(request):
    """Create a new manager"""
    if request.method == 'POST':
        manager = Manager(
            first_name=request.POST.get('first_name'),
            last_name=request.POST.get('last_name'),
            email=request.POST.get('email'),
            phone=request.POST.get('phone'),
        )
        manager.save()
        messages.success(request, f'Manager {manager.first_name} {manager.last_name} created successfully!')
        return redirect('players:managers_list')

    return render(request, 'players/manager_create.html')


def manager_delete_view(request, pk):
    """Delete a manager"""
    manager = get_object_or_404(Manager, pk=pk)

    if request.method == 'POST':
        manager_name = f"{manager.first_name} {manager.last_name}"
        manager.delete()
        messages.success(request, f'Manager {manager_name} deleted successfully!')
        return redirect('players:managers_list')

    context = {'manager': manager}
    return render(request, 'players/manager_confirm_delete.html', context)


def teams_list_view(request):
    """List all teams with search, sorting, and pagination"""
    from django.db.models import Count
    search_query = request.GET.get('search', '')
    sort_by = request.GET.get('sort', 'name')
    order = request.GET.get('order', 'asc')

    teams = Team.objects.select_related('manager').annotate(player_count=Count('players')).all()

    # Apply search
    if search_query:
        from django.db.models import Q
        teams = teams.filter(
            Q(name__icontains=search_query) |
            Q(manager__first_name__icontains=search_query) |
            Q(manager__last_name__icontains=search_query)
        )

    # Apply sorting
    valid_sort_fields = ['name', 'manager__last_name', 'player_count']
    if sort_by in valid_sort_fields:
        if order == 'desc':
            teams = teams.order_by(f'-{sort_by}', 'name')
        else:
            teams = teams.order_by(sort_by, 'name')
    else:
        teams = teams.order_by('name')

    # Pagination
    paginator = Paginator(teams, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Get unassigned managers
    unassigned_managers = Manager.objects.filter(teams__isnull=True).order_by('last_name', 'first_name')

    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'sort_by': sort_by,
        'order': order,
        'total_teams': Team.objects.count(),
        'unassigned_managers': unassigned_managers
    }
    return render(request, 'players/teams_list.html', context)


def team_edit_view(request, pk):
    """View and edit a single team"""
    team = get_object_or_404(Team, pk=pk)

    if request.method == 'POST':
        team.name = request.POST.get('name')
        team.manager_secret = request.POST.get('manager_secret')

        # Handle manager assignment
        manager_id = request.POST.get('manager_id')
        if manager_id == '':
            team.manager = None
        else:
            try:
                manager = Manager.objects.get(pk=manager_id)
                team.manager = manager
            except Manager.DoesNotExist:
                pass

        team.save()
        messages.success(request, f'Team {team.name} updated successfully!')
        return redirect('players:team_edit', pk=team.pk)

    # Get all managers for dropdown
    all_managers = Manager.objects.all().order_by('last_name', 'first_name')

    # Get all players assigned to this team
    team_players = Player.objects.filter(team=team).order_by('first_name', 'last_name')

    context = {
        'team': team,
        'all_managers': all_managers,
        'team_players': team_players
    }
    return render(request, 'players/team_edit.html', context)


def team_create_view(request):
    """Create a new team"""
    if request.method == 'POST':
        team = Team(
            name=request.POST.get('name'),
            manager_secret=request.POST.get('manager_secret'),
        )

        # Handle manager assignment
        manager_id = request.POST.get('manager_id')
        if manager_id:
            try:
                manager = Manager.objects.get(pk=manager_id)
                team.manager = manager
            except Manager.DoesNotExist:
                pass

        team.save()
        messages.success(request, f'Team {team.name} created successfully!')
        return redirect('players:teams_list')

    # Get all managers for dropdown
    all_managers = Manager.objects.all().order_by('last_name', 'first_name')

    context = {'all_managers': all_managers}
    return render(request, 'players/team_create.html', context)


def team_delete_view(request, pk):
    """Delete a team"""
    team = get_object_or_404(Team, pk=pk)

    if request.method == 'POST':
        team_name = team.name
        team.delete()
        messages.success(request, f'Team {team_name} deleted successfully!')
        return redirect('players:teams_list')

    context = {'team': team}
    return render(request, 'players/team_confirm_delete.html', context)


def player_rankings_view(request):
    """Create or update player rankings (top 20 players)"""
    # Get team_secret from URL parameter
    team_secret = request.GET.get('team_secret', request.POST.get('team_secret', ''))

    # Find the manager associated with this team_secret
    manager = None
    if team_secret:
        try:
            team = Team.objects.get(manager_secret=team_secret)
            manager = team.manager
        except Team.DoesNotExist:
            messages.error(request, 'Invalid team secret.')

    if request.method == 'POST':
        # Get the rankings data from the form (comma-separated player IDs in ranked order)
        rankings_data = request.POST.get('rankings', '')

        if rankings_data:
            # Parse the comma-separated IDs
            player_ids = [int(pid) for pid in rankings_data.split(',') if pid]

            # Create a JSON structure with rank and player ID
            rankings_json = json.dumps([
                {"rank": idx + 1, "player_id": player_id}
                for idx, player_id in enumerate(player_ids)
            ])

            # Update or create ranking for this manager (ensures only one ranking per manager)
            if manager:
                PlayerRanking.objects.update_or_create(
                    manager=manager,
                    defaults={'ranking': rankings_json}
                )
            else:
                # If no manager, just create a new ranking
                PlayerRanking.objects.create(ranking=rankings_json)

            messages.success(request, f'Player rankings saved successfully! ({len(player_ids)} players ranked)')

            # Redirect back to team page if team_secret was provided
            if team_secret:
                return redirect('players:team_detail', team_secret=team_secret)
            else:
                return redirect('players:player_rankings')
        else:
            messages.error(request, 'No rankings data provided.')

    # Load existing rankings for this manager
    existing_ranking = None
    ranked_player_ids = []
    if manager:
        try:
            existing_ranking = PlayerRanking.objects.get(manager=manager)
            # Parse the JSON to get player IDs in order
            rankings_data = json.loads(existing_ranking.ranking)
            ranked_player_ids = [item['player_id'] for item in rankings_data]
        except PlayerRanking.DoesNotExist:
            pass

    # Get all players for the dropdown, ordered by name
    all_players = Player.objects.all().order_by('last_name', 'first_name')

    # Get IDs of all players who are managers' daughters
    manager_daughter_ids = list(Manager.objects.filter(daughter__isnull=False).values_list('daughter_id', flat=True))

    context = {
        'all_players': all_players,
        'team_secret': team_secret,
        'manager': manager,
        'ranked_player_ids': json.dumps(ranked_player_ids),  # Pass as JSON for JavaScript
        'manager_daughter_ids': json.dumps(manager_daughter_ids)  # Pass as JSON for JavaScript
    }
    return render(request, 'players/player_rankings.html', context)


def manager_daughter_rankings_view(request):
    """Create or update manager daughter rankings"""
    # Get team_secret from URL parameter
    team_secret = request.GET.get('team_secret', request.POST.get('team_secret', ''))

    # Find the manager associated with this team_secret
    manager = None
    if team_secret:
        try:
            team = Team.objects.get(manager_secret=team_secret)
            manager = team.manager
        except Team.DoesNotExist:
            messages.error(request, 'Invalid team secret.')

    if request.method == 'POST':
        # Get the rankings data from the form (comma-separated player IDs in ranked order)
        rankings_data = request.POST.get('rankings', '')

        if rankings_data:
            # Parse the comma-separated IDs
            player_ids = [int(pid) for pid in rankings_data.split(',') if pid]

            # Create a JSON structure with rank and player ID
            rankings_json = json.dumps([
                {"rank": idx + 1, "player_id": player_id}
                for idx, player_id in enumerate(player_ids)
            ])

            # Update or create ranking for this manager (ensures only one ranking per manager)
            if manager:
                ManagerDaughterRanking.objects.update_or_create(
                    manager=manager,
                    defaults={'ranking': rankings_json}
                )
            else:
                # If no manager, just create a new ranking
                ManagerDaughterRanking.objects.create(ranking=rankings_json)

            messages.success(request, f'Manager daughter rankings saved successfully! ({len(player_ids)} players ranked)')

            # Redirect back to team page if team_secret was provided
            if team_secret:
                return redirect('players:team_detail', team_secret=team_secret)
            else:
                return redirect('players:manager_daughter_rankings')
        else:
            messages.error(request, 'No rankings data provided.')

    # Load existing rankings for this manager
    existing_ranking = None
    ranked_player_ids = []
    if manager:
        try:
            existing_ranking = ManagerDaughterRanking.objects.get(manager=manager)
            # Parse the JSON to get player IDs in order
            rankings_data = json.loads(existing_ranking.ranking)
            ranked_player_ids = [item['player_id'] for item in rankings_data]
        except ManagerDaughterRanking.DoesNotExist:
            pass

    # Get only players who are managers' daughters, ordered by name
    manager_daughter_ids = Manager.objects.filter(daughter__isnull=False).values_list('daughter_id', flat=True)
    all_players = Player.objects.filter(id__in=manager_daughter_ids).order_by('last_name', 'first_name')

    context = {
        'all_players': all_players,
        'team_secret': team_secret,
        'manager': manager,
        'ranked_player_ids': json.dumps(ranked_player_ids),  # Pass as JSON for JavaScript
        'manager_daughter_ids': json.dumps(list(manager_daughter_ids))  # Pass as JSON for JavaScript
    }
    return render(request, 'players/manager_daughter_rankings.html', context)


def run_draft_view(request):
    """Run the draft - display grid of rounds and picks"""
    # Get the most recent draft
    try:
        draft = Draft.objects.latest('created_at')
    except Draft.DoesNotExist:
        messages.error(request, 'No draft found. Please create a draft first.')
        return redirect('players:create_draft')

    # Validate draft has all required fields
    errors = []

    if not draft.rounds or draft.rounds <= 0:
        errors.append('Draft must have a valid number of rounds.')

    if not draft.picks_per_round or draft.picks_per_round <= 0:
        errors.append('Draft must have a valid number of picks per round.')

    # Check if order field has team assignments
    if not draft.order or draft.order.strip() == '':
        errors.append('Draft order has not been set. Please configure the draft order.')
    else:
        # Try to parse the order field (should be comma-separated team IDs or JSON)
        try:
            order_data = draft.order.strip()
            if order_data.startswith('['):
                # JSON format
                team_order = json.loads(order_data)
            else:
                # Comma-separated format
                team_order = [tid.strip() for tid in order_data.split(',') if tid.strip()]

            if not team_order or len(team_order) == 0:
                errors.append('No teams have been assigned to the draft order.')
            elif len(team_order) != draft.picks_per_round:
                errors.append(f'Draft order is incomplete. Expected {draft.picks_per_round} teams but only {len(team_order)} are assigned.')
        except (json.JSONDecodeError, ValueError):
            errors.append('Draft order data is invalid.')

    # If there are validation errors, show error page
    if errors:
        context = {
            'draft': draft,
            'errors': errors,
            'show_grid': False,
        }
        return render(request, 'players/run_draft.html', context)

    # Create ranges for rounds and picks
    rounds = list(range(1, draft.rounds + 1))
    picks = list(range(1, draft.picks_per_round + 1))

    # Parse the order field to get team objects
    order_data = draft.order.strip()
    if order_data.startswith('['):
        team_ids = json.loads(order_data)
    else:
        team_ids = [int(tid.strip()) for tid in order_data.split(',') if tid.strip()]

    # Get team objects in order
    teams_dict = {team.id: team for team in Team.objects.filter(id__in=team_ids)}
    ordered_teams = [teams_dict[tid] for tid in team_ids]

    # Create a mapping of round -> pick -> team for snake draft
    pick_assignments = {}
    for round_num in rounds:
        pick_assignments[round_num] = {}
        if round_num % 2 == 1:  # Odd rounds: normal order
            for pick_num in picks:
                team_index = pick_num - 1
                pick_assignments[round_num][pick_num] = ordered_teams[team_index]
        else:  # Even rounds: reversed order (snake draft)
            for pick_num in picks:
                team_index = len(ordered_teams) - pick_num
                pick_assignments[round_num][pick_num] = ordered_teams[team_index]

    # Load existing draft picks - structure as nested dict like pick_assignments
    existing_picks = DraftPick.objects.select_related('player', 'team').all()
    draft_picks_map = {}
    for draft_pick in existing_picks:
        if draft_pick.round not in draft_picks_map:
            draft_picks_map[draft_pick.round] = {}
        draft_picks_map[draft_pick.round][draft_pick.pick] = {
            'player_name': f"{draft_pick.player.first_name} {draft_pick.player.last_name}",
            'player_id': draft_pick.player.id
        }

    # Check if there's a final round with partial picks
    has_final_round = False
    final_round_number = 0

    if draft.final_round_draft_order:
        has_final_round = True
        final_round_number = draft.rounds + 1

        # Parse final round team IDs
        final_round_team_ids = [int(tid) for tid in draft.final_round_draft_order.split(',') if tid]

        # Get team objects for final round
        final_teams_dict = {team.id: team for team in Team.objects.filter(id__in=final_round_team_ids)}

        # Add final round to pick_assignments
        pick_assignments[final_round_number] = {}
        for pick_num, team_id in enumerate(final_round_team_ids, start=1):
            pick_assignments[final_round_number][pick_num] = final_teams_dict[team_id]

    context = {
        'draft': draft,
        'rounds': rounds,
        'picks': picks,
        'pick_assignments': pick_assignments,
        'draft_picks_map': draft_picks_map,
        'show_grid': True,
        'has_final_round': has_final_round,
        'final_round_number': final_round_number,
    }
    return render(request, 'players/run_draft.html', context)


def available_players_view(request):
    """Get list of players not yet drafted"""
    include_player_id = request.GET.get('include_player')

    # Get all player IDs that have been drafted (exclude empty picks)
    drafted_player_ids = list(DraftPick.objects.filter(player__isnull=False).values_list('player_id', flat=True))

    # If we're editing and need to include a specific player, remove them from drafted list
    if include_player_id:
        drafted_player_ids = [pid for pid in drafted_player_ids if str(pid) != str(include_player_id)]

    # Get all players not in the drafted list
    available_players = Player.objects.exclude(id__in=drafted_player_ids).order_by('last_name', 'first_name')

    # Build response
    players_data = [{
        'id': player.id,
        'first_name': player.first_name,
        'last_name': player.last_name,
        'conflict': player.conflict,
        'draftable': player.draftable
    } for player in available_players]

    return JsonResponse({
        'success': True,
        'players': players_data
    })


@csrf_exempt
def make_pick_view(request):
    """Create or update a draft pick record"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})

    try:
        data = json.loads(request.body)
        round_num = data.get('round')
        pick_num = data.get('pick')
        player_id = data.get('player_id')
        team_name = data.get('team_name')

        # Get the player
        player = Player.objects.get(id=player_id)

        # Get the team by name
        team = Team.objects.get(name=team_name)

        # Create or update the draft pick
        draft_pick, created = DraftPick.objects.update_or_create(
            round=round_num,
            pick=pick_num,
            defaults={
                'player': player,
                'team': team
            }
        )

        return JsonResponse({
            'success': True,
            'player_name': f"{player.first_name} {player.last_name}"
        })

    except Player.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Player not found'})
    except Team.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Team not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt
def undraft_pick_view(request):
    """Delete a draft pick record"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})

    try:
        data = json.loads(request.body)
        round_num = data.get('round')
        pick_num = data.get('pick')
        team_name = data.get('team_name')

        # Get the team by name
        team = Team.objects.get(name=team_name)

        # Delete the draft pick if it exists
        draft_pick = DraftPick.objects.filter(
            round=round_num,
            pick=pick_num,
            team=team
        ).first()

        if draft_pick:
            draft_pick.delete()

        return JsonResponse({
            'success': True
        })

    except Team.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Team not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


def validate_draft_assignment_view(request):
    """Validate draft assignment and return warning counts"""
    try:
        # Get the most recent draft
        draft = Draft.objects.latest('created_at')

        # Calculate total draft slots
        total_slots = draft.rounds * draft.picks_per_round

        # Add final round picks if configured
        if draft.final_round_draft_order:
            final_round_team_ids = [int(tid) for tid in draft.final_round_draft_order.split(',') if tid]
            total_slots += len(final_round_team_ids)

        # Count how many slots have been filled (have a player assigned)
        filled_slots = DraftPick.objects.filter(player__isnull=False).count()

        # Warning 1: Count remaining unfilled draft slots
        unfilled_slots = total_slots - filled_slots

        # Get all player IDs that have been drafted
        drafted_player_ids = set(DraftPick.objects.filter(player__isnull=False).values_list('player_id', flat=True))

        # Warning 2: Count players who:
        # - ARE assigned to a team (team is not null)
        # - BUT were NOT drafted (no DraftPick record)
        pre_assigned_count = Player.objects.filter(team__isnull=False).exclude(id__in=drafted_player_ids).count()

        return JsonResponse({
            'success': True,
            'undrafted_count': unfilled_slots,
            'pre_assigned_count': pre_assigned_count
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt
def reset_draft_view(request):
    """Delete all draft picks to reset the draft"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})

    try:
        # Delete all draft picks
        deleted_count = DraftPick.objects.all().delete()[0]

        return JsonResponse({
            'success': True,
            'message': f'Successfully reset draft. Deleted {deleted_count} draft picks.'
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt
def assign_players_to_teams_view(request):
    """Assign all drafted players to their teams based on draft picks"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})

    try:
        # Get all draft picks that have both a player and a team
        draft_picks = DraftPick.objects.filter(
            player__isnull=False,
            team__isnull=False
        ).select_related('player', 'team')

        success_count = 0
        already_assigned_count = 0
        errors = []

        for pick in draft_picks:
            try:
                # Check if already processed
                if pick.player_assigned_to_team:
                    already_assigned_count += 1
                    continue

                # Assign player to team
                pick.player.team = pick.team
                pick.player.save()

                # Mark as assigned
                pick.player_assigned_to_team = True
                pick.save()

                success_count += 1

            except Exception as e:
                errors.append({
                    'round': pick.round,
                    'pick': pick.pick,
                    'player': f"{pick.player.first_name} {pick.player.last_name}" if pick.player else 'Unknown',
                    'team': pick.team.name if pick.team else 'Unknown',
                    'error': str(e)
                })

        # Count picks that couldn't be processed (missing player or team)
        incomplete_picks = DraftPick.objects.filter(
            models.Q(player__isnull=True) | models.Q(team__isnull=True)
        ).count()

        return JsonResponse({
            'success': True,
            'summary': {
                'total_processed': success_count + already_assigned_count + len(errors),
                'newly_assigned': success_count,
                'already_assigned': already_assigned_count,
                'errors': len(errors),
                'incomplete_picks': incomplete_picks
            },
            'error_details': errors
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt
def simulate_draft_view(request):
    """Simulate a draft by randomly assigning all players to teams (for testing only)"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})

    try:
        import json
        import random

        # Get password from request
        data = json.loads(request.body)
        password = data.get('password', '')

        # Verify password
        if password != 'tex@5city':
            return JsonResponse({'success': False, 'error': 'Invalid password'})

        # Get the current draft
        try:
            draft = Draft.objects.latest('created_at')
        except Draft.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'No draft found'})

        # Parse draft order to get team IDs
        order_data = draft.order.strip()
        if order_data.startswith('['):
            team_ids = json.loads(order_data)
        else:
            team_ids = [int(tid.strip()) for tid in order_data.split(',') if tid.strip()]

        # Get all teams
        teams = list(Team.objects.filter(id__in=team_ids))
        if not teams:
            return JsonResponse({'success': False, 'error': 'No teams found in draft order'})

        # Get all players who haven't been drafted yet
        drafted_player_ids = DraftPick.objects.filter(player__isnull=False).values_list('player_id', flat=True)
        available_players = list(Player.objects.exclude(id__in=drafted_player_ids))

        if not available_players:
            return JsonResponse({'success': False, 'error': 'No available players to draft'})

        # Shuffle players randomly
        random.shuffle(available_players)

        picks_created = 0
        current_player_index = 0

        # Create picks for regular rounds
        for round_num in range(1, draft.rounds + 1):
            if current_player_index >= len(available_players):
                break

            # Snake draft: reverse order on even rounds
            if round_num % 2 == 0:
                round_teams = list(reversed(teams))
            else:
                round_teams = teams

            for pick_num, team in enumerate(round_teams, start=1):
                if current_player_index >= len(available_players):
                    break

                # Create or update draft pick
                draft_pick, created = DraftPick.objects.update_or_create(
                    round=round_num,
                    pick=pick_num,
                    defaults={
                        'player': available_players[current_player_index],
                        'team': team
                    }
                )

                picks_created += 1
                current_player_index += 1

        # Handle final round if needed and we still have players
        if draft.final_round_draft_order and current_player_index < len(available_players):
            final_round_team_ids = [int(tid) for tid in draft.final_round_draft_order.split(',') if tid]
            final_round_teams = Team.objects.filter(id__in=final_round_team_ids)
            teams_dict = {team.id: team for team in final_round_teams}

            final_round_num = draft.rounds + 1

            for pick_num, team_id in enumerate(final_round_team_ids, start=1):
                if current_player_index >= len(available_players):
                    break

                team = teams_dict.get(team_id)
                if team:
                    draft_pick, created = DraftPick.objects.update_or_create(
                        round=final_round_num,
                        pick=pick_num,
                        defaults={
                            'player': available_players[current_player_index],
                            'team': team
                        }
                    )

                    picks_created += 1
                    current_player_index += 1

        return JsonResponse({
            'success': True,
            'picks_created': picks_created,
            'players_drafted': current_player_index
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@require_http_methods(["POST"])
@csrf_exempt
def update_player_field(request, player_id):
    """Update a single boolean field on a player (for inline editing)"""
    try:
        player = get_object_or_404(Player, id=player_id)
        field = request.POST.get('field')
        value = request.POST.get('value') == 'true'

        # Only allow updating these specific fields
        if field not in ['attended_try_out', 'draftable']:
            return JsonResponse({'success': False, 'error': 'Invalid field'})

        setattr(player, field, value)
        player.save()

        return JsonResponse({'success': True, 'field': field, 'value': value})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
