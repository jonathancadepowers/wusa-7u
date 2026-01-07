from django.core.management.base import BaseCommand
from players.models import PracticeSlot


class Command(BaseCommand):
    help = 'Insert 18 new practice slots into the database'

    def handle(self, *args, **options):
        practice_slots = [
            "Monday, 5:30 PM, Old Ahrens, Oden",
            "Monday, 6:00 PM, McGovern, Thompson",
            "Monday, 6:30 PM, Old Ahrens, Jackson",
            "Monday, 6:30 PM, Bayland 1, Mendez",
            "Monday, 5:30 PM, Bayland 2, Caraway",
            "Tuesday, 6:00 PM, McGovern, Rutherford",
            "Tuesday, 6:30 PM, Old Ahrens, Brown",
            "Tuesday, 6:30 PM, Bayland 1, Conley",
            "Wednesday, 5:30 PM, Old Ahrens, Radcliffe",
            "Wednesday, 6:00 PM, McGovern, Hughes",
            "Wednesday, 6:30 PM, Ahrens, Buttry",
            "Wednesday, 6:30 PM, Old Ahrens, Heard",
            "Wednesday, 6:30 PM, Bayland 1, Miller",
            "Wednesday, 5:30 PM, Bayland 2, Slattery",
            "Thursday, 5:30 PM, Old Ahrens, Harris",
            "Thursday, 6:30 PM, Ahrens, Walker",
            "Thursday, 6:30 PM, Old Ahrens, Aladroos",
            "Thursday, 6:30 PM, Bayland 1, Venditti"
        ]

        created_count = 0
        for slot_text in practice_slots:
            slot, created = PracticeSlot.objects.get_or_create(practice_slot=slot_text)
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Created: {slot_text}'))
            else:
                self.stdout.write(f'Already exists: {slot_text}')

        self.stdout.write(self.style.SUCCESS(f'\nTotal created: {created_count}'))
        self.stdout.write(self.style.SUCCESS(f'Total practice slots in database: {PracticeSlot.objects.count()}'))
