from django.core.management.base import BaseCommand
from players.models import Team


class Command(BaseCommand):
    help = 'Populate preseason practice slots for all teams'

    def handle(self, *args, **options):
        # Format: Day, Time, Location, Manager, Team Name
        slots_data = [
            "Saturday, 9am, Pershing, RRutherford, Monsoon",
            "Saturday, 10am, Pershing, WThompson, Sandstorm",
            "Saturday, 11am, Pershing, G Jackson, Cyclones",
            "Saturday, 12pm, Pershing, M Venditti, Tsunamis",
            "Saturday, 1pm, Pershing, W Brown, Lightning",
            "Saturday, 2pm, Pershing, Slattery, Blizzard",
            "Saturday, 3pm, Pershing, J Conley, Hailstorm",
            "Saturday, 10am, Bayland 1, JCaraway, Fireballs",
            "Sunday, 1pm, Gilbert, Hughes, Whirlwind",
            "Sunday, 2pm, Gilbert, JRadcliffe, Hurricanes",
            "Sunday, 3pm, Gilbert, S. Miller, Earthquakes",
            "Sunday, 4pm, Gilbert, RWalker, Thunder",
            "Sunday, 1pm, Ahrens, UAladroos, Avalanche",
            "Sunday, 2pm, Ahrens, CButtry, Heatwave",
            "Sunday, 3pm, Ahrens, DHarris, Wildfire",
            "Sunday, 4pm, Old Ahrens, BHeard, Tornadoes",
            "Sunday, 5pm, Old Ahrens, Toden, Volcanoes",
        ]

        updated_count = 0
        not_found = []

        for slot_line in slots_data:
            # Split by comma and extract team name (last item)
            parts = [p.strip() for p in slot_line.split(',')]
            team_name = parts[-1]

            # The preseason practice slot text is everything except the team name
            preseason_slot = ', '.join(parts[:-1])

            try:
                team = Team.objects.get(name=team_name)
                team.preseason_practice_slot = preseason_slot
                team.save()
                updated_count += 1
                self.stdout.write(self.style.SUCCESS(f'Updated {team_name}: {preseason_slot}'))
            except Team.DoesNotExist:
                not_found.append(team_name)
                self.stdout.write(self.style.WARNING(f'Team not found: {team_name}'))

        self.stdout.write(self.style.SUCCESS(f'\nTotal teams updated: {updated_count}'))

        if not_found:
            self.stdout.write(self.style.WARNING(f'Teams not found: {", ".join(not_found)}'))
