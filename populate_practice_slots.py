import os
import django
import random

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from players.models import Team

# Define realistic practice slots
days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
times = ['6:00pm', '6:30pm', '7:00pm', '7:30pm', '8:00pm']
locations = ['South Campus', 'Bayland', 'North Park', 'West Field', 'Central Rec', 'East Side Complex']

# Get all teams
teams = Team.objects.all()

print(f"Found {teams.count()} teams")
print("Populating practice slots...\n")

for team in teams:
    # Generate random but realistic practice slot
    day = random.choice(days)
    time = random.choice(times)
    location = random.choice(locations)

    practice_slot = f"{day}, {time}, {location}"

    team.practice_slot = practice_slot
    team.save()

    print(f"✓ {team.name}: {practice_slot}")

print(f"\nSuccessfully populated practice slots for {teams.count()} teams!")
