from django.core.management.base import BaseCommand
from players.models import Player


class Command(BaseCommand):
    help = 'Reset all players attended_try_out field to False'

    def handle(self, *args, **options):
        # Update all players to set attended_try_out to False
        updated_count = Player.objects.update(attended_try_out=False)

        self.stdout.write(
            self.style.SUCCESS(f'Successfully reset attended_try_out to False for {updated_count} players')
        )
