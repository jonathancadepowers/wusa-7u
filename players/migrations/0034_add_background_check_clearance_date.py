# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('players', '0033_add_passed_background_check_to_manager'),
    ]

    operations = [
        migrations.AddField(
            model_name='manager',
            name='background_check_clearance_date',
            field=models.DateField(null=True, blank=True),
        ),
    ]
