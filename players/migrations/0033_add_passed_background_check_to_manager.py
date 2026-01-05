# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('players', '0032_rename_rounds_to_rounds_draftable_and_add_rounds_nondraftable'),
    ]

    operations = [
        migrations.AddField(
            model_name='manager',
            name='passed_background_check',
            field=models.BooleanField(default=False),
        ),
    ]
