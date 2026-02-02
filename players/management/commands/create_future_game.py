from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from players.models import Team, Event, Roster, EventType


class Command(BaseCommand):
    help = 'Create a future game for the Avalanche team to test reuse roster feature'

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

        # Find another team to be the opponent (different from Blizzard if possible)
        opponent = Team.objects.exclude(id=avalanche.id).exclude(name__icontains='Blizzard').first()
        if not opponent:
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

        # Create a future event (7 days from now)
        future_timestamp = timezone.now() + timedelta(days=7)

        event = Event.objects.create(
            name=f'{avalanche.name} vs {opponent.name}',
            event_type=event_type,
            timestamp=future_timestamp,
            location='Main Field',
            home_team=avalanche,
            away_team=opponent
        )
        self.stdout.write(f'Created event: {event.name} on {future_timestamp}')

        # Create an empty roster for this game (no assignments yet)
        roster = Roster.objects.create(
            event=event,
            team=avalanche,
            inning_1={},
            inning_2={},
            inning_3={},
            inning_4={},
            inning_5={},
            inning_6={},
            lineup=[]
        )

        self.stdout.write(self.style.SUCCESS(f'Created roster with ID: {roster.id}'))
        self.stdout.write(self.style.SUCCESS(f'Now go to roster {roster.id} and use "Reuse Previous Roster" to load from the Blizzard game!'))
