from django.core.management.base import BaseCommand
from players.models import Manager


class Command(BaseCommand):
    help = 'Update all manager email addresses to jpowers+<name>@gmail.com format (for testing)'

    def handle(self, *args, **options):
        managers = Manager.objects.all()

        if not managers:
            self.stdout.write(self.style.ERROR('No managers found in database.'))
            return

        updated_count = 0

        for manager in managers:
            # Create email in format: jpowers+firstname.lastname@gmail.com
            # Convert to lowercase and replace spaces with dots
            first_name = manager.first_name.lower().replace(' ', '.')
            last_name = manager.last_name.lower().replace(' ', '.')
            new_email = f'jpowers+{first_name}.{last_name}@gmail.com'

            old_email = manager.email
            manager.email = new_email
            manager.save()

            updated_count += 1
            self.stdout.write(
                self.style.SUCCESS(f'{manager.first_name} {manager.last_name}: {old_email} → {new_email}')
            )

        self.stdout.write(
            self.style.SUCCESS(f'\nCompleted! Updated {updated_count} manager email addresses.')
        )
