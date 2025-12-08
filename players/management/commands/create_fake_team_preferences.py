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

        for manager in managers:
            # Shuffle teams to create random preferences
            shuffled_teams = random.sample(teams, len(teams))

            # Create preferences data
            preferences_data = {
                'team_ids': [str(team.id) for team in shuffled_teams],
                'team_names': [team.name for team in shuffled_teams]
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
