from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, Http404
from django.views.decorators.http import require_http_methods
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.views.decorators.csrf import csrf_exempt
from django.db import models
from .models import Player, Team, Manager, PlayerRanking, ManagerDaughterRanking, Draft, DraftPick, TeamPreference, GeneralSetting, StarredDraftPick, DivisionValidationRegistry, ValidationCode
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

# Validation functions for division setup checklist
def validation_code_create_players():
    """Validate that at least 10 players exist"""
    from .models import ValidationCode

    player_count = Player.objects.count()
    is_valid = (player_count >= 10)

    # Update ValidationCode.value field
    validation = ValidationCode.objects.get(code='validation_code_create_players')
    validation.value = is_valid
    validation.save()

    # Return metadata for display
    return {
        'count': player_count,
        'count_label': 'players',
        'status_note': f'{player_count} players created (need at least 10)'
    }

def validation_code_create_teams():
    """Validate that at least 5 teams exist"""
    from .models import ValidationCode

    team_count = Team.objects.count()
    is_valid = (team_count >= 5)

    # Update ValidationCode.value field
    validation = ValidationCode.objects.get(code='validation_code_create_teams')
    validation.value = is_valid
    validation.save()

    # Return metadata for display
    return {
        'count': team_count,
        'count_label': 'teams',
        'status_note': f'{team_count} teams created (need at least 5)'
    }

def validation_code_create_managers():
    """Validate that manager count equals team count and all managers have daughters"""
    from .models import ValidationCode

    manager_count = Manager.objects.count()
    team_count = Team.objects.count()
    managers_without_daughters = Manager.objects.filter(daughter__isnull=True).count()

    is_valid = (manager_count == team_count and manager_count > 0 and managers_without_daughters == 0)

    # Update ValidationCode.value field
    validation = ValidationCode.objects.get(code='validation_code_create_managers')
    validation.value = is_valid
    validation.save()

    # Return metadata for display
    if managers_without_daughters > 0:
        status_note = f'{manager_count} managers created, but {managers_without_daughters} missing daughter assignments'
    elif manager_count != team_count:
        status_note = f'{manager_count} managers, {team_count} teams (must be equal)'
    else:
        status_note = f'{manager_count} managers created and all have daughters assigned'

    # Calculate managers with daughters assigned
    managers_with_daughters = manager_count - managers_without_daughters

    return {
        'count': manager_count,
        'count_label': f'Managers ({managers_with_daughters} Assigned to Daughters)',
        'status_note': status_note
    }

def validation_code_collect_manager_team_preferences():
    """Validate that all managers have submitted team preferences OR all teams have managers assigned"""
    from .models import ValidationCode

    manager_count = Manager.objects.count()
    team_count = Team.objects.count()
    teams_without_managers = Team.objects.filter(manager__isnull=True).count()
    team_preferences_count = TeamPreference.objects.count()

    # Complete if all managers have submitted preferences OR (teams exist AND all teams have been assigned managers)
    is_valid = (team_preferences_count >= manager_count or (team_count > 0 and teams_without_managers == 0))

    # Update ValidationCode.value field
    validation = ValidationCode.objects.get(code='validation_code_collect_manager_team_preferences')
    validation.value = is_valid
    validation.save()

    # Return metadata for display
    if teams_without_managers == 0:
        status_note = 'All teams have managers assigned'
    else:
        status_note = f'{team_preferences_count} preferences submitted'

    # Calculate teams with managers assigned
    teams_with_managers = team_count - teams_without_managers

    return {
        'count': team_preferences_count,
        'count_label': f'Preferences Submitted, {teams_with_managers} Managers Assigned to Teams',
        'status_note': status_note
    }

def validation_code_assign_managers_to_teams():
    """Validate that all teams have managers assigned"""
    from .models import ValidationCode

    manager_count = Manager.objects.count()
    teams_without_managers = Team.objects.filter(manager__isnull=True).count()
    managers_with_teams = Team.objects.filter(manager__isnull=False).count()

    is_valid = (manager_count > 0 and teams_without_managers == 0 and managers_with_teams == manager_count)

    # Update ValidationCode.value field
    validation = ValidationCode.objects.get(code='validation_code_assign_managers_to_teams')
    validation.value = is_valid
    validation.save()

    # Return metadata for display
    return {
        'count': managers_with_teams,
        'count_label': 'teams with managers',
        'status_note': f'{managers_with_teams}/{manager_count} teams have managers assigned'
    }

def validation_code_send_managers_team_secrets():
    """N/A - Manual task performed outside the website"""
    from .models import ValidationCode

    # This is a manual task, so we mark it as False (incomplete)
    validation = ValidationCode.objects.get(code='validation_code_send_managers_team_secrets')
    validation.value = False
    validation.save()

    # Return metadata for display
    return {
        'count': 0,
        'count_label': 'manual task',
        'status_note': 'Manual task - send secrets via email/text'
    }

def validation_code_request_manager_rankings():
    """N/A - Manual task performed outside the website"""
    from .models import ValidationCode

    # This is a manual task, so we mark it as False (incomplete)
    validation = ValidationCode.objects.get(code='validation_code_request_manager_rankings')
    validation.value = False
    validation.save()

    # Return metadata for display
    return {
        'count': 0,
        'count_label': 'manual task',
        'status_note': 'Manual task - request rankings via email/text'
    }

def validation_code_analyze_and_release_player_rankings():
    """Validate that at least one player ranking has been submitted"""
    from .models import ValidationCode

    player_rankings_count = PlayerRanking.objects.count()
    is_valid = (player_rankings_count >= 1)

    # Update ValidationCode.value field
    validation = ValidationCode.objects.get(code='validation_code_analyze_and_release_player_rankings')
    validation.value = is_valid
    validation.save()

    # Return metadata for display
    return {
        'count': player_rankings_count,
        'count_label': 'player rankings',
        'status_note': f'{player_rankings_count} player rankings submitted (need at least 1)'
    }

def validation_code_analyze_manager_daughter_rankings():
    """Validate that at least one manager daughter ranking has been submitted"""
    from .models import ValidationCode

    manager_daughter_rankings_count = ManagerDaughterRanking.objects.count()
    is_valid = (manager_daughter_rankings_count >= 1)

    # Update ValidationCode.value field
    validation = ValidationCode.objects.get(code='validation_code_analyze_manager_daughter_rankings')
    validation.value = is_valid
    validation.save()

    # Return metadata for display
    return {
        'count': manager_daughter_rankings_count,
        'count_label': 'daughter rankings',
        'status_note': f'{manager_daughter_rankings_count} manager daughter rankings submitted (need at least 1)'
    }

def validation_code_assign_practice_slots():
    """Validate that all teams have been assigned practice slots"""
    from .models import ValidationCode, PracticeSlotRanking

    all_teams = Team.objects.all()
    team_count = all_teams.count()
    teams_without_slots = all_teams.filter(practice_slot__isnull=True)
    teams_with_slots = all_teams.filter(practice_slot__isnull=False)

    # Complete if teams exist AND all teams have practice slots assigned
    is_valid = (team_count > 0 and teams_without_slots.count() == 0)

    # Update ValidationCode.value field
    validation = ValidationCode.objects.get(code='validation_code_assign_practice_slots')
    validation.value = is_valid
    validation.save()

    # Return metadata for display
    return {
        'count': teams_with_slots.count(),
        'count_label': 'teams with practice slots',
        'status_note': f'{teams_with_slots.count()}/{all_teams.count()} teams have practice slots assigned'
    }

def validation_code_setup_draft():
    """Validate that draft is fully configured"""
    from .models import ValidationCode, Draft
    import json as json_module

    # Fetch the draft object from the database
    draft = Draft.objects.first()
    draft_setup_complete = False

    if draft:
        # Check that all required draft configuration fields are populated
        # (rounds > 0, picks_per_round > 0, and order is not empty)
        draft_valid = (
            draft.rounds and draft.rounds > 0 and
            draft.picks_per_round and draft.picks_per_round > 0 and
            draft.order and draft.order.strip() != ''
        )

        if draft_valid:
            try:
                # Parse the order field (can be JSON array or comma-separated team IDs)
                order_data = draft.order.strip()
                if order_data.startswith('['):
                    team_ids = json_module.loads(order_data)
                else:
                    team_ids = [int(tid.strip()) for tid in order_data.split(',') if tid.strip()]

                # Verify that the number of teams in order matches picks_per_round
                draft_setup_complete = (len(team_ids) == draft.picks_per_round and len(team_ids) > 0)
            except (json_module.JSONDecodeError, ValueError):
                draft_setup_complete = False

    # Update the ValidationCode in the database with the result
    validation = ValidationCode.objects.get(code='validation_code_setup_draft')
    validation.value = draft_setup_complete
    validation.save()

    # Return metadata for display
    if draft:
        if draft_setup_complete:
            status_note = f'Draft configured: {draft.rounds} rounds, {draft.picks_per_round} teams'
        else:
            status_note = 'Draft exists but not fully configured'
    else:
        status_note = 'No draft created yet'

    return {
        'count': 1 if draft_setup_complete else 0,
        'count_label': 'draft configured',
        'status_note': status_note
    }

def validation_code_run_the_draft():
    """Validate that all players have been assigned to teams"""
    from .models import ValidationCode

    player_count = Player.objects.count()
    players_without_team = Player.objects.filter(team__isnull=True).count()
    players_with_team = player_count - players_without_team

    is_valid = (player_count > 0 and players_without_team == 0)

    # Update ValidationCode.value field
    validation = ValidationCode.objects.get(code='validation_code_run_the_draft')
    validation.value = is_valid
    validation.save()

    # Return metadata for display
    return {
        'count': players_with_team,
        'count_label': 'players assigned',
        'status_note': f'{players_with_team}/{player_count} players assigned to teams'
    }


