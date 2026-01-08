from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('players', '0047_make_event_description_optional'),
    ]

    operations = [
        migrations.AddField(
            model_name='eventtype',
            name='color',
            field=models.CharField(default='#0d6efd', help_text='Hex color code (e.g., #0d6efd)', max_length=7),
        ),
    ]
