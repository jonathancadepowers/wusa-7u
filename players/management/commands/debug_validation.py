from django.core.management.base import BaseCommand
from players.models import Player, DraftPick, Draft


class Command(BaseCommand):
    help = 'Debug validation logic'

    def handle(self, *args, **options):
        try:
            # Get most recent draft
            draft = Draft.objects.latest('created_at')
            self.stdout.write(f'Draft ID: {draft.id}')

            # Calculate total draft slots
            total_slots = draft.rounds * draft.picks_per_round
            if draft.final_round_draft_order:
                final_round_team_ids = [int(tid) for tid in draft.final_round_draft_order.split(',') if tid]
                total_slots += len(final_round_team_ids)
                self.stdout.write(f'Final round teams: {len(final_round_team_ids)}')
            self.stdout.write(f'Total slots: {total_slots}')

            # Count filled slots
            filled_slots = DraftPick.objects.filter(player__isnull=False).count()
            self.stdout.write(f'Filled slots: {filled_slots}')

            # Unfilled slots
            unfilled_slots = total_slots - filled_slots
            self.stdout.write(f'Unfilled slots: {unfilled_slots}')

            # Get drafted player IDs
            drafted_player_ids = set(DraftPick.objects.filter(player__isnull=False).values_list('player_id', flat=True))
            self.stdout.write(f'Drafted player count: {len(drafted_player_ids)}')

            # Pre-assigned count
            pre_assigned_count = Player.objects.filter(team__isnull=False).exclude(id__in=drafted_player_ids).count()
            self.stdout.write(f'Pre-assigned count: {pre_assigned_count}')

            # Total players with teams
            total_with_teams = Player.objects.filter(team__isnull=False).count()
            self.stdout.write(f'Total players with teams: {total_with_teams}')

            # Show some pre-assigned players if any
            if pre_assigned_count > 0:
                pre_assigned_players = Player.objects.filter(team__isnull=False).exclude(id__in=drafted_player_ids)[:5]
                self.stdout.write('\nFirst 5 pre-assigned players:')
                for p in pre_assigned_players:
                    self.stdout.write(f'  - {p.first_name} {p.last_name} (ID: {p.id}, Team: {p.team.name if p.team else "None"})')

        except Draft.DoesNotExist:
            self.stdout.write(self.style.ERROR('No draft found'))
        except Exception as e:
            import traceback
            self.stdout.write(self.style.ERROR(f'Error: {e}'))
            self.stdout.write(traceback.format_exc())
