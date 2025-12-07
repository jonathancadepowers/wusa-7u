from django.core.management.base import BaseCommand
from players.models import Player, Draft


class Command(BaseCommand):
    help = 'Check if players were added after draft was created'

    def handle(self, *args, **options):
        draft = Draft.objects.latest('created_at')
        self.stdout.write(f'Draft created at: {draft.created_at}')
        self.stdout.write(f'Draft last updated at: {draft.updated_at}')

        total_players = Player.objects.count()
        self.stdout.write(f'\nTotal players now: {total_players}')

        players_before_draft = Player.objects.filter(created_at__lte=draft.created_at).count()
        players_after_draft = Player.objects.filter(created_at__gt=draft.created_at).count()

        self.stdout.write(f'Players created before draft: {players_before_draft}')
        self.stdout.write(f'Players created after draft: {players_after_draft}')

        if players_after_draft > 0:
            self.stdout.write('\nPlayers added after draft was created:')
            for p in Player.objects.filter(created_at__gt=draft.created_at).order_by('created_at'):
                self.stdout.write(f'  - {p.first_name} {p.last_name} (created: {p.created_at})')