def run_all_validations():
    """
    Master function that runs all 12 validation functions.

    This function is called by the division_setup_checklist page to refresh
    all validation statuses in the database.
    """
    import logging
    logger = logging.getLogger(__name__)

    logger.info("Running all validation functions...")

    # Call all 12 validation functions in order
    validation_code_create_players()
    validation_code_create_teams()
    validation_code_create_managers()
    validation_code_collect_manager_team_preferences()
    validation_code_assign_managers_to_teams()
    validation_code_send_managers_team_secrets()
    validation_code_request_manager_rankings()
    validation_code_analyze_and_release_player_rankings()
    validation_code_analyze_manager_daughter_rankings()
    validation_code_assign_practice_slots()
    validation_code_setup_draft()
    validation_code_run_the_draft()

    logger.info("All validation functions completed successfully")


@require_http_methods(["POST"])
def refresh_all_validations_api(request):
    """
    API endpoint to trigger all validation functions.

    Called by division_setup_checklist page on load to refresh all validations.
    """
    import logging
    logger = logging.getLogger(__name__)

    try:
        logger.info("API: Starting validation refresh...")
        run_all_validations()
        logger.info("API: Validation refresh completed")

        return JsonResponse({
            'success': True,
            'message': 'All validations refreshed successfully'
        })
    except Exception as e:
        logger.error(f"API: Error refreshing validations: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


def division_validation_registry_view(request):
    """Division validation registry visualization page"""
    import inspect
    import json
    from django.http import JsonResponse

    # Handle POST request to save validation configuration
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            # Save each page's validation configuration
            for page_url, validations in data.items():
                # Get or create the registry entry for this page
                registry, created = DivisionValidationRegistry.objects.get_or_create(
                    page=page_url,
                    defaults={
                        'validations_to_run_on_page_load': validations.get('validations_to_run_on_page_load', []),
                        'validation_code_triggers': validations.get('validation_code_triggers', [])
                    }
                )

                # Update existing entry if it wasn't just created
                if not created:
                    registry.validations_to_run_on_page_load = validations.get('validations_to_run_on_page_load', [])
                    registry.validation_code_triggers = validations.get('validation_code_triggers', [])
                    registry.save()

            return JsonResponse({'success': True, 'message': 'Configuration saved successfully'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

    # Define all validation codes with their actual Python source code
    all_validation_codes = [
        {
            'code': 'validation_code_create_players',
            'title': 'Create Players',
            'source': inspect.getsource(validation_code_create_players)
        },
        {
            'code': 'validation_code_create_teams',
            'title': 'Create Teams',
            'source': inspect.getsource(validation_code_create_teams)
        },
        {
            'code': 'validation_code_create_managers',
            'title': 'Create Managers',
            'source': inspect.getsource(validation_code_create_managers)
        },
        {
            'code': 'validation_code_collect_manager_team_preferences',
            'title': 'Collect Manager Team Preferences',
            'source': inspect.getsource(validation_code_collect_manager_team_preferences)
        },
        {
            'code': 'validation_code_assign_managers_to_teams',
            'title': 'Assign Managers to Teams',
            'source': inspect.getsource(validation_code_assign_managers_to_teams)
        },
        {
            'code': 'validation_code_send_managers_team_secrets',
            'title': 'Send Managers Team Secrets',
            'source': inspect.getsource(validation_code_send_managers_team_secrets)
        },
        {
            'code': 'validation_code_request_manager_rankings',
            'title': 'Request Manager Rankings',
            'source': inspect.getsource(validation_code_request_manager_rankings)
        },
        {
            'code': 'validation_code_analyze_and_release_player_rankings',
            'title': 'Analyze and Release Player Rankings',
            'source': inspect.getsource(validation_code_analyze_and_release_player_rankings)
        },
        {
            'code': 'validation_code_analyze_manager_daughter_rankings',
            'title': 'Analyze Manager Daughter Rankings',
            'source': inspect.getsource(validation_code_analyze_manager_daughter_rankings)
        },
        {
            'code': 'validation_code_assign_practice_slots',
            'title': 'Assign Practice Slots',
            'source': inspect.getsource(validation_code_assign_practice_slots)
        },
        {
            'code': 'validation_code_setup_draft',
            'title': 'Setup Draft',
            'source': inspect.getsource(validation_code_setup_draft)
        },
        {
            'code': 'validation_code_run_the_draft',
            'title': 'Run the Draft',
            'source': inspect.getsource(validation_code_run_the_draft)
        },
    ]

    # Define all pages/views
    pages = [
        # Main pages
        {'url': '/public_portal/', 'title': 'Public Portal'},
        {'url': '/admin_dashboard/', 'title': 'Admin Dashboard'},
        {'url': '/settings/', 'title': 'Settings'},
        {'url': '/division_setup_checklist/', 'title': 'Division Setup Checklist'},
        {'url': '/division_validation_registry/', 'title': 'Division Validation Registry'},

        # Draft pages
        {'url': '/draft/create/', 'title': 'Create Draft'},
        {'url': '/draft/edit/', 'title': 'Edit Draft'},
        {'url': '/draft/run/', 'title': 'Run Draft'},
        {'url': '/draft/available-players/', 'title': 'Available Players'},

        # Player pages
        {'url': '/players/', 'title': 'Players List'},
        {'url': '/players/create/', 'title': 'Create Player'},
        {'url': '/players/{id}/', 'title': 'Player Detail'},

        # Team pages
        {'url': '/teams/', 'title': 'Teams List'},
        {'url': '/teams/create/', 'title': 'Create Team'},
        {'url': '/teams/{id}/', 'title': 'Edit Team'},
        {'url': '/teams/{id}/delete/', 'title': 'Delete Team'},
        {'url': '/teams/{team_secret}/', 'title': 'Team Detail (Public)'},

        # Manager pages
        {'url': '/managers/', 'title': 'Managers List'},
        {'url': '/managers/create/', 'title': 'Create Manager'},
        {'url': '/managers/{id}/', 'title': 'Manager Detail'},
        {'url': '/managers/{id}/delete/', 'title': 'Delete Manager'},
        {'url': '/managers/{id}/assign-team/', 'title': 'Assign Manager to Team'},
        {'url': '/managers/randomly-assign/', 'title': 'Randomly Assign Managers'},
        {'url': '/managers/randomly-assign-daughters/', 'title': 'Randomly Assign Daughters'},

        # Rankings pages
        {'url': '/player_rankings/', 'title': 'Player Rankings'},
        {'url': '/player_rankings/analyze/', 'title': 'Analyze Player Rankings'},
        {'url': '/player_rankings/analyze/public/', 'title': 'Player Rankings Analysis (Public)'},
        {'url': '/manager_daughter_rankings/', 'title': 'Manager Daughter Rankings'},
        {'url': '/manager_daughter_rankings/analyze/', 'title': 'Analyze Manager Daughter Rankings'},
        {'url': '/practice_slot_rankings/', 'title': 'Practice Slot Rankings'},

        # Other pages
        {'url': '/try_out_check_in/', 'title': 'Try-Out Check In'},
        {'url': '/team_preferences/', 'title': 'Team Preferences'},
        {'url': '/team_preferences/analyze/', 'title': 'Analyze Team Preferences'},
        {'url': '/team_preferences/assign/', 'title': 'Assign Managers to Teams'},
        {'url': '/manage_practice_slots/', 'title': 'Manage Practice Slots'},
        {'url': '/practice_slots/analyze/', 'title': 'Analyze Practice Slots'},
        {'url': '/practice_slots/assign/', 'title': 'Assign Practice Slots to Teams'},
    ]

    # Load existing configurations from database
    existing_configs = {}
    for registry in DivisionValidationRegistry.objects.all():
        existing_configs[registry.page] = {
            'validations_to_run_on_page_load': registry.validations_to_run_on_page_load or [],
            'validation_code_triggers': registry.validation_code_triggers or []
        }

    context = {
        'pages': pages,
        'all_validation_codes': all_validation_codes,
        'existing_configs': json.dumps(existing_configs),
    }

    return render(request, 'players/division_validation_registry.html', context)


def division_setup_checklist_view(request):
    """Division setup checklist page"""
    import inspect
    import logging

    logger = logging.getLogger(__name__)

    # Helper function to execute validation code from database
    def execute_validation_from_db(validation_code):
        """
        Execute validation logic from ValidationCode table.
        Returns True/False based on validation result.
        """
        try:
            from .models import ValidationCode

            # Fetch validation from database
            validation = ValidationCode.objects.filter(code=validation_code).first()

            if not validation:
                logger.warning(f"Validation code '{validation_code}' not found in database")
                return False

            # Simply return the boolean value directly
            # (ValidationCode.value is now a BooleanField)
            return validation.value

        except Exception as e:
            logger.error(f"Error executing validation code '{validation_code}': {str(e)}")
            # On error, assume validation fails
            return False

    # Execute ALL validation codes from database
    result_create_players = execute_validation_from_db('validation_code_create_players')
    result_create_teams = execute_validation_from_db('validation_code_create_teams')
    result_create_managers = execute_validation_from_db('validation_code_create_managers')
    result_collect_preferences = execute_validation_from_db('validation_code_collect_manager_team_preferences')
    result_assign_managers = execute_validation_from_db('validation_code_assign_managers_to_teams')
    result_send_secrets = execute_validation_from_db('validation_code_send_managers_team_secrets')
    result_request_rankings = execute_validation_from_db('validation_code_request_manager_rankings')
    result_analyze_player_rankings = execute_validation_from_db('validation_code_analyze_and_release_player_rankings')
    result_analyze_daughter_rankings = execute_validation_from_db('validation_code_analyze_manager_daughter_rankings')
    result_assign_practice_slots = execute_validation_from_db('validation_code_assign_practice_slots')
    result_setup_draft = execute_validation_from_db('validation_code_setup_draft')
    result_run_draft = execute_validation_from_db('validation_code_run_the_draft')

    # Call legacy Python functions for rich metadata (count, count_label, etc.)
    result_create_players_meta = validation_code_create_players()
    result_create_teams_meta = validation_code_create_teams()
    result_create_managers_meta = validation_code_create_managers()
    result_collect_preferences_meta = validation_code_collect_manager_team_preferences()
    result_assign_managers_meta = validation_code_assign_managers_to_teams()
    result_send_secrets_meta = validation_code_send_managers_team_secrets()
    result_request_rankings_meta = validation_code_request_manager_rankings()
    result_analyze_player_rankings_meta = validation_code_analyze_and_release_player_rankings()
    result_analyze_daughter_rankings_meta = validation_code_analyze_manager_daughter_rankings()
    result_assign_practice_slots_meta = validation_code_assign_practice_slots()
    result_setup_draft_meta = validation_code_setup_draft()
    result_run_draft_meta = validation_code_run_the_draft()

    # Build checklist items
    checklist_items = [
        {
            'title': 'Create Players',
            'description': 'Export all players for this division from TeamSideline (as an .xlsx file) and then upload them.',
            'validation_code': 'validation_code_create_players',
            'validation_logic': 'At least 10 players exist in the database',
            'validation_description': 'At least 10 players have been created',
            'validation_source': inspect.getsource(validation_code_create_players),
            'link': '/settings/#player-data-import',
            'link_text': 'Go to Player Data Import',
            'status': 'complete' if result_create_players else 'incomplete',
            'count': result_create_players_meta.get('count'),
            'count_label': result_create_players_meta.get('count_label'),
            'status_note': result_create_players_meta.get('status_note')
        },
        {
            'title': 'Create Teams',
            'description': 'Create each of the teams for your division, one by one. Don\'t assign managers just yet.',
            'validation_code': 'validation_code_create_teams',
            'validation_source': inspect.getsource(validation_code_create_teams),            'validation_logic': 'At least 5 teams exist in the database',
            'validation_description': 'At least 5 teams have been created',
            'link': '/teams/',
            'link_text': 'Go to Teams',
            'status': 'complete' if result_create_teams else 'incomplete',
            'count': result_create_teams_meta.get('count'),
            'count_label': result_create_teams_meta.get('count_label'),
            'status_note': result_create_teams_meta.get('status_note')
        },
        {
            'title': 'Create Managers',
            'description': 'Create all managers/head coaches. Don\'t assign managers to teams just yet. You must also assign a daughter (player) to each manager.',
            'validation_code': 'validation_code_create_managers',
            'validation_source': inspect.getsource(validation_code_create_managers),            'validation_logic': 'Manager count equals team count AND all managers have a daughter assigned',
            'validation_description': 'One manager per team and all managers have been assigned to their daughter',
            'link': '/managers/',
            'link_text': 'Go to Managers',
            'status': 'complete' if result_create_managers else 'incomplete',
            'count': result_create_managers_meta.get('count'),
            'count_label': result_create_managers_meta.get('count_label'),
            'status_note': result_create_managers_meta.get('status_note')
        },
        {
            'title': 'Collect Manager Team Preferences',
            'description': 'Email managers the submission form that asks them to stack rank which teams they want to manage. A email has been drafted for you to send.',
            'validation_code': 'validation_code_collect_manager_team_preferences',
            'validation_source': inspect.getsource(validation_code_collect_manager_team_preferences),            'validation_logic': 'Every manager has submitted team preferences (ranking all teams) OR all managers have been assigned to teams',
            'validation_description': 'Every manager has submitted their team preferences OR all managers have been assigned to teams',
            'link': '/settings/#emails',
            'link_text': 'Go to Emails',
            'link_note': 'Click "Send Team Preferences Email"',
            'status': 'complete' if result_collect_preferences else 'incomplete',
            'count': result_collect_preferences_meta.get('count'),
            'count_label': result_collect_preferences_meta.get('count_label'),
            'status_note': result_collect_preferences_meta.get('status_note')
        },
        {
            'title': 'Assign Managers to Team',
            'description': 'Analyze the manager\'s team preference and assign managers to teams accordingly.',
            'validation_code': 'validation_code_assign_managers_to_teams',
            'validation_source': inspect.getsource(validation_code_assign_managers_to_teams),            'validation_logic': 'All teams have a manager assigned AND manager count equals teams with managers',
            'validation_description': 'All teams have a manager assigned',
            'link': '/team_preferences/analyze/',
            'link_text': 'Go to Analysis',
            'status': 'complete' if result_assign_managers else 'incomplete',
            'count': result_assign_managers_meta.get('count'),
            'count_label': result_assign_managers_meta.get('count_label'),
            'status_note': result_assign_managers_meta.get('status_note')
        },
        {
            'title': 'Send Managers "Team Secrets"',
            'description': 'Each manager will have a dashboard to manage their team. To view this page, they must use their unique "team secret." Managers should not know each other\'s secrets. Outside of this website, email/text each manager: (1) their team name (see above) and (2) their secret. To do so, on the Teams page, click the button at the top to view all team secrets.',
            'validation_code': 'validation_code_send_managers_team_secrets',
            'validation_source': inspect.getsource(validation_code_send_managers_team_secrets),            'validation_logic': 'N/A - Manual task performed outside the website',
            'validation_description': 'N/A - Manual task performed outside the website',
            'link': '/teams/',
            'link_text': 'Go to Teams',
            'link_note': 'Click "View All Team Secrets"',
            'status': 'na',
            'status_note': result_send_secrets_meta.get('status_note')
        },
        {
            'title': 'Request Manager Rankings',
            'description': 'Once each manager has their "team secret" (see above) then email all managers a link to their team\'s dashboard. At the top of this dashboard will be list of tasks for them to complete, to submit various rankings needed to build the draft. A email has been drafted for you to send.\n\nManagers must submit rankings for (1) all players, (2) manager\'s daughters, (3) their preferences for practice slots.\n\nTip: You can view any manager\'s team portal (to see exactly what they see) by going <a href="/public_portal/">here</a> and clicking a team (when prompted, enter the "master" password you were given).',
            'validation_code': 'validation_code_request_manager_rankings',
            'validation_source': inspect.getsource(validation_code_request_manager_rankings),            'validation_logic': 'N/A - Manual task performed outside the website',
            'validation_description': 'N/A - Manual task performed outside the website',
            'link': '/settings/#emails',
            'link_text': 'Go to Emails',
            'link_note': 'Click "Send Team Pages to Managers"',
            'status': 'na',
            'status_note': result_request_rankings_meta.get('status_note')
        },
        {
            'title': 'Analyze & Release Player Rankings',
            'description': 'Once all managers have submitted their top 20 player rankings, review them and then release them to managers to review.',
            'validation_code': 'validation_code_analyze_and_release_player_rankings',
            'validation_source': inspect.getsource(validation_code_analyze_and_release_player_rankings),            'validation_logic': 'All managers have submitted player rankings (PlayerRanking record exists for each manager)',
            'validation_description': 'At least one player ranking has been submitted',
            'link': '/player_rankings/analyze/',
            'link_text': 'Go to Analysis',
            'status': 'complete' if result_analyze_player_rankings else 'incomplete',
            'count': result_analyze_player_rankings_meta.get('count'),
            'count_label': result_analyze_player_rankings_meta.get('count_label'),
            'status_note': result_analyze_player_rankings_meta.get('status_note')
        },
        {
            'title': 'Analyze Manager\'s Daughters Rankings',
            'description': 'Once all managers have submitted their rankings of manager\'s daughters, review them. These rankings will NOT be released to managers. Rather, you will use these rankings to set draft positions for all manager\'s daughter.',
            'validation_code': 'validation_code_analyze_manager_daughter_rankings',
            'validation_source': inspect.getsource(validation_code_analyze_manager_daughter_rankings),            'validation_logic': 'All managers have submitted manager daughter rankings (ManagerDaughterRanking record exists for each manager)',
            'validation_description': 'At least one manager daughter ranking has been submitted',
            'link': '/manager_daughter_rankings/analyze/',
            'link_text': 'Go to Analysis',
            'status': 'complete' if result_analyze_daughter_rankings else 'incomplete',
            'count': result_analyze_daughter_rankings_meta.get('count'),
            'count_label': result_analyze_daughter_rankings_meta.get('count_label'),
            'status_note': result_analyze_daughter_rankings_meta.get('status_note')
        },
        {
            'title': 'Assign Practice Slots',
            'description': 'Review the practice slot preferences submitted by managers, then assignment one slot to each team.',
            'validation_code': 'validation_code_assign_practice_slots',
            'validation_source': inspect.getsource(validation_code_assign_practice_slots),            'validation_logic': 'All teams have been assigned a practice slot (practice_slot field is not null)',
            'validation_description': 'Every team has been assigned a practice slot',
            'link': '/practice_slots/analyze/',
            'link_text': 'Go to Analysis',
            'link_note': 'Click "Assign Practice Slots to Teams"',
            'status': 'complete' if result_assign_practice_slots else 'incomplete',
            'count': result_assign_practice_slots_meta.get('count'),
            'count_label': result_assign_practice_slots_meta.get('count_label'),
            'status_note': result_assign_practice_slots_meta.get('status_note')
        },
        {
            'title': 'Setup Draft',
            'description': 'Configure all draft settings including the number of rounds, teams participating, and the order in which teams will draft players.',
            'validation_code': 'validation_code_setup_draft',
            'validation_source': inspect.getsource(validation_code_setup_draft),            'validation_logic': 'Draft exists with rounds > 0, picks_per_round > 0, valid draft order format, and number of teams in draft order equals picks_per_round',
            'validation_description': 'Draft has been configured with rounds, teams, and a valid draft order',
            'link': '/draft/edit/',
            'link_text': 'Go to Draft Setup',
            'status': 'complete' if result_setup_draft else 'incomplete',
            'count': result_setup_draft_meta.get('count'),
            'count_label': result_setup_draft_meta.get('count_label'),
            'status_note': result_setup_draft_meta.get('status_note')
        },
        {
            'title': 'Run the Draft',
            'description': 'Complete every round of the draft. Once all players have been selected, assign players to the team that drafting them.',
            'validation_code': 'validation_code_run_the_draft',
            'validation_source': inspect.getsource(validation_code_run_the_draft),            'validation_logic': 'At least one player exists AND all players have been assigned to a team (team field is not null)',
            'validation_description': 'At least one player exists and all players have been assigned to teams',
            'link': '/draft/run/',
            'link_text': 'Go to Draft Board',
            'link_note': 'Click "Draft Complete" to Assign Players to Teams',
            'status': 'complete' if result_run_draft else 'incomplete',
            'count': result_run_draft_meta.get('count'),
            'count_label': result_run_draft_meta.get('count_label'),
            'status_note': result_run_draft_meta.get('status_note')
        }
    ]

    # Check if all checklist items are complete (ignoring N/A items)
    all_complete = all(item['status'] in ['complete', 'na'] for item in checklist_items)

    # Check if validations were already refreshed (to prevent showing overlay)
    validations_already_refreshed = request.GET.get('validations_refreshed') == 'true'

    context = {
        'checklist_items': checklist_items,
        'validations_already_refreshed': validations_already_refreshed,
    }
    return render(request, 'players/division_setup_checklist.html', context)


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
    from .models import Draft, Manager
    import string
    import random
    import json

    # Get the first (and should be only) draft
    draft = Draft.objects.first()

    # Get counts for template context
    player_count = Player.objects.count()
    team_count = Team.objects.count()

    if request.method == 'POST':

        rounds = int(request.POST.get('rounds'))
        picks_per_round = int(request.POST.get('picks_per_round'))
        order = request.POST.get('order', '')

        # Handle non-draftable players
        non_draftable_player_ids = request.POST.getlist('non_draftable_players')

        # Step 1: Set ALL players to draftable = True
        Player.objects.all().update(draftable=True)

        # Step 2: Set selected players to draftable = False
        if non_draftable_player_ids:
            Player.objects.filter(id__in=non_draftable_player_ids).update(draftable=False)

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

        # Calculate suggested rounds (players / teams) - round down to get base rounds
        # The system will automatically handle extra players in a final round
        if team_count > 0:
            suggested_rounds = int(player_count / team_count)
            suggested_picks_per_round = team_count

    # Get total player count
    player_count = Player.objects.count()

    # Check if there are any draft picks
    has_draft_picks = DraftPick.objects.exists()

    # Get all teams for draft order
    all_teams = Team.objects.all().order_by('name')

    # Calculate max players per team (ceiling of total players / number of teams)
    team_count = all_teams.count()
    if team_count > 0:
        import math
        max_players_per_team = math.ceil(player_count / team_count)
    else:
        max_players_per_team = 0

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

    # Get players who didn't attend try-outs
    no_show_players = Player.objects.filter(attended_try_out=False).order_by('last_name', 'first_name')

    context = {
        'draft': draft,
        'is_create': is_create,
        'suggested_rounds': suggested_rounds,
        'suggested_picks_per_round': suggested_picks_per_round,
        'all_teams': all_teams,
        'ordered_team_ids': ordered_team_ids,
        'player_count': player_count,
        'max_players_per_team': max_players_per_team,
        'needs_extra_round': needs_extra_round,
        'total_regular_picks': total_regular_picks,
        'extra_picks_needed': extra_picks_needed,
        'final_round_number': final_round_number,
        'final_round_team_names': final_round_team_names,
        'has_draft_picks': has_draft_picks,
        'no_show_players': no_show_players,
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
    MASTER_PASSWORD = 'wusarocks'

    if not team_secret:
        return JsonResponse({
            'success': False,
            'error': 'Please enter a team secret.'
        }, status=400)

    # Check if master password is used - redirect to first team
    if team_secret == MASTER_PASSWORD:
        first_team = Team.objects.order_by('name').first()
        if first_team:
            return JsonResponse({
                'success': True,
                'team_url': f'/teams/{first_team.manager_secret}/'
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'No teams available.'
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
    if not (excel_file.name.endswith('.xlsx') or excel_file.name.endswith('.xls')):
        return JsonResponse({
            'success': False,
            'error': 'Invalid file type. Please upload an Excel file (.xlsx or .xls)'
        }, status=400)

    try:
        # Save file temporarily
        file_path = default_storage.save(f'tmp/{excel_file.name}', ContentFile(excel_file.read()))
        full_path = default_storage.path(file_path)

        # Read Excel file with appropriate engine
        # Try to read as Excel first, but fall back to TSV if it's actually a text file
        try:
            if excel_file.name.endswith('.xls'):
                df = pd.read_excel(full_path, engine='xlrd')
            else:
                df = pd.read_excel(full_path, engine='openpyxl')
        except Exception as excel_error:
            # If reading as Excel fails, try reading as tab-delimited text
            # This handles cases where .xls files are actually TSV exports
            try:
                df = pd.read_csv(full_path, sep='\t', encoding='utf-8')
            except Exception as csv_error:
                # If both fail, raise the original Excel error
                raise excel_error

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
    from .models import PlayerRanking, ManagerDaughterRanking, PracticeSlotRanking, PracticeSlot
    from django.contrib import messages
    import json

    try:
        team = Team.objects.get(manager_secret=team_secret)
    except Team.DoesNotExist:
        raise Http404("Team not found")

    # Handle practice slot assignment via POST
    if request.method == 'POST' and 'practice_slot_id' in request.POST:
        practice_slot_id = request.POST.get('practice_slot_id')
        if practice_slot_id:
            try:
                practice_slot = PracticeSlot.objects.get(id=practice_slot_id)
                team.practice_slot = practice_slot
                team.save()
                messages.success(request, f'Practice slot assigned: {practice_slot.practice_slot}')
            except PracticeSlot.DoesNotExist:
                messages.error(request, 'Invalid practice slot selected')
        else:
            # Remove practice slot assignment
            team.practice_slot = None
            team.save()
            messages.success(request, 'Practice slot removed')
        return redirect('players:team_detail', team_secret=team_secret)

    # Get all players assigned to this team
    players = team.players.all().order_by('last_name', 'first_name')

    # Check if draft portal is open
    try:
        portal_setting = GeneralSetting.objects.get(key='open_draft_portal_to_managers')
        portal_open = portal_setting.value == 'true'
    except GeneralSetting.DoesNotExist:
        portal_open = False

    # Get available players (not yet drafted) and drafted players if portal is open
    available_players = []
    drafted_players = []
    starred_player_ids = set()
    if portal_open:
        # Get all player IDs that have been drafted
        drafted_player_ids = DraftPick.objects.filter(player__isnull=False).values_list('player_id', flat=True)
        # Get players not in that list
        available_players = Player.objects.exclude(id__in=drafted_player_ids).order_by('last_name', 'first_name')
        # Get players drafted by this team
        drafted_picks = DraftPick.objects.filter(team=team, player__isnull=False).select_related('player').order_by('round', 'pick')
        drafted_players = [pick.player for pick in drafted_picks]
        # Get starred player IDs for this team
        starred_player_ids = set(StarredDraftPick.objects.filter(team=team).values_list('player_id', flat=True))

    # Calculate checklist status for this manager
    checklist_items = []

    if team.manager:
        try:
            # Task 1: Rank All Players (top 20)
            expected_player_count = 20
            try:
                player_ranking = PlayerRanking.objects.get(manager=team.manager)
                ranking_data = json.loads(player_ranking.ranking)
                if len(ranking_data) == 0:
                    player_ranking_status = 'not_started'
                elif len(ranking_data) < expected_player_count:
                    player_ranking_status = 'in_progress'
                else:
                    player_ranking_status = 'completed'
            except PlayerRanking.DoesNotExist:
                player_ranking_status = 'not_started'

            checklist_items.append({
                'title': 'Rank All Players',
                'url': f"/player_rankings/?team_secret={team.manager_secret}",
                'status': player_ranking_status
            })

            # Task 2: Rank Manager's Daughters
            # Get total count of all manager's daughters in the division
            manager_daughter_ids = Manager.objects.filter(daughter__isnull=False).values_list('daughter_id', flat=True)
            total_daughters = len(manager_daughter_ids)

            try:
                daughter_ranking = ManagerDaughterRanking.objects.get(manager=team.manager)
                ranking_data = json.loads(daughter_ranking.ranking)
                if len(ranking_data) == 0:
                    daughter_ranking_status = 'not_started'
                elif len(ranking_data) < total_daughters:
                    daughter_ranking_status = 'in_progress'
                else:
                    daughter_ranking_status = 'completed'
            except ManagerDaughterRanking.DoesNotExist:
                daughter_ranking_status = 'not_started'

            checklist_items.append({
                'title': "Rank Manager's Daughters",
                'url': f"/manager_daughter_rankings/?team_secret={team.manager_secret}",
                'status': daughter_ranking_status
            })

            # Task 3: Rank Practice Slots
            total_slots = PracticeSlot.objects.count()
            try:
                practice_ranking = PracticeSlotRanking.objects.get(team=team)
                ranking_data = json.loads(practice_ranking.rankings)
                if len(ranking_data) == 0:
                    practice_ranking_status = 'not_started'
                elif len(ranking_data) < total_slots:
                    practice_ranking_status = 'in_progress'
                else:
                    practice_ranking_status = 'completed'
            except PracticeSlotRanking.DoesNotExist:
                practice_ranking_status = 'not_started'

            checklist_items.append({
                'title': 'Rank Practice Slots',
                'url': f"/practice_slot_rankings/?team_secret={team.manager_secret}",
                'status': practice_ranking_status
            })

            # Task 4: View All Rankings
            # This is just a view action, so no status
            checklist_items.append({
                'title': 'View All Rankings',
                'url': '/player_rankings/analyze/public/',
                'status': 'n/a'
            })
        except Exception as e:
            # If there's any error, just don't show the checklist
            import logging
            logging.error(f"Error calculating checklist: {e}")
            checklist_items = []

    # Get all practice slots for the dropdown
    all_practice_slots = PracticeSlot.objects.all().order_by('practice_slot')

    context = {
        'team': team,
        'players': players,
        'checklist_items': checklist_items,
        'portal_open': portal_open,
        'available_players': available_players,
        'drafted_players': drafted_players,
        'starred_player_ids': starred_player_ids,
        'all_practice_slots': all_practice_slots
    }
    return render(request, 'players/team_detail.html', context)


@csrf_exempt
def toggle_star_player_view(request, team_secret):
    """Toggle starring a player for a team"""
    if request.method == 'POST':
        try:
            player_id = request.POST.get('player_id')

            # Get the team
            team = Team.objects.get(manager_secret=team_secret)
            player = Player.objects.get(id=player_id)

            # Check if already starred
            starred = StarredDraftPick.objects.filter(team=team, player=player).first()

            if starred:
                # Unstar - delete the record
                starred.delete()
                return JsonResponse({'success': True, 'starred': False})
            else:
                # Star - create the record
                StarredDraftPick.objects.create(team=team, player=player)
                return JsonResponse({'success': True, 'starred': True})

        except Team.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Team not found'}, status=404)
        except Player.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Player not found'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)


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

    # Check if manager count equals team count
    total_managers = Manager.objects.count()
    total_teams = Team.objects.count()
    manager_team_mismatch = total_managers != total_teams

    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'sort_by': sort_by,
        'order': order,
        'total_managers': total_managers,
        'total_teams': total_teams,
        'manager_team_mismatch': manager_team_mismatch,
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
        daughter_id = request.POST.get('daughter')
        daughter = None
        if daughter_id:
            daughter = Player.objects.filter(id=daughter_id).first()

        manager = Manager(
            first_name=request.POST.get('first_name'),
            last_name=request.POST.get('last_name'),
            email=request.POST.get('email'),
            phone=request.POST.get('phone'),
            daughter=daughter
        )
        manager.save()
        messages.success(request, f'Manager {manager.first_name} {manager.last_name} created successfully!')
        return redirect('players:managers_list')

    # Get all players for the daughter dropdown
    players = Player.objects.all().order_by('first_name', 'last_name')
    context = {'players': players}
    return render(request, 'players/manager_create.html', context)


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

    # Get all teams with manager info for the secrets modal
    all_teams = Team.objects.select_related('manager').filter(manager__isnull=False).order_by('name')

    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'sort_by': sort_by,
        'order': order,
        'total_teams': Team.objects.count(),
        'unassigned_managers': unassigned_managers,
        'all_teams': all_teams
    }
    return render(request, 'players/teams_list.html', context)


def unassign_practice_slots(request):
    """Unassign all practice slots from all teams (for testing purposes)"""
    if request.method == 'POST':
        try:
            # Remove all practice slot assignments from teams
            updated_count = Team.objects.filter(practice_slot__isnull=False).update(practice_slot=None)

            return JsonResponse({
                'success': True,
                'message': f'Successfully unassigned practice slots from {updated_count} team(s).'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Error unassigning practice slots: {str(e)}'
            }, status=500)

    return JsonResponse({
        'success': False,
        'error': 'Invalid request method'
    }, status=400)


def team_edit_view(request, pk):
    """View and edit a single team"""
    from .models import PracticeSlot
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

        # Handle practice slot assignment
        practice_slot_id = request.POST.get('practice_slot_id')
        if practice_slot_id == '':
            team.practice_slot = None
        else:
            try:
                practice_slot = PracticeSlot.objects.get(pk=practice_slot_id)
                team.practice_slot = practice_slot
            except PracticeSlot.DoesNotExist:
                pass

        team.save()
        messages.success(request, f'Team {team.name} updated successfully!')
        return redirect('players:team_edit', pk=team.pk)

    # Get all managers for dropdown
    all_managers = Manager.objects.all().order_by('last_name', 'first_name')

    # Get all practice slots for dropdown
    all_practice_slots = PracticeSlot.objects.all().order_by('practice_slot')

    # Get all players assigned to this team
    team_players = Player.objects.filter(team=team).order_by('first_name', 'last_name')

    context = {
        'team': team,
        'all_managers': all_managers,
        'all_practice_slots': all_practice_slots,
        'team_players': team_players
    }
    return render(request, 'players/team_edit.html', context)


def team_create_view(request):
    """Create a new team"""
    import string
    import random as rand

    def generate_unique_secret():
        """Generate a unique 7-character alphanumeric secret"""
        characters = string.ascii_letters + string.digits
        while True:
            secret = ''.join(rand.choice(characters) for _ in range(7))
            # Check if this secret already exists
            if not Team.objects.filter(manager_secret=secret).exists():
                return secret

    if request.method == 'POST':
        team = Team(
            name=request.POST.get('name'),
            manager_secret=request.POST.get('manager_secret'),
        )
        team.save()
        messages.success(request, f'Team {team.name} created successfully!')
        return redirect('players:teams_list')

    # Generate a unique secret for the form
    unique_secret = generate_unique_secret()

    context = {'generated_secret': unique_secret}
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


def practice_slot_rankings_view(request):
    """Create or update practice slot rankings for a team"""
    from .models import PracticeSlot, PracticeSlotRanking

    # Get team_secret from URL parameter
    team_secret = request.GET.get('team_secret', request.POST.get('team_secret', ''))

    # Find the team associated with this team_secret
    team = None
    if team_secret:
        try:
            team = Team.objects.get(manager_secret=team_secret)
        except Team.DoesNotExist:
            messages.error(request, 'Invalid team secret.')

    if request.method == 'POST':
        # Get the rankings data from the form (comma-separated slot IDs in ranked order)
        rankings_data = request.POST.get('rankings', '')

        if rankings_data:
            # Parse the comma-separated IDs
            slot_ids = [int(sid) for sid in rankings_data.split(',') if sid]

            # Create a JSON structure with rank and slot ID
            rankings_json = json.dumps([
                {"rank": idx + 1, "slot_id": slot_id}
                for idx, slot_id in enumerate(slot_ids)
            ])

            # Update or create ranking for this team (ensures only one ranking per team)
            if team:
                PracticeSlotRanking.objects.update_or_create(
                    team=team,
                    defaults={'rankings': rankings_json}
                )
            else:
                # If no team, just create a new ranking
                PracticeSlotRanking.objects.create(rankings=rankings_json)

            messages.success(request, f'Practice slot rankings saved successfully! ({len(slot_ids)} slots ranked)')

            # Redirect back to team page if team_secret was provided
            if team_secret:
                return redirect('players:team_detail', team_secret=team_secret)
            else:
                return redirect('players:practice_slot_rankings')
        else:
            messages.error(request, 'No rankings data provided.')

    # Load existing rankings for this team
    existing_ranking = None
    ranked_slot_ids = []
    if team:
        try:
            existing_ranking = PracticeSlotRanking.objects.get(team=team)
            # Parse the JSON to get slot IDs in order
            rankings_data = json.loads(existing_ranking.rankings)
            ranked_slot_ids = [item['slot_id'] for item in rankings_data]
        except PracticeSlotRanking.DoesNotExist:
            pass

    # Get all practice slots, ordered by practice_slot
    all_slots = PracticeSlot.objects.all().order_by('practice_slot')
    total_slots = all_slots.count()

    context = {
        'all_slots': all_slots,
        'total_slots': total_slots,
        'team_secret': team_secret,
        'team': team,
        'ranked_slot_ids': json.dumps(ranked_slot_ids),  # Pass as JSON for JavaScript
    }
    return render(request, 'players/practice_slot_rankings.html', context)


@login_required
def practice_slots_analyze_view(request):
    """Display practice slots analysis page"""
    # Check if any teams already have practice slots assigned
    teams_with_slots = Team.objects.filter(practice_slot__isnull=False).count()

    context = {
        'teams_with_slots': teams_with_slots
    }

    return render(request, 'players/practice_slots_analyze.html', context)


@login_required
@require_http_methods(["POST"])
def run_practice_slots_analysis_view(request):
    """Run analysis to match teams with their preferred practice slots"""
    from .models import PracticeSlot, PracticeSlotRanking
    import random

    try:
        # Get all teams and practice slots
        all_teams = list(Team.objects.all())
        all_slots = list(PracticeSlot.objects.all())

        # Validation 2: Check if team and slot counts match
        if len(all_teams) != len(all_slots):
            return JsonResponse({
                'success': False,
                'error': f'The number of teams ({len(all_teams)}) does not match the number of practice slots ({len(all_slots)}). They must be equal.'
            }, status=400)

        # Randomly shuffle teams
        random.shuffle(all_teams)

        # Available slots (will be removed as they're assigned)
        available_slots = {slot.id: slot for slot in all_slots}

        # Assignments
        assignments = []

        for team in all_teams:
            assigned_slot = None
            has_rankings = False

            # Try to get team's practice slot rankings
            try:
                ranking = PracticeSlotRanking.objects.get(team=team)
                rankings_data = json.loads(ranking.rankings)
                has_rankings = True

                # Try to assign most preferred available slot
                for item in rankings_data:
                    slot_id = item['slot_id']
                    if slot_id in available_slots:
                        assigned_slot = available_slots[slot_id]
                        del available_slots[slot_id]
                        break

            except PracticeSlotRanking.DoesNotExist:
                pass

            # If no ranking or no preferred slot available, assign first available
            if not assigned_slot and available_slots:
                slot_id = next(iter(available_slots))
                assigned_slot = available_slots[slot_id]
                del available_slots[slot_id]

            assignments.append({
                'team_id': team.id,
                'team_name': team.name,
                'slot_id': assigned_slot.id if assigned_slot else None,
                'slot_text': assigned_slot.practice_slot if assigned_slot else None,
                'has_rankings': has_rankings
            })

        return JsonResponse({
            'success': True,
            'assignments': assignments,
            'all_slots': [{'id': s.id, 'practice_slot': s.practice_slot} for s in all_slots]
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'An error occurred: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def assign_practice_slots_to_teams_view(request):
    """Assign practice slots to teams based on analysis results"""
    from .models import PracticeSlot, PracticeSlotRanking

    try:
        assignments_json = request.POST.get('assignments', '')

        if not assignments_json:
            return JsonResponse({
                'success': False,
                'error': 'No assignment data provided.'
            }, status=400)

        try:
            assignments = json.loads(assignments_json)
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid assignment data.'
            }, status=400)

        # Validate that each slot is assigned exactly once
        slot_ids = [a['slot_id'] for a in assignments]
        if len(slot_ids) != len(set(slot_ids)):
            return JsonResponse({
                'success': False,
                'error': 'Each practice slot must be assigned to exactly one team.'
            }, status=400)

        # Perform the assignments by setting the foreign key relationship
        assigned_count = 0
        for assignment in assignments:
            team_id = assignment['team_id']
            slot_id = assignment['slot_id']

            if not team_id or not slot_id:
                continue

            team = Team.objects.get(id=team_id)
            slot = PracticeSlot.objects.get(id=slot_id)

            # Set the practice_slot foreign key on the team
            team.practice_slot = slot
            team.save()
            assigned_count += 1

        return JsonResponse({
            'success': True,
            'message': f'Successfully assigned practice slots to {assigned_count} teams!'
        })

    except Team.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'One or more teams not found.'
        }, status=404)
    except PracticeSlot.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'One or more practice slots not found.'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'An error occurred: {str(e)}'
        }, status=500)


def run_draft_view(request):
    """Run the draft - display grid of rounds and picks"""

    # Get the draft portal status
    try:
        portal_setting = GeneralSetting.objects.get(key='open_draft_portal_to_managers')
        portal_open = portal_setting.value == 'true'
    except GeneralSetting.DoesNotExist:
        portal_open = False

    # Get the most recent draft
    try:
        draft = Draft.objects.latest('created_at')
    except Draft.DoesNotExist:
        messages.error(request, 'No draft found. Please create a draft first.')
        return redirect('players:edit_draft')

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
        # Only add pick to map if player is assigned
        if draft_pick.player:
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
        'portal_open': portal_open,
    }
    return render(request, 'players/run_draft.html', context)


