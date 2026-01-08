from django.core.management.base import BaseCommand
from players.models import Team


class Command(BaseCommand):
    help = 'Remove coach names from preseason practice slots'

    def handle(self, *args, **options):
        teams = Team.objects.exclude(preseason_practice_slot__isnull=True).exclude(preseason_practice_slot='')

        updated_count = 0

        for team in teams:
            # Split by comma and remove the last part (coach name)
            parts = [p.strip() for p in team.preseason_practice_slot.split(',')]

            if len(parts) > 1:
                # Rejoin all parts except the last one
                new_value = ', '.join(parts[:-1])

                self.stdout.write(f'{team.name}:')
                self.stdout.write(f'  Old: {team.preseason_practice_slot}')
                self.stdout.write(f'  New: {new_value}')

                team.preseason_practice_slot = new_value
                team.save()
                updated_count += 1

        self.stdout.write(self.style.SUCCESS(f'\nTotal teams updated: {updated_count}'))
