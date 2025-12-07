from django.core.management.base import BaseCommand
from players.models import Player, DraftPick


class Command(BaseCommand):
    help = 'Check available players'

    def handle(self, *args, **options):
        drafted_ids = list(DraftPick.objects.filter(player__isnull=False).values_list('player_id', flat=True))
        self.stdout.write(f'Drafted player IDs count: {len(drafted_ids)}')
        self.stdout.write(f'Unique drafted IDs: {len(set(drafted_ids))}')

        total_players = Player.objects.count()
        self.stdout.write(f'Total players: {total_players}')

        available = Player.objects.exclude(id__in=drafted_ids)
        self.stdout.write(f'Available players: {available.count()}')
        for p in available:
            self.stdout.write(f'  - {p.first_name} {p.last_name} (ID: {p.id})')

        # Check if either of the two players showing up are actually drafted
        nora = Player.objects.filter(first_name='Nora', last_name='Amanullah').first()
        hayden = Player.objects.filter(first_name='Hayden', last_name='Heard').first()

        if nora:
            nora_drafted = DraftPick.objects.filter(player=nora).exists()
            self.stdout.write(f'\nNora Amanullah (ID: {nora.id}) drafted: {nora_drafted}')

        if hayden:
            hayden_drafted = DraftPick.objects.filter(player=hayden).exists()
            self.stdout.write(f'Hayden Heard (ID: {hayden.id}) drafted: {hayden_drafted}')