def toggle_draft_portal_view(request):
    """Toggle the open_draft_portal_to_managers setting"""
    if request.method == 'POST':
        try:
            # Get or create the setting
            setting, created = GeneralSetting.objects.get_or_create(
                key='open_draft_portal_to_managers',
                defaults={'value': 'true'}
            )

            # If it already existed, toggle its value
            if not created:
                if setting.value == 'true':
                    setting.value = 'false'
                    messages.success(request, 'Manager Draft Portal has been closed.')
                else:
                    setting.value = 'true'
                    messages.success(request, 'Manager Draft Portal has been opened.')
                setting.save()
            else:
                messages.success(request, 'Manager Draft Portal has been opened.')

            return redirect('players:run_draft')
        except Exception as e:
            messages.error(request, f'Error toggling draft portal: {str(e)}')
            return redirect('players:run_draft')

    return redirect('players:run_draft')


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

        # Broadcast the draft pick to all connected WebSocket clients
        from asgiref.sync import async_to_sync
        from channels.layers import get_channel_layer

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            'draft_updates',
            {
                'type': 'draft_update',
                'player_id': player.id,
                'player_name': f"{player.first_name} {player.last_name}",
                'player_birthday': str(player.birthday) if player.birthday else None,
                'player_school': player.school,
                'player_history': player.history,
                'player_conflict': player.conflict,
                'player_draftable': player.draftable,
                'team_name': team.name,
                'team_id': team.id,
                'round': round_num,
                'pick': pick_num
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
            # Save player info before deleting
            player = draft_pick.player
            player_id = player.id if player else None
            player_name = f"{player.first_name} {player.last_name}" if player else None
            player_birthday = str(player.birthday) if (player and player.birthday) else None
            player_school = player.school if player else None
            player_history = player.history if player else None
            player_conflict = player.conflict if player else None
            player_draftable = player.draftable if player else None

            draft_pick.delete()

            # Broadcast the undraft to all connected WebSocket clients
            if player:
                from asgiref.sync import async_to_sync
                from channels.layers import get_channel_layer

                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    'draft_updates',
                    {
                        'type': 'undraft_update',
                        'player_id': player_id,
                        'player_name': player_name,
                        'player_birthday': player_birthday,
                        'player_school': player_school,
                        'player_history': player_history,
                        'player_conflict': player_conflict,
                        'player_draftable': player_draftable,
                        'team_name': team.name,
                        'team_id': team.id,
                        'round': round_num,
                        'pick': pick_num
                    }
                )

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

        # Warning 3: Count draft picks that have already been assigned to teams
        # This indicates that the assignment has already been completed
        already_assigned_count = DraftPick.objects.filter(player_assigned_to_team=True).count()

        return JsonResponse({
            'success': True,
            'undrafted_count': unfilled_slots,
            'pre_assigned_count': pre_assigned_count,
            'already_assigned_count': already_assigned_count
        })

    except Draft.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'No draft found. Please create a draft first.'})
    except Exception as e:
        import traceback
        return JsonResponse({
            'success': False,
            'error': f'{type(e).__name__}: {str(e)}',
            'traceback': traceback.format_exc()
        })


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
def reset_teams_view(request):
    """Remove all players from all teams (for testing purposes)"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})

    try:
        # Count players currently assigned to teams
        count = Player.objects.filter(team__isnull=False).count()

        # Unassociate players from teams
        Player.objects.all().update(team=None)

        # Reset the player_assigned_to_team flag on all draft picks
        DraftPick.objects.filter(player_assigned_to_team=True).update(player_assigned_to_team=False)

        return JsonResponse({
            'success': True,
            'message': f'Successfully removed {count} players from teams and reset assignment flags.'
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt
def delete_all_players_view(request):
    """Delete all players from the database (DANGEROUS - for testing only)"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})

    try:
        # Count players to be deleted
        count = Player.objects.count()

        # Delete all players (this will cascade delete related records)
        Player.objects.all().delete()

        return JsonResponse({
            'success': True,
            'message': f'Successfully deleted {count} players and all related data.'
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

        # Close the draft portal to managers after assignment
        try:
            portal_setting, created = GeneralSetting.objects.get_or_create(
                key='open_draft_portal_to_managers',
                defaults={'value': 'false'}
            )
            if not created and portal_setting.value == 'true':
                portal_setting.value = 'false'
                portal_setting.save()
        except Exception as e:
            # Log error but don't fail the assignment
            import logging
            logging.error(f"Error closing draft portal: {e}")

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
        import random

        # Check if draft picks already exist
        existing_picks = DraftPick.objects.count()
        if existing_picks > 0:
            return JsonResponse({
                'success': False,
                'error': 'Draft picks already exist. Please reset the draft before simulating.',
                'existing_picks': existing_picks
            })

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


def team_preferences_view(request):
    """Team name preferences page for managers"""
    # Get all team names from the teams table
    all_teams = Team.objects.all().order_by('name')

    context = {
        'all_teams': all_teams,
    }
    return render(request, 'players/team_preferences.html', context)


@login_required
def player_rankings_analyze_view(request):
    """Analyze manager player rankings"""
    from .models import PlayerRanking, Manager, Player, GeneralSetting
    from collections import defaultdict

    # Check if rankings have been released
    rankings_released = False
    try:
        setting = GeneralSetting.objects.get(key='player_rankings_public')
        rankings_released = setting.value.lower() == 'true'
    except GeneralSetting.DoesNotExist:
        rankings_released = False

    # Get all player rankings
    all_rankings = PlayerRanking.objects.all()

    # Dictionary to accumulate scores for each player
    # For Borda count: higher rank position = higher points
    player_scores = defaultdict(list)
    max_rank = 0  # Track the maximum rank seen to determine Borda points

    # First pass: collect all ranks and find max rank
    for ranking in all_rankings:
        try:
            rankings_data = json.loads(ranking.ranking)
            for item in rankings_data:
                player_id = item.get('player_id')
                rank = item.get('rank')
                if player_id and rank:
                    player_scores[player_id].append(rank)
                    max_rank = max(max_rank, rank)
        except (json.JSONDecodeError, KeyError):
            continue

    # Calculate Borda count and average rank for each player
    player_stats = []
    for player_id, ranks in player_scores.items():
        # Borda count: rank 1 gets max_rank points, rank 2 gets (max_rank - 1) points, etc.
        borda_count = sum(max_rank - rank + 1 for rank in ranks)
        avg_rank = sum(ranks) / len(ranks)

        try:
            player = Player.objects.get(id=player_id)
            player_stats.append({
                'player': player,
                'average_rank': avg_rank,
                'borda_count': borda_count,
                'num_rankings': len(ranks)
            })
        except Player.DoesNotExist:
            continue

    # Sort by Borda count (higher is better), then by average rank as tiebreaker
    player_stats.sort(key=lambda x: (-x['borda_count'], x['average_rank']))
    top_players = player_stats[:20]

    # Find managers who haven't submitted rankings
    all_managers = Manager.objects.all()
    managers_with_rankings = PlayerRanking.objects.filter(manager__isnull=False).values_list('manager_id', flat=True).distinct()
    managers_without_rankings = all_managers.exclude(id__in=managers_with_rankings)

    context = {
        'top_players': top_players,
        'managers_without_rankings': managers_without_rankings,
        'managers_without_count': managers_without_rankings.count(),
        'rankings_released': rankings_released,
    }
    return render(request, 'players/player_rankings_analyze.html', context)


@login_required
@require_http_methods(["POST"])
def release_player_rankings_view(request):
    """Toggle player rankings release status"""
    from .models import GeneralSetting

    try:
        # Get current state
        try:
            setting = GeneralSetting.objects.get(key='player_rankings_public')
            current_value = setting.value.lower() == 'true'
        except GeneralSetting.DoesNotExist:
            current_value = False

        # Toggle the value
        new_value = 'false' if current_value else 'true'

        # Create or update the setting
        setting, created = GeneralSetting.objects.update_or_create(
            key='player_rankings_public',
            defaults={'value': new_value}
        )

        message = 'Player rankings have been released to coaches.' if new_value == 'true' else 'Player rankings have been unreleased from coaches.'

        return JsonResponse({
            'success': True,
            'message': message,
            'new_state': new_value
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


def player_rankings_analyze_public_view(request):
    """Public view of player rankings analysis (no login required)"""
    from .models import PlayerRanking, Manager, Player, GeneralSetting
    from collections import defaultdict

    # Check if rankings are released
    rankings_released = False
    try:
        setting = GeneralSetting.objects.get(key='player_rankings_public')
        rankings_released = setting.value.lower() == 'true'
    except GeneralSetting.DoesNotExist:
        rankings_released = False

    # If not released, show message
    if not rankings_released:
        context = {
            'rankings_released': False
        }
        return render(request, 'players/player_rankings_analyze_public.html', context)

    # Get all player rankings
    all_rankings = PlayerRanking.objects.all()

    # Dictionary to accumulate scores for each player
    # For Borda count: higher rank position = higher points
    player_scores = defaultdict(list)
    max_rank = 0  # Track the maximum rank seen to determine Borda points

    # First pass: collect all ranks and find max rank
    for ranking in all_rankings:
        try:
            rankings_data = json.loads(ranking.ranking)
            for item in rankings_data:
                player_id = item.get('player_id')
                rank = item.get('rank')
                if player_id and rank:
                    player_scores[player_id].append(rank)
                    max_rank = max(max_rank, rank)
        except (json.JSONDecodeError, KeyError):
            continue

    # Calculate Borda count and average rank for each player
    player_stats = []
    for player_id, ranks in player_scores.items():
        # Borda count: rank 1 gets max_rank points, rank 2 gets (max_rank - 1) points, etc.
        borda_count = sum(max_rank - rank + 1 for rank in ranks)
        avg_rank = sum(ranks) / len(ranks)

        try:
            player = Player.objects.get(id=player_id)
            player_stats.append({
                'player': player,
                'average_rank': avg_rank,
                'borda_count': borda_count,
                'num_rankings': len(ranks)
            })
        except Player.DoesNotExist:
            continue

    # Sort by Borda count (higher is better), then by average rank as tiebreaker
    player_stats.sort(key=lambda x: (-x['borda_count'], x['average_rank']))
    top_players = player_stats[:20]

    # Don't show manager submission info on public page
    context = {
        'top_players': top_players,
        'rankings_released': True,
    }
    return render(request, 'players/player_rankings_analyze_public.html', context)


@login_required
def manager_daughter_rankings_analyze_view(request):
    """Analyze manager daughter rankings with Borda count"""
    from .models import ManagerDaughterRanking, Manager, Player
    from collections import defaultdict

    # Get all manager daughter rankings
    all_rankings = ManagerDaughterRanking.objects.all()
    player_scores = defaultdict(list)
    max_rank = 0

    # Process all rankings to collect scores for each player
    for ranking in all_rankings:
        rankings_data = json.loads(ranking.ranking)
        for item in rankings_data:
            player_id = item.get('player_id')
            rank = item.get('rank')
            if player_id and rank:
                player_scores[player_id].append(rank)
                max_rank = max(max_rank, rank)

    # Calculate Borda count for each player
    player_stats = []
    for player_id, ranks in player_scores.items():
        # Borda count: rank 1 gets max_rank points, rank 2 gets max_rank-1 points, etc.
        borda_count = sum(max_rank - rank + 1 for rank in ranks)
        avg_rank = sum(ranks) / len(ranks)
        try:
            player = Player.objects.get(id=player_id)
            player_stats.append({
                'player': player,
                'average_rank': avg_rank,
                'borda_count': borda_count,
                'num_rankings': len(ranks)
            })
        except Player.DoesNotExist:
            continue

    # Sort by Borda count (higher is better), then by average rank (lower is better)
    player_stats.sort(key=lambda x: (-x['borda_count'], x['average_rank']))

    # Get top 20 players
    top_players = player_stats[:20]

    # Get managers who haven't submitted rankings
    all_managers = Manager.objects.all()
    managers_with_rankings = ManagerDaughterRanking.objects.values_list('manager_id', flat=True)
    managers_without_rankings = all_managers.exclude(id__in=managers_with_rankings)

    context = {
        'top_players': top_players,
        'managers_without_rankings': managers_without_rankings,
        'managers_without_count': managers_without_rankings.count(),
    }
    return render(request, 'players/manager_daughter_rankings_analyze.html', context)


@login_required
def try_out_check_in_view(request):
    """Try out check in form"""
    return render(request, 'players/try_out_check_in.html')


@login_required
def search_players_view(request):
    """Search players by name for autocomplete"""
    from .models import Player

    query = request.GET.get('q', '').strip()

    if len(query) < 2:
        return JsonResponse({'results': []})

    # Search by first name or last name
    from django.db.models import Q
    players = Player.objects.filter(
        Q(first_name__icontains=query) | Q(last_name__icontains=query)
    ).order_by('last_name', 'first_name')[:10]  # Limit to 10 results

    results = []
    for player in players:
        results.append({
            'id': player.id,
            'name': f"{player.first_name} {player.last_name}",
            'attended_try_out': player.attended_try_out
        })

    return JsonResponse({'results': results})


@login_required
@require_http_methods(["POST"])
def toggle_try_out_attendance_view(request):
    """Toggle player try-out attendance"""
    from .models import Player

    try:
        data = json.loads(request.body)
        player_id = data.get('player_id')
        attended = data.get('attended')

        if not player_id:
            return JsonResponse({'success': False, 'error': 'Player ID is required'}, status=400)

        player = Player.objects.get(id=player_id)
        player.attended_try_out = attended
        player.save()

        action = "checked in" if attended else "check-in removed"
        message = f"{player.first_name} {player.last_name} has been {action} successfully!"

        return JsonResponse({
            'success': True,
            'message': message,
            'player_name': f"{player.first_name} {player.last_name}",
            'attended': player.attended_try_out
        })
    except Player.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Player not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def team_preferences_analyze_view(request):
    """Analyze team preferences and assign managers to teams"""
    context = {}
    return render(request, 'players/team_preferences_analyze.html', context)


@require_http_methods(["POST"])
def save_team_preferences_view(request):
    """Save team name preferences for a manager"""
    try:
        email = request.POST.get('email', '').strip()
        preferences_json = request.POST.get('preferences', '')

        # Validate email is provided
        if not email:
            return JsonResponse({
                'success': False,
                'error': 'Please enter your email address.'
            }, status=400)

        # Validate preferences data
        if not preferences_json:
            return JsonResponse({
                'success': False,
                'error': 'Please rank at least one team name before submitting.'
            }, status=400)

        # Check if email matches a manager
        try:
            manager = Manager.objects.get(email=email)
        except Manager.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Email address not found. Please make sure you entered the email address that matches your manager registration.'
            }, status=400)

        # Parse the preferences JSON
        try:
            preferences_data = json.loads(preferences_json)
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid preferences data.'
            }, status=400)

        # Validate that all teams are ranked
        total_teams = Team.objects.count()
        ranked_teams = len(preferences_data.get('team_ids', []))

        if ranked_teams != total_teams:
            return JsonResponse({
                'success': False,
                'error': f'You must rank all {total_teams} team names. You have currently ranked {ranked_teams}.'
            }, status=400)

        # Create or update the team preference record
        team_preference, created = TeamPreference.objects.update_or_create(
            manager=manager,
            defaults={'preferences': preferences_data}
        )

        action = 'saved' if created else 'updated'

        return JsonResponse({
            'success': True,
            'message': f'Your team name preferences have been {action} successfully!'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'An error occurred: {str(e)}'
        }, status=500)


