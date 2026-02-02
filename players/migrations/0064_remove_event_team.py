# Generated manually on 2026-01-25

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('players', '0063_event_home_team_away_team'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='event',
            name='team',
        ),
    ]
