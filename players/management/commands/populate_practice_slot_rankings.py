import json
import random
from django.core.management.base import BaseCommand
from players.models import Team, PracticeSlot, PracticeSlotRanking


class Command(BaseCommand):
    help = 'Populate practice slot rankings with fake but realistic data for each team'

    def handle(self, *args, **options):
        # Get all teams and practice slots
        teams = Team.objects.all()
        practice_slots = list(PracticeSlot.objects.all())
        
        if not practice_slots:
            self.stdout.write(self.style.ERROR('No practice slots found. Please create practice slots first.'))
            return
        
        if not teams:
            self.stdout.write(self.style.ERROR('No teams found.'))
            return
        
        created_count = 0
        updated_count = 0
        
        for team in teams:
            # Shuffle practice slots to create a random ranking for this team
            team_slot_ranking = practice_slots.copy()
            random.shuffle(team_slot_ranking)
            
            # Create rankings JSON
            rankings_json = json.dumps([
                {"rank": idx + 1, "slot_id": slot.id}
                for idx, slot in enumerate(team_slot_ranking)
            ])
            
            # Create or update practice slot ranking for this team
            ranking, created = PracticeSlotRanking.objects.update_or_create(
                team=team,
                defaults={'rankings': rankings_json}
            )
            
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Created ranking for team: {team.name}'))
            else:
                updated_count += 1
                self.stdout.write(self.style.WARNING(f'Updated ranking for team: {team.name}'))
        
        self.stdout.write(self.style.SUCCESS(
            f'\nCompleted! Created {created_count} new rankings, updated {updated_count} existing rankings.'
        ))