@require_http_methods(["POST"])
def run_team_analysis_view(request):
    """Run analysis to match managers with their preferred teams"""
    import random

    try:
        # Validation 1: Check if any managers already have teams assigned
        managers_with_teams = Manager.objects.filter(teams__isnull=False).count()
        if managers_with_teams > 0:
            return JsonResponse({
                'success': False,
                'error': 'Some managers are already assigned to teams. This analysis can only be used when no managers have teams assigned yet.'
            }, status=400)

        # Get all managers and teams
        all_managers = list(Manager.objects.all())
        all_teams = list(Team.objects.all())

        # Validation 2: Check if manager and team counts match
        if len(all_managers) != len(all_teams):
            return JsonResponse({
                'success': False,
                'error': f'The number of managers ({len(all_managers)}) does not match the number of teams ({len(all_teams)}). They must be equal.'
            }, status=400)

        # Separate managers with and without preferences
        managers_with_prefs = []
        managers_without_prefs = []

        for manager in all_managers:
            try:
                pref = TeamPreference.objects.get(manager=manager)
                managers_with_prefs.append({
                    'manager': manager,
                    'preferences': pref.preferences
                })
            except TeamPreference.DoesNotExist:
                managers_without_prefs.append({
                    'manager': manager,
                    'preferences': None
                })

        # Randomly shuffle managers with preferences
        random.shuffle(managers_with_prefs)

        # Create final list: managers with prefs first, then without
        ordered_managers = managers_with_prefs + managers_without_prefs

        # Available teams (will be removed as they're assigned)
        available_teams = {team.id: team for team in all_teams}

        # Assignments
        assignments = []

        for manager_data in ordered_managers:
            manager = manager_data['manager']
            preferences = manager_data['preferences']
            assigned_team = None

            if preferences and 'team_ids' in preferences:
                # Try to assign most preferred available team
                for team_id_str in preferences['team_ids']:
                    team_id = int(team_id_str)
                    if team_id in available_teams:
                        assigned_team = available_teams[team_id]
                        del available_teams[team_id]
                        break

            # If no preference or no preferred team available, assign first available
            if not assigned_team and available_teams:
                team_id = next(iter(available_teams))
                assigned_team = available_teams[team_id]
                del available_teams[team_id]

            assignments.append({
                'manager_id': manager.id,
                'manager_name': f"{manager.first_name} {manager.last_name}",
                'team_id': assigned_team.id if assigned_team else None,
                'team_name': assigned_team.name if assigned_team else None,
                'has_preferences': preferences is not None
            })

        return JsonResponse({
            'success': True,
            'assignments': assignments,
            'all_teams': [{'id': t.id, 'name': t.name} for t in all_teams]
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'An error occurred: {str(e)}'
        }, status=500)


