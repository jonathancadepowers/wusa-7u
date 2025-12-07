from django.core.management.base import BaseCommand
from players.models import Player


class Command(BaseCommand):
    help = 'Unassociate all players from their teams'

    def handle(self, *args, **options):
        count = Player.objects.filter(team__isnull=False).count()
        self.stdout.write(f'Found {count} players currently assigned to teams')
        
        Player.objects.all().update(team=None)
        
        self.stdout.write(self.style.SUCCESS(
            f'Successfully unassociated all {count} players from their teams'
        ))
