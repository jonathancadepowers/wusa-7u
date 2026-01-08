from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('players', '0046_add_event_location'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='description',
            field=models.TextField(blank=True, null=True),
        ),
    ]
