# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('players', '0034_add_background_check_clearance_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='manager',
            name='comments',
            field=models.TextField(blank=True, null=True),
        ),
    ]
