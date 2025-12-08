from django.core.management.base import BaseCommand
from players.models import PracticeSlot, Team


class Command(BaseCommand):
    help = 'Create practice slots - one per team with realistic time slots'

    def handle(self, *args, **options):
        # Count teams to determine how many slots to create
        team_count = Team.objects.count()

        # If no teams, default to 8 slots
        slots_to_create = max(team_count, 8)

        # Realistic practice slot times
        practice_slots = [
            "Monday 5:00 PM - 6:00 PM",
            "Monday 6:00 PM - 7:00 PM",
            "Tuesday 5:00 PM - 6:00 PM",
            "Tuesday 6:00 PM - 7:00 PM",
            "Wednesday 5:00 PM - 6:00 PM",
            "Wednesday 6:00 PM - 7:00 PM",
            "Thursday 5:00 PM - 6:00 PM",
            "Thursday 6:00 PM - 7:00 PM",
            "Friday 5:00 PM - 6:00 PM",
            "Friday 6:00 PM - 7:00 PM",
            "Saturday 9:00 AM - 10:00 AM",
            "Saturday 10:00 AM - 11:00 AM",
        ]

        # Clear existing practice slots
        existing_count = PracticeSlot.objects.count()
        if existing_count > 0:
            PracticeSlot.objects.all().delete()
            self.stdout.write(
                self.style.WARNING(f'Deleted {existing_count} existing practice slot(s)')
            )

        # Create slots
        created_count = 0
        for i in range(slots_to_create):
            slot_text = practice_slots[i % len(practice_slots)]
            PracticeSlot.objects.create(practice_slot=slot_text)
            created_count += 1
            self.stdout.write(
                self.style.SUCCESS(f'Created practice slot: {slot_text}')
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nCompleted! Created {created_count} practice slot(s) based on {team_count} team(s) in database.'
            )
        )
