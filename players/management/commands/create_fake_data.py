from django.core.management.base import BaseCommand
from players.models import Manager, Player, PlayerRanking
import random
import json
from datetime import date, timedelta


class Command(BaseCommand):
    help = 'Create fake players and 17 player rankings with realistic JSON data'

    def handle(self, *args, **options):
        # First, create 50 fake players
        first_names = [
            'Emma', 'Olivia', 'Ava', 'Isabella', 'Sophia', 'Mia', 'Charlotte', 'Amelia',
            'Harper', 'Evelyn', 'Abigail', 'Emily', 'Elizabeth', 'Sofia', 'Avery', 'Ella',
            'Madison', 'Scarlett', 'Victoria', 'Aria', 'Grace', 'Chloe', 'Camila', 'Penelope',
            'Riley', 'Layla', 'Lillian', 'Nora', 'Zoey', 'Mila', 'Aubrey', 'Hannah', 'Lily',
            'Addison', 'Eleanor', 'Natalie', 'Luna', 'Savannah', 'Brooklyn', 'Leah', 'Zoe',
            'Stella', 'Hazel', 'Ellie', 'Paisley', 'Audrey', 'Skylar', 'Violet', 'Claire', 'Bella'
        ]

        last_names = [
            'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis',
            'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson',
            'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin', 'Lee', 'Thompson', 'White',
            'Harris', 'Clark', 'Lewis', 'Robinson', 'Walker', 'Hall', 'Allen', 'Young',
            'King', 'Wright', 'Hill', 'Green', 'Adams', 'Baker', 'Nelson', 'Carter', 'Mitchell',
            'Roberts', 'Turner', 'Phillips', 'Campbell', 'Parker', 'Evans', 'Edwards', 'Collins', 'Stewart', 'Morris'
        ]

        schools = [
            'Washington Elementary', 'Lincoln Elementary', 'Roosevelt Elementary', 'Jefferson Elementary',
            'Madison Elementary', 'Franklin Elementary', 'Wilson Elementary', 'Kennedy Elementary',
            'Monroe Elementary', 'Jackson Elementary'
        ]

        # Create 50 players
        players_created = 0
        for i in range(50):
            # Random birthday for 7U (6-7 years old)
            days_ago = random.randint(365 * 6, 365 * 8)
            birthday = date.today() - timedelta(days=days_ago)

            Player.objects.create(
                first_name=first_names[i],
                last_name=last_names[i],
                birthday=birthday,
                school=random.choice(schools),
                parent_phone_1=f'555-{random.randint(100, 999)}-{random.randint(1000, 9999)}',
                parent_email_1=f'{first_names[i].lower()}.{last_names[i].lower()}@example.com',
                jersey_size=random.choice(['XS', 'S', 'M']),
                attended_try_out=True,
                draftable=True
            )
            players_created += 1

        self.stdout.write(self.style.SUCCESS(f'Created {players_created} fake players'))

        # Get all managers and players
        managers = list(Manager.objects.all())
        players = list(Player.objects.all())

        if len(managers) < 17:
            self.stdout.write(self.style.ERROR(f'Need at least 17 managers, only found {len(managers)}'))
            return

        self.stdout.write(f'Found {len(managers)} managers and {len(players)} players')

        # Create exactly 17 player rankings, one per unique manager
        created_count = 0
        for i in range(17):
            # Use the i-th manager (ensures uniqueness)
            mgr = managers[i]

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
            self.stdout.write(f'Created PlayerRanking {created_count} for manager: {mgr.first_name} {mgr.last_name}')

        self.stdout.write(self.style.SUCCESS(f'\nTotal PlayerRanking records created: {created_count}'))
        self.stdout.write(self.style.SUCCESS(f'Total in database: {PlayerRanking.objects.count()}'))
