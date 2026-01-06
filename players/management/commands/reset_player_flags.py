from django.core.management.base import BaseCommand
from players.models import Player


class Command(BaseCommand):
    help = 'Reset all players to draftable=True and attended_try_out=False'

    def handle(self, *args, **options):
        # Update all players
        updated_count = Player.objects.all().update(
            draftable=True,
            attended_try_out=False
        )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully updated {updated_count} players:\n'
                f'  - draftable: True\n'
                f'  - attended_try_out: False'
            )
        )
