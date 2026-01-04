# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('players', '0031_team_colors'),
    ]

    operations = [
        migrations.RenameField(
            model_name='draft',
            old_name='rounds',
            new_name='rounds_draftable',
        ),
        migrations.AddField(
            model_name='draft',
            name='rounds_nondraftable',
            field=models.IntegerField(default=0),
        ),
    ]