@require_http_methods(["POST"])
def assign_managers_to_teams_view(request):
    """Assign managers to teams based on analysis results"""
    try:
        assignments_json = request.POST.get('assignments', '')

        if not assignments_json:
            return JsonResponse({
                'success': False,
                'error': 'No assignment data provided.'
            }, status=400)

        try:
            assignments = json.loads(assignments_json)
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid assignment data.'
            }, status=400)

        # Validate that each team is assigned exactly once
        team_ids = [a['team_id'] for a in assignments]
        if len(team_ids) != len(set(team_ids)):
            return JsonResponse({
                'success': False,
                'error': 'Each team must be assigned to exactly one manager.'
            }, status=400)

        # Perform the assignments
        for assignment in assignments:
            manager = Manager.objects.get(id=assignment['manager_id'])
            team = Team.objects.get(id=assignment['team_id'])
            team.manager = manager
            team.save()

        return JsonResponse({
            'success': True,
            'message': f'Successfully assigned {len(assignments)} managers to teams!'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'An error occurred: {str(e)}'
        }, status=500)


@require_http_methods(["POST"])
def unassign_all_managers_view(request):
    """Remove all managers from all teams (testing feature)"""
    try:
        # Get all teams and remove their manager assignments
        teams_updated = Team.objects.filter(manager__isnull=False).update(manager=None)

        return JsonResponse({
            'success': True,
            'message': f'Successfully removed {teams_updated} manager assignments from teams.'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'An error occurred: {str(e)}'
        }, status=500)


