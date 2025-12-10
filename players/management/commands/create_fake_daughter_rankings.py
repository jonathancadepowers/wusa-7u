from django.core.management.base import BaseCommand
from players.models import Manager, Player, ManagerDaughterRanking
import random
import json


class Command(BaseCommand):
    help = 'Create fake manager daughter rankings with correct JSON format'

    def handle(self, *args, **options):
        # Get all managers
        managers = list(Manager.objects.all())

        if not managers:
            self.stdout.write(self.style.ERROR("No managers found in database"))
            return

        # Get all players who are managers' daughters
        manager_daughter_ids = Manager.objects.filter(daughter__isnull=False).values_list('daughter_id', flat=True)
        daughter_players = list(Player.objects.filter(id__in=manager_daughter_ids))

        if not daughter_players:
            self.stdout.write(self.style.ERROR("No manager daughters found in database"))
            return

        self.stdout.write(f"Found {len(managers)} managers and {len(daughter_players)} manager daughters")

        # Create manager daughter rankings for each manager
        created_count = 0
        for manager in managers:
            # Create a shuffled list of manager's daughters
            shuffled = list(daughter_players)
            random.shuffle(shuffled)

            # Create ranking data in the correct format: [{"player_id": 1, "rank": 1}, ...]
            ranking_data = [{"player_id": p.id, "rank": idx + 1} for idx, p in enumerate(shuffled)]

            # Create the ManagerDaughterRanking record
            ManagerDaughterRanking.objects.create(
                manager=manager,
                ranking=json.dumps(ranking_data)
            )

            created_count += 1
            self.stdout.write(f"Created ManagerDaughterRanking {created_count} for manager: {manager.first_name} {manager.last_name}")

        self.stdout.write(self.style.SUCCESS(f"\nTotal ManagerDaughterRanking records created: {created_count}"))
        self.stdout.write(self.style.SUCCESS(f"Total in database: {ManagerDaughterRanking.objects.count()}"))
