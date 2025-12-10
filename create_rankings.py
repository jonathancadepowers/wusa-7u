import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wusa.settings')
django.setup()

from players.models import Manager, Player, PlayerRanking
import random
import json

# Get all managers and players
managers = list(Manager.objects.all())
players = list(Player.objects.all())

if not managers:
    print("No managers found in database")
elif not players:
    print("No players found in database")
else:
    print(f"Found {len(managers)} managers and {len(players)} players")

    # Create 17 player rankings with correct JSON format
    created_count = 0
    for i in range(17):
        # Use modulo to cycle through managers if we have fewer than 17
        mgr = managers[i % len(managers)]

        # Create a shuffled list of players
        shuffled = list(players)
        random.shuffle(shuffled)

        # Create ranking data in the correct format: [{"player_id": 1, "rank": 1}, ...]
        ranking_data = [{"player_id": p.id, "rank": idx + 1} for idx, p in enumerate(shuffled)]

        # Create the PlayerRanking record
        PlayerRanking.objects.create(
            manager=mgr,
            ranking=json.dumps(ranking_data)
        )

        created_count += 1
        print(f"Created PlayerRanking {created_count} for manager: {mgr.first_name} {mgr.last_name}")

    print(f"\nTotal PlayerRanking records created: {created_count}")
    print(f"Total in database: {PlayerRanking.objects.count()}")