@require_http_methods(["POST"])
@csrf_exempt
def randomly_assign_managers_view(request):
    """Randomly assign unassigned managers to available teams (testing feature)"""
    import random

    try:
        # Get all unassigned managers
        unassigned_managers = list(Manager.objects.filter(teams__isnull=True))

        if not unassigned_managers:
            return JsonResponse({
                'success': False,
                'error': 'No unassigned managers found. All managers are already assigned to teams.'
            })

        # Get all teams without a manager
        available_teams = list(Team.objects.filter(manager__isnull=True))

        if not available_teams:
            return JsonResponse({
                'success': False,
                'error': 'No available teams found. All teams already have a manager assigned.'
            })

        # Shuffle both lists for randomness
        random.shuffle(unassigned_managers)
        random.shuffle(available_teams)

        # Assign managers to teams (as many as possible)
        assignments_made = 0
        for manager, team in zip(unassigned_managers, available_teams):
            team.manager = manager
            team.save()
            assignments_made += 1

        # Determine how many managers or teams are left over
        managers_left = len(unassigned_managers) - assignments_made
        teams_left = len(available_teams) - assignments_made

        message = f'Successfully assigned {assignments_made} managers to teams.'

        if managers_left > 0:
            message += f' {managers_left} managers remain unassigned (no available teams).'
        elif teams_left > 0:
            message += f' {teams_left} teams remain without managers (no available managers).'

        return JsonResponse({
            'success': True,
            'message': message
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'An error occurred: {str(e)}'
        }, status=500)


