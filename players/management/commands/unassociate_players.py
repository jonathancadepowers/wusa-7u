from django.core.management.base import BaseCommand
from players.models import Player, DraftPick


class Command(BaseCommand):
    help = 'Unassociate all players from their teams and reset assignment flags'

    def handle(self, *args, **options):
        count = Player.objects.filter(team__isnull=False).count()
        self.stdout.write(f'Found {count} players currently assigned to teams')

        # Unassociate players from teams
        Player.objects.all().update(team=None)

        # Reset the player_assigned_to_team flag on all draft picks
        flag_reset_count = DraftPick.objects.filter(player_assigned_to_team=True).update(player_assigned_to_team=False)
        self.stdout.write(f'Reset {flag_reset_count} draft pick assignment flags')

        self.stdout.write(self.style.SUCCESS(
            f'Successfully unassociated all {count} players from their teams and reset assignment flags'
        ))
