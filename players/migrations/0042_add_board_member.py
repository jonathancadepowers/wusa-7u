# Generated manually
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('players', '0041_add_preseason_practice_slot'),
    ]

    operations = [
        migrations.AddField(
            model_name='manager',
            name='board_member',
            field=models.BooleanField(default=False),
        ),
    ]
