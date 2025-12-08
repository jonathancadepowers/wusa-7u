import random
from django.core.management.base import BaseCommand
from players.models import Manager, Team, TeamPreference


class Command(BaseCommand):
    help = 'Create fake team preferences for all managers (for testing purposes)'

    def handle(self, *args, **options):
        managers = Manager.objects.all()
        teams = list(Team.objects.all())

        if not teams:
            self.stdout.write(self.style.ERROR('No teams found in database.'))
            return

        created_count = 0
        updated_count = 0

        # Find Blazing Comets team
        blazing_comets = None
        for team in teams:
            if team.name == 'Blazing Comets':
                blazing_comets = team
                break

        if not blazing_comets:
            self.stdout.write(self.style.ERROR('Blazing Comets team not found in database.'))
            return

        for manager in managers:
            # Start with Blazing Comets as first choice
            # Then shuffle the remaining teams
            other_teams = [t for t in teams if t.id != blazing_comets.id]
            shuffled_other_teams = random.sample(other_teams, len(other_teams))

            # Blazing Comets first, then random order for the rest
            ordered_teams = [blazing_comets] + shuffled_other_teams

            # Create preferences data
            preferences_data = {
                'team_ids': [str(team.id) for team in ordered_teams],
                'team_names': [team.name for team in ordered_teams]
            }

            # Create or update team preference
            team_preference, created = TeamPreference.objects.update_or_create(
                manager=manager,
                defaults={'preferences': preferences_data}
            )

            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created preferences for {manager.first_name} {manager.last_name}')
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'Updated preferences for {manager.first_name} {manager.last_name}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nCompleted! Created: {created_count}, Updated: {updated_count}, Total: {created_count + updated_count}'
            )
        )
