#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from players.models import Manager, Player
import random

# Get all managers and players
managers = list(Manager.objects.all())
players = list(Player.objects.all())

print(f"Total managers: {len(managers)}")
print(f"Total players: {len(players)}")

if managers and players:
    print("\nAssigning daughters to managers:\n")

    # Get players who are not already daughters
    assigned_daughter_ids = set(Manager.objects.filter(daughter__isnull=False).values_list('daughter_id', flat=True))
    available_players = [p for p in players if p.id not in assigned_daughter_ids]

    print(f"Available players (not already daughters): {len(available_players)}")

    count = 0
    for manager in managers:
        if manager.daughter:
            print(f"✓ {manager.first_name} {manager.last_name} already has daughter: {manager.daughter.first_name} {manager.daughter.last_name}")
        elif available_players:
            # Randomly assign a daughter
            selected_player = random.choice(available_players)
            manager.daughter = selected_player
            manager.save()
            available_players.remove(selected_player)
            count += 1
            print(f"✓ Assigned {selected_player.first_name} {selected_player.last_name} to {manager.first_name} {manager.last_name}")
        else:
            print(f"✗ No available players left for {manager.first_name} {manager.last_name}")

    print(f"\n{count} new daughters assigned!")
else:
    print("No managers or players found")
