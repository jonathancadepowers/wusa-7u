from django.core.management.base import BaseCommand
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from players.models import Manager, Team
import time


class Command(BaseCommand):
    help = 'Send team assignment emails to all managers'

    def add_arguments(self, parser):
        parser.add_argument(
            '--test',
            action='store_true',
            help='Test mode - only send to first manager',
        )
        parser.add_argument(
            '--delay',
            type=int,
            default=1,
            help='Delay in seconds between emails (default: 1)',
        )

    def handle(self, *args, **options):
        test_mode = options['test']
        delay = options['delay']

        # Get all managers with assigned teams
        managers_with_teams = Manager.objects.filter(teams__isnull=False).distinct()

        if not managers_with_teams.exists():
            self.stdout.write(self.style.ERROR('No managers with assigned teams found.'))
            return

        total_managers = managers_with_teams.count()

        if test_mode:
            self.stdout.write(self.style.WARNING('TEST MODE: Only sending to first manager'))
            managers_with_teams = managers_with_teams[:1]

        self.stdout.write(f'Found {total_managers} manager(s) with teams')
        self.stdout.write(f'Sending emails with {delay} second delay between each...\n')

        success_count = 0
        error_count = 0

        for index, manager in enumerate(managers_with_teams, 1):
            # Get the manager's team (assuming one team per manager)
            team = manager.teams.first()

            if not team:
                self.stdout.write(self.style.WARNING(f'Skipping {manager.first_name} {manager.last_name} - no team found'))
                continue

            # Construct the portal URL
            portal_url = f"https://wusa-7u-6b0e52b973f0.herokuapp.com/teams/{team.manager_secret}/"

            # Prepare context for templates
            context = {
                'manager': manager,
                'team': team,
                'portal_url': portal_url,
            }

            # Render email templates
            subject = f'Your WUSA 7U Team Assignment - {team.name}'
            text_content = render_to_string('players/emails/team_assignment.txt', context)
            html_content = render_to_string('players/emails/team_assignment.html', context)

            try:
                # Create email message
                email = EmailMultiAlternatives(
                    subject=subject,
                    body=text_content,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[manager.email],
                    reply_to=[settings.DEFAULT_REPLY_TO_EMAIL],
                )
                email.attach_alternative(html_content, "text/html")

                # Send email
                email.send()

                success_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'[{index}/{len(managers_with_teams)}] ✓ Sent to {manager.first_name} {manager.last_name} ({manager.email}) - Team: {team.name}'
                    )
                )

                # Delay between emails (except for the last one)
                if index < len(managers_with_teams):
                    time.sleep(delay)

            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(
                        f'[{index}/{len(managers_with_teams)}] ✗ Failed to send to {manager.first_name} {manager.last_name}: {str(e)}'
                    )
                )

        # Summary
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS(f'Successfully sent: {success_count}'))
        if error_count > 0:
            self.stdout.write(self.style.ERROR(f'Failed: {error_count}'))
        self.stdout.write('='*50)
