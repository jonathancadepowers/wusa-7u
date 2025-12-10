from django.core.management.base import BaseCommand
from players.models import Manager, Player
import random


class Command(BaseCommand):
    help = 'Randomly assign all managers to daughters (players) - FOR TESTING ONLY'

    def handle(self, *args, **options):
        # Get all managers and all players
        managers = list(Manager.objects.all())
        players = list(Player.objects.all())

        if not managers:
            self.stdout.write(self.style.ERROR('No managers found in database'))
            return

        if not players:
            self.stdout.write(self.style.ERROR('No players found in database'))
            return

        # Shuffle players for randomness
        random.shuffle(players)

        # Assign each manager to a random player
        # If more managers than players, some players will be assigned to multiple managers
        assignments_made = 0
        for i, manager in enumerate(managers):
            # Use modulo to cycle through players if we run out
            player = players[i % len(players)]
            manager.daughter = player
            manager.save()
            assignments_made += 1
            self.stdout.write(f'Assigned {manager.first_name} {manager.last_name} to daughter: {player.first_name} {player.last_name}')

        self.stdout.write(self.style.SUCCESS(f'\nTotal assignments made: {assignments_made}'))
        self.stdout.write(f'Managers: {len(managers)}, Players: {len(players)}')
