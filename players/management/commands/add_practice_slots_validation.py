from django.core.management.base import BaseCommand
from players.models import ValidationCode, DivisionValidationRegistry


class Command(BaseCommand):
    help = 'Add validation_code_create_practice_slots record and division_validation_registry entry'

    def handle(self, *args, **options):
        # Add ValidationCode record
        validation_code, created = ValidationCode.objects.get_or_create(
            code='validation_code_create_practice_slots',
            defaults={
                'value': False,
                'error_message': 'You must create practice slots before accessing this page.'
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created ValidationCode: {validation_code.code}'))
        else:
            self.stdout.write(self.style.WARNING(f'ValidationCode already exists: {validation_code.code}'))

        # Add DivisionValidationRegistry record
        registry, created = DivisionValidationRegistry.objects.get_or_create(
            page='/practice_slots/',
            defaults={
                'validations_to_run_on_page_load': [],
                'validation_code_triggers': []
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created DivisionValidationRegistry for: {registry.page}'))
        else:
            self.stdout.write(self.style.WARNING(f'DivisionValidationRegistry already exists for: {registry.page}'))

        self.stdout.write(self.style.SUCCESS('\nDone! You can now:'))
        self.stdout.write('1. See validation_code_create_practice_slots in the Validation Codes admin')
        self.stdout.write('2. Edit the /practice_slots/ registry entry to add validation codes')
