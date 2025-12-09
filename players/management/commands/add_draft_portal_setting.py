from django.core.management.base import BaseCommand
from players.models import GeneralSetting


class Command(BaseCommand):
    help = 'Add open_draft_portal_to_managers setting to general_settings table'

    def handle(self, *args, **options):
        setting, created = GeneralSetting.objects.get_or_create(
            key='open_draft_portal_to_managers',
            defaults={'value': 'false'}
        )

        if created:
            self.stdout.write(self.style.SUCCESS(
                f'Successfully created setting: {setting.key} = {setting.value}'
            ))
        else:
            self.stdout.write(self.style.WARNING(
                f'Setting already exists: {setting.key} = {setting.value}'
            ))
