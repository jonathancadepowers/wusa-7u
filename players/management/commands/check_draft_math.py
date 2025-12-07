from django.core.management.base import BaseCommand
from players.models import Player, Draft, Team


class Command(BaseCommand):
    help = 'Check draft math'

    def handle(self, *args, **options):
        draft = Draft.objects.latest('created_at')
        total_players = Player.objects.filter(draftable=True).count()
        num_teams = Team.objects.count()
        
        self.stdout.write(f'Total draftable players: {total_players}')
        self.stdout.write(f'Number of teams: {num_teams}')
        self.stdout.write(f'Players ÷ Teams = {total_players / num_teams if num_teams > 0 else 0}')
        self.stdout.write(f'')
        self.stdout.write(f'Draft configuration:')
        self.stdout.write(f'  Rounds: {draft.rounds}')
        self.stdout.write(f'  Picks per round: {draft.picks_per_round}')
        self.stdout.write(f'  Regular picks: {draft.rounds * draft.picks_per_round}')
        
        if draft.final_round_draft_order:
            final_round_teams = len([tid for tid in draft.final_round_draft_order.split(',') if tid])
            self.stdout.write(f'  Final round picks: {final_round_teams}')
            total_slots = draft.rounds * draft.picks_per_round + final_round_teams
        else:
            total_slots = draft.rounds * draft.picks_per_round
            
        self.stdout.write(f'  Total slots: {total_slots}')
        self.stdout.write(f'')
        self.stdout.write(f'Expected: {total_players} players = {total_slots} slots')
        self.stdout.write(f'Actual difference: {total_slots - total_players} (slots - players)')
