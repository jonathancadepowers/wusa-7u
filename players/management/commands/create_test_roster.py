from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from players.models import Team, Event, Roster, EventType


class Command(BaseCommand):
    help = 'Create a test previous game and roster for the Avalanche team'

    def handle(self, *args, **options):
        # Find the Avalanche team
        try:
            avalanche = Team.objects.get(name__icontains='Avalanche')
        except Team.DoesNotExist:
            self.stdout.write(self.style.ERROR('Avalanche team not found'))
            return
        except Team.MultipleObjectsReturned:
            avalanche = Team.objects.filter(name__icontains='Avalanche').first()

        self.stdout.write(f'Found team: {avalanche.name}')

        # Find another team to be the opponent
        opponent = Team.objects.exclude(id=avalanche.id).first()
        if not opponent:
            self.stdout.write(self.style.ERROR('No other team found to be opponent'))
            return

        self.stdout.write(f'Opponent team: {opponent.name}')

        # Get or create a Game event type
        event_type, _ = EventType.objects.get_or_create(
            name='Game',
            defaults={'color': '#0d6efd'}
        )

        # Create a previous event (7 days ago)
        previous_timestamp = timezone.now() - timedelta(days=7)

        event = Event.objects.create(
            name=f'{avalanche.name} vs {opponent.name}',
            event_type=event_type,
            timestamp=previous_timestamp,
            location='Test Field',
            home_team=avalanche,
            away_team=opponent
        )
        self.stdout.write(f'Created event: {event.name}')

        # Get the players from the Avalanche team
        players = list(avalanche.players.all())
        if len(players) < 9:
            self.stdout.write(self.style.WARNING(f'Only {len(players)} players found, need at least 9 for full roster'))

        # Create position assignments
        positions = ['C', 'P', '1B', '2B', '3B', 'SS', 'LF', 'CF', 'RF']

        inning_data = {}
        for i, pos in enumerate(positions):
            if i < len(players):
                inning_data[pos] = str(players[i].id)

        # Create lineup (all players in order)
        lineup = [str(p.id) for p in players]

        # Create the roster with some variety in innings
        roster = Roster.objects.create(
            event=event,
            team=avalanche,
            inning_1=inning_data.copy(),
            inning_2=self._rotate_positions(inning_data, players, 1),
            inning_3=self._rotate_positions(inning_data, players, 2),
            inning_4=self._rotate_positions(inning_data, players, 3),
            inning_5=self._rotate_positions(inning_data, players, 4),
            inning_6=self._rotate_positions(inning_data, players, 5),
            lineup=lineup
        )

        self.stdout.write(self.style.SUCCESS(f'Created roster with ID: {roster.id}'))
        self.stdout.write(self.style.SUCCESS('Test data created successfully!'))

    def _rotate_positions(self, base_data, players, rotation):
        """Rotate player positions for variety"""
        positions = list(base_data.keys())
        player_ids = list(base_data.values())

        if len(player_ids) == 0:
            return {}

        # Rotate the player IDs
        rotated = player_ids[rotation:] + player_ids[:rotation]

        result = {}
        for i, pos in enumerate(positions):
            if i < len(rotated):
                result[pos] = rotated[i]

        return result