@require_http_methods(["POST"])
@csrf_exempt
def randomly_assign_daughters_view(request):
    """Randomly assign all managers to daughters (players) - FOR TESTING ONLY"""
    import random

    try:
        # Get all managers and all players
        managers = list(Manager.objects.all())
        players = list(Player.objects.all())

        if not managers:
            return JsonResponse({
                'success': False,
                'error': 'No managers found in database.'
            })

        if not players:
            return JsonResponse({
                'success': False,
                'error': 'No players found in database.'
            })

        # Shuffle players for randomness
        random.shuffle(players)

        # Assign each manager to a random player
        # If more managers than players, some players will be assigned to multiple managers
        assignments_made = 0
        for i, manager in enumerate(managers):
            # Use modulo to cycle through players if we run out
            player = players[i % len(players)]
            manager.daughter = player
            manager.save()
            assignments_made += 1

        message = f'Successfully assigned {assignments_made} managers to daughters.'
        message += f' Managers: {len(managers)}, Players: {len(players)}.'

        if len(managers) > len(players):
            message += f' Note: Some players were assigned to multiple managers because there are more managers than players.'

        return JsonResponse({
            'success': True,
            'message': message
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'An error occurred: {str(e)}'
        }, status=500)


@require_http_methods(["GET"])
def get_manager_emails_view(request):
    """Get all manager email addresses"""
    try:
        managers = Manager.objects.all().order_by('first_name', 'last_name')
        emails = [manager.email for manager in managers if manager.email]

        return JsonResponse({
            'success': True,
            'emails': emails
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["POST"])
def send_team_preferences_email_view(request):
    """Send team preferences email to all managers"""
    from django.core.mail import EmailMultiAlternatives
    from django.conf import settings as django_settings
    from django.utils.html import strip_tags

    try:
        subject = request.POST.get('subject', '').strip()
        html_body = request.POST.get('body', '').strip()
        cc_emails = request.POST.get('cc_emails', '').strip()

        if not subject or not html_body:
            return JsonResponse({
                'success': False,
                'error': 'Subject and body are required.'
            }, status=400)

        # Get all managers
        managers = Manager.objects.all()
        if not managers:
            return JsonResponse({
                'success': False,
                'error': 'No managers found in the database.'
            }, status=400)

        # Parse CC emails
        cc_list = []
        if cc_emails:
            cc_list = [email.strip() for email in cc_emails.split(',') if email.strip()]

        # Create plain text version from HTML
        text_body = strip_tags(html_body)

        # Send email to each manager
        sent_count = 0
        failed_emails = []

        for manager in managers:
            if manager.email:
                try:
                    msg = EmailMultiAlternatives(
                        subject=subject,
                        body=text_body,
                        from_email=django_settings.DEFAULT_FROM_EMAIL,
                        to=[manager.email],
                        cc=cc_list if cc_list else None,
                    )
                    msg.attach_alternative(html_body, "text/html")
                    msg.send(fail_silently=False)
                    sent_count += 1
                except Exception as e:
                    failed_emails.append(f"{manager.email} ({str(e)})")

        if failed_emails:
            return JsonResponse({
                'success': False,
                'error': f'Sent {sent_count} emails but failed to send to: {", ".join(failed_emails)}'
            }, status=500)

        return JsonResponse({
            'success': True,
            'message': f'Successfully sent {sent_count} emails to managers!'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'An error occurred: {str(e)}'
        }, status=500)


@login_required
def manage_practice_slots_view(request):
    """View to manage practice slots with CRUD operations"""
    from .models import PracticeSlot

    practice_slots = PracticeSlot.objects.all().order_by('-created_at')

    context = {
        'practice_slots': practice_slots
    }

    return render(request, 'players/manage_practice_slots.html', context)


@login_required
@require_http_methods(["POST"])
def create_practice_slot_view(request):
    """Create a new practice slot"""
    from .models import PracticeSlot

    try:
        practice_slot = request.POST.get('practice_slot', '').strip()

        if not practice_slot:
            return JsonResponse({
                'success': False,
                'error': 'Practice slot text is required.'
            }, status=400)

        slot = PracticeSlot.objects.create(practice_slot=practice_slot)

        return JsonResponse({
            'success': True,
            'message': 'Practice slot created successfully!',
            'slot': {
                'id': slot.id,
                'practice_slot': slot.practice_slot,
                'created_at': slot.created_at.strftime('%Y-%m-%d %H:%M:%S')
            }
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'An error occurred: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def update_practice_slot_view(request, pk):
    """Update an existing practice slot"""
    from .models import PracticeSlot

    try:
        slot = PracticeSlot.objects.get(pk=pk)
        practice_slot = request.POST.get('practice_slot', '').strip()

        if not practice_slot:
            return JsonResponse({
                'success': False,
                'error': 'Practice slot text is required.'
            }, status=400)

        slot.practice_slot = practice_slot
        slot.save()

        return JsonResponse({
            'success': True,
            'message': 'Practice slot updated successfully!',
            'slot': {
                'id': slot.id,
                'practice_slot': slot.practice_slot,
                'updated_at': slot.updated_at.strftime('%Y-%m-%d %H:%M:%S')
            }
        })
    except PracticeSlot.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Practice slot not found.'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'An error occurred: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def delete_practice_slot_view(request, pk):
    """Delete a practice slot"""
    from .models import PracticeSlot

    try:
        slot = PracticeSlot.objects.get(pk=pk)
        slot.delete()

        return JsonResponse({
            'success': True,
            'message': 'Practice slot deleted successfully!'
        })
    except PracticeSlot.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Practice slot not found.'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'An error occurred: {str(e)}'
        }, status=500)
