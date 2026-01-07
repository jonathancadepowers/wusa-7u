# Generated manually
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('players', '0040_add_sibling_ranking'),
    ]

    operations = [
        migrations.AddField(
            model_name='team',
            name='preseason_practice_slot',
            field=models.TextField(blank=True, null=True),
        ),
    ]
