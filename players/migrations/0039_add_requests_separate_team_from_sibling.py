# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('players', '0038_add_siblings_field'),
    ]

    operations = [
        migrations.AddField(
            model_name='player',
            name='requests_separate_team_from_sibling',
            field=models.BooleanField(default=False),
        ),
    ]
