# Generated manually on 2026-01-25

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('players', '0062_alter_roster_inning_1_alter_roster_inning_2_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='home_team',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='home_events', to='players.team'),
        ),
        migrations.AddField(
            model_name='event',
            name='away_team',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='away_events', to='players.team'),
        ),
    ]
