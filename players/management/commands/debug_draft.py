from django.core.management.base import BaseCommand
from players.models import Player, Draft, DraftPick


class Command(BaseCommand):
    help = 'Debug draft configuration'

    def handle(self, *args, **options):
        draft = Draft.objects.latest('created_at')
        total_players = Player.objects.count()
        total_slots = draft.rounds * draft.picks_per_round

        if draft.final_round_draft_order:
            final_round_team_ids = [int(tid) for tid in draft.final_round_draft_order.split(',') if tid]
            total_slots += len(final_round_team_ids)
            self.stdout.write(f'Final round teams: {len(final_round_team_ids)}')

        drafted_count = DraftPick.objects.filter(player__isnull=False).count()

        self.stdout.write(f'Total players: {total_players}')
        self.stdout.write(f'Rounds: {draft.rounds}')
        self.stdout.write(f'Picks per round: {draft.picks_per_round}')
        self.stdout.write(f'Total draft slots: {total_slots}')
        self.stdout.write(f'Players currently drafted: {drafted_count}')
        self.stdout.write(f'Difference: {total_slots - drafted_count}')
